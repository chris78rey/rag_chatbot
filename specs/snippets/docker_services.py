"""
Docker Service Locator - Smart Connection String Resolution

Resolves service URLs based on execution context (Docker container vs. local host).
Automatically detects environment and returns appropriate connection strings.

This snippet handles the complexity of having different hostnames depending on
whether code runs inside Docker (container-to-container) or on the host machine.

Features:
- Automatic environment detection (Docker vs. local)
- Service registry with fallback hosts
- Support for multiple protocols (HTTP, Redis, PostgreSQL, etc.)
- Health check helpers
- Configuration integration

Usage:
    locator = ServiceLocator()
    
    # In Docker: "http://qdrant:6333"
    # On local: "http://localhost:6333"
    qdrant_url = locator.get_url("qdrant", "http")
    
    redis_url = locator.get_url("redis", "redis")
"""

import os
from enum import Enum
from typing import Optional, Dict, Tuple
from dataclasses import dataclass


class ExecutionEnvironment(Enum):
    """Where the code is running."""
    DOCKER = "docker"      # Inside a Docker container
    LOCAL = "local"        # On host machine (development)
    PRODUCTION = "prod"    # Remote deployment
    UNKNOWN = "unknown"    # Could not determine


@dataclass
class ServiceDefinition:
    """Definition of a service's connection parameters."""
    docker_host: str      # Hostname inside Docker network
    local_host: str       # Hostname on local machine
    default_port: int     # Default port number
    protocols: Dict[str, str] = None  # Protocol-specific URL patterns
    
    def __post_init__(self):
        if self.protocols is None:
            self.protocols = {
                "http": "http",
                "https": "https",
                "redis": "redis",
                "postgresql": "postgresql",
            }


class ServiceLocator:
    """
    Smart resolver for service connection strings.
    
    Maintains a registry of known services and their hosts, then
    returns the appropriate connection string based on environment.
    
    Example:
        locator = ServiceLocator()
        
        # Automatically detects environment
        qdrant_url = locator.get_url("qdrant")
        redis_url = locator.get_url("redis", "redis")
        
        # Force specific environment
        locator_prod = ServiceLocator(env=ExecutionEnvironment.PRODUCTION)
        prod_url = locator_prod.get_url("qdrant")
    """
    
    # Service registry: service_name -> ServiceDefinition
    SERVICES: Dict[str, ServiceDefinition] = {
        "qdrant": ServiceDefinition(
            docker_host="qdrant",
            local_host="localhost",
            default_port=6333,
        ),
        "redis": ServiceDefinition(
            docker_host="redis",
            local_host="localhost",
            default_port=6379,
        ),
        "api": ServiceDefinition(
            docker_host="api",
            local_host="localhost",
            default_port=8000,
        ),
        "postgres": ServiceDefinition(
            docker_host="postgres",
            local_host="localhost",
            default_port=5432,
        ),
        "mongodb": ServiceDefinition(
            docker_host="mongodb",
            local_host="localhost",
            default_port=27017,
        ),
        "elasticsearch": ServiceDefinition(
            docker_host="elasticsearch",
            local_host="localhost",
            default_port=9200,
        ),
    }
    
    def __init__(
        self,
        env: ExecutionEnvironment | None = None,
        custom_services: Dict[str, ServiceDefinition] | None = None
    ):
        """
        Initialize service locator.
        
        Args:
            env: Execution environment (auto-detected if None)
            custom_services: Additional service definitions
        """
        self.env = env or self._detect_environment()
        
        # Merge custom services
        if custom_services:
            self.SERVICES = {**self.SERVICES, **custom_services}
    
    @staticmethod
    def _detect_environment() -> ExecutionEnvironment:
        """
        Auto-detect execution environment.
        
        Checks for Docker indicators:
        - /.dockerenv file (most reliable)
        - DOCKER_HOST environment variable
        - Running in Docker Compose (DOCKER_COMPOSE env var)
        
        Returns:
            Detected ExecutionEnvironment
        """
        # Check if running in Docker container
        if os.path.exists("/.dockerenv"):
            return ExecutionEnvironment.DOCKER
        
        # Check Docker environment variables
        if os.getenv("DOCKER_HOST"):
            return ExecutionEnvironment.DOCKER
        
        # Check Docker Compose specific vars
        if os.getenv("DOCKER_COMPOSE") or os.getenv("COMPOSE_PROJECT_NAME"):
            return ExecutionEnvironment.DOCKER
        
        # Check for Kubernetes
        if os.path.exists("/var/run/secrets/kubernetes.io"):
            return ExecutionEnvironment.PRODUCTION
        
        # Check for production indicators
        if os.getenv("ENVIRONMENT") == "production":
            return ExecutionEnvironment.PRODUCTION
        
        # Default to local development
        return ExecutionEnvironment.LOCAL
    
    def get_url(
        self,
        service: str,
        protocol: str = "http",
        path: str = "",
        port: Optional[int] = None,
    ) -> str:
        """
        Get connection URL for a service.
        
        Args:
            service: Service name (must be in SERVICES registry)
            protocol: Protocol ('http', 'redis', 'postgresql', etc.)
            path: Optional path suffix (e.g., '/api/v1')
            port: Optional custom port (overrides default)
        
        Returns:
            Full service URL
        
        Raises:
            ValueError: If service not found in registry
        
        Examples:
            locator = ServiceLocator()
            
            # HTTP service
            url = locator.get_url("qdrant", "http")
            # Docker: "http://qdrant:6333"
            # Local: "http://localhost:6333"
            
            # Redis service
            url = locator.get_url("redis", "redis")
            # Docker: "redis://redis:6379"
            # Local: "redis://localhost:6379"
            
            # Custom port
            url = locator.get_url("api", "http", port=9000)
            
            # With path
            url = locator.get_url("qdrant", "http", path="/health")
        """
        if service not in self.SERVICES:
            available = ", ".join(self.SERVICES.keys())
            raise ValueError(
                f"Unknown service: {service}\n"
                f"Available services: {available}"
            )
        
        definition = self.SERVICES[service]
        
        # Choose host based on environment
        if self.env == ExecutionEnvironment.DOCKER:
            host = definition.docker_host
        else:
            host = definition.local_host
        
        # Use provided port or default
        port = port or definition.default_port
        
        # Build URL with protocol-specific format
        if protocol.lower() == "redis":
            # Redis URL format: redis://host:port/db
            url = f"redis://{host}:{port}/0"
        elif protocol.lower() == "postgresql":
            # PostgreSQL URL format: postgresql://host:port/dbname
            url = f"postgresql://{host}:{port}/postgres"
        elif protocol.lower() == "mongodb":
            # MongoDB URL format: mongodb://host:port
            url = f"mongodb://{host}:{port}"
        else:
            # Standard HTTP-like format
            url = f"{protocol}://{host}:{port}"
        
        # Add path if provided
        if path:
            if not path.startswith("/"):
                path = "/" + path
            url += path
        
        return url
    
    def get_many_urls(
        self,
        services: Dict[str, Tuple[str, str]]
    ) -> Dict[str, str]:
        """
        Get URLs for multiple services at once.
        
        Args:
            services: Dict of service_name -> (protocol, path)
        
        Returns:
            Dict of service_name -> url
        
        Example:
            urls = locator.get_many_urls({
                "qdrant": ("http", ""),
                "redis": ("redis", ""),
                "api": ("http", "/api/v1"),
            })
            
            # Result:
            # {
            #     "qdrant": "http://localhost:6333",
            #     "redis": "redis://localhost:6379/0",
            #     "api": "http://localhost:8000/api/v1",
            # }
        """
        result = {}
        
        for service, (protocol, path) in services.items():
            result[service] = self.get_url(service, protocol, path)
        
        return result
    
    @classmethod
    def quick_url(
        cls,
        service: str,
        protocol: str = "http"
    ) -> str:
        """
        Convenience class method for quick URL resolution.
        
        Uses auto-detection, no need to create ServiceLocator instance.
        
        Args:
            service: Service name
            protocol: Protocol
        
        Returns:
            Service URL
        
        Example:
            qdrant_url = ServiceLocator.quick_url("qdrant")
            redis_url = ServiceLocator.quick_url("redis", "redis")
        """
        return cls().get_url(service, protocol)
    
    def health_check(self, service: str, protocol: str = "http") -> bool:
        """
        Check if service is accessible.
        
        Args:
            service: Service name
            protocol: Protocol to use
        
        Returns:
            True if service is reachable, False otherwise
        
        Example:
            if locator.health_check("qdrant"):
                print("✅ Qdrant is running")
            else:
                print("❌ Qdrant is not accessible")
        """
        try:
            url = self.get_url(service, protocol)
            
            if protocol.lower() in ("redis",):
                # Check Redis
                import redis
                r = redis.from_url(url, socket_connect_timeout=2)
                r.ping()
                return True
            
            elif protocol.lower() in ("http", "https"):
                # Check HTTP service
                import requests
                response = requests.get(
                    url + "/health" if service == "qdrant" else url,
                    timeout=2
                )
                return response.status_code < 500
            
            else:
                # Unknown protocol, assume OK
                return True
        
        except Exception:
            return False
    
    def get_all_urls(self) -> Dict[str, str]:
        """
        Get default URLs for all registered services.
        
        Returns:
            Dict of service_name -> default_url
        
        Example:
            all_urls = locator.get_all_urls()
            for service, url in all_urls.items():
                print(f"{service}: {url}")
        """
        result = {}
        
        for service in self.SERVICES.keys():
            result[service] = self.get_url(service)
        
        return result
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ServiceLocator(env={self.env.value})"


class ServiceConfig:
    """
    Configuration object that uses ServiceLocator for dynamic URLs.
    
    Useful for config objects that need to adapt based on environment.
    """
    
    def __init__(self, locator: ServiceLocator | None = None):
        """Initialize with optional custom locator."""
        self.locator = locator or ServiceLocator()
    
    def get_qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return self.locator.get_url("qdrant", "http")
    
    def get_redis_url(self) -> str:
        """Get Redis URL."""
        return self.locator.get_url("redis", "redis")
    
    def get_api_url(self, path: str = "") -> str:
        """Get API URL."""
        return self.locator.get_url("api", "http", path)
    
    def get_postgres_url(self) -> str:
        """Get PostgreSQL URL."""
        return self.locator.get_url("postgres", "postgresql")
    
    def to_dict(self) -> Dict[str, str]:
        """Get all service URLs as dictionary."""
        return {
            "qdrant": self.get_qdrant_url(),
            "redis": self.get_redis_url(),
            "api": self.get_api_url(),
            "postgres": self.get_postgres_url(),
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Docker Service Locator Examples")
    print("=" * 70)
    
    # Example 1: Auto-detect environment
    print("\n1. Auto-detect environment:")
    locator = ServiceLocator()
    print(f"   Detected environment: {locator.env.value}")
    print(f"   Qdrant URL: {locator.get_url('qdrant')}")
    print(f"   Redis URL: {locator.get_url('redis', 'redis')}")
    
    # Example 2: Force specific environment
    print("\n2. Force Docker environment:")
    docker_locator = ServiceLocator(env=ExecutionEnvironment.DOCKER)
    print(f"   Qdrant URL: {docker_locator.get_url('qdrant')}")
    
    print("\n3. Force Local environment:")
    local_locator = ServiceLocator(env=ExecutionEnvironment.LOCAL)
    print(f"   Qdrant URL: {local_locator.get_url('qdrant')}")
    
    # Example 3: Quick method
    print("\n4. Quick method (no instance creation):")
    url = ServiceLocator.quick_url("qdrant")
    print(f"   Quick URL: {url}")
    
    # Example 4: Multiple services
    print("\n5. Get multiple URLs at once:")
    urls = locator.get_many_urls({
        "qdrant": ("http", ""),
        "redis": ("redis", ""),
        "api": ("http", "/api/v1"),
    })
    for service, url in urls.items():
        print(f"   {service}: {url}")
    
    # Example 5: Service config
    print("\n6. Using ServiceConfig:")
    config = ServiceConfig()
    print(f"   Qdrant: {config.get_qdrant_url()}")
    print(f"   Redis: {config.get_redis_url()}")
    print(f"   All: {config.to_dict()}")
    
    # Example 6: Health checks (may fail if services not running)
    print("\n7. Health checks (may fail):")
    print(f"   Qdrant health: {locator.health_check('qdrant')}")
    print(f"   Redis health: {locator.health_check('redis', 'redis')}")
    
    # Example 7: Custom services
    print("\n8. Add custom service:")
    custom_service = ServiceDefinition(
        docker_host="my_service",
        local_host="localhost",
        default_port=5000,
    )
    custom_locator = ServiceLocator(
        custom_services={"my_service": custom_service}
    )
    print(f"   Custom service URL: {custom_locator.get_url('my_service')}")
    
    print("\n" + "=" * 70)