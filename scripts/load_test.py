#!/usr/bin/env python3
"""
Load Test Script para RAF Chatbot - Prueba de Concurrencia

Simula múltiples usuarios concurrentes haciendo queries al chatbot.

Uso:
    python scripts/load_test.py --users 100 --requests 10
    python scripts/load_test.py --users 50 --duration 60
    python scripts/load_test.py --users 100 --requests 5 --url http://localhost:8001

Requisitos:
    pip install aiohttp

Autor: RAF Chatbot Team
Fecha: 2026-01-09
"""

import argparse
import asyncio
import time
import statistics
import random
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

try:
    import aiohttp
except ImportError:
    print("Error: aiohttp no está instalado.")
    print("Instala con: pip install aiohttp")
    exit(1)


# Queries de prueba variadas
SAMPLE_QUERIES = [
    "What is the lean startup methodology?",
    "What is validated learning?",
    "Who is Eric Ries?",
    "What is a pivot?",
    "What is the build measure learn cycle?",
    "How do you measure progress in a startup?",
    "What is innovation accounting?",
    "What is minimum viable product?",
    "How to reduce waste in startups?",
    "What is Toyota production system?",
    "What is continuous deployment?",
    "How to test business hypotheses?",
    "What is actionable metrics?",
    "What is vanity metrics?",
    "How to achieve product market fit?",
]


@dataclass
class RequestResult:
    """Resultado de una request individual."""
    user_id: int
    request_id: int
    success: bool
    status_code: int
    latency_ms: float
    error: Optional[str] = None
    has_answer: bool = False
    has_sources: bool = False


@dataclass
class LoadTestResults:
    """Resultados agregados del test de carga."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_s: float = 0.0
    latencies_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    requests_with_answer: int = 0
    requests_with_sources: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def requests_per_second(self) -> float:
        if self.total_duration_s == 0:
            return 0.0
        return self.total_requests / self.total_duration_s
    
    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return statistics.mean(self.latencies_ms)
    
    @property
    def p50_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return statistics.median(self.latencies_ms)
    
    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def min_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return min(self.latencies_ms)
    
    @property
    def max_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return max(self.latencies_ms)


class LoadTester:
    """Ejecutor de pruebas de carga."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        num_users: int = 10,
        requests_per_user: int = 10,
        duration_seconds: Optional[int] = None,
        rag_id: str = "default",
        timeout_seconds: int = 30,
        verbose: bool = False
    ):
        self.base_url = base_url.rstrip('/')
        self.num_users = num_users
        self.requests_per_user = requests_per_user
        self.duration_seconds = duration_seconds
        self.rag_id = rag_id
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.verbose = verbose
        self.results = LoadTestResults()
        self._stop_event = asyncio.Event()
    
    async def make_request(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        request_id: int
    ) -> RequestResult:
        """Ejecuta una request individual."""
        query = random.choice(SAMPLE_QUERIES)
        url = f"{self.base_url}/query/simple"
        payload = {
            "query": query,
            "rag_id": self.rag_id
        }
        
        start_time = time.perf_counter()
        
        try:
            async with session.post(url, json=payload) as response:
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                result = RequestResult(
                    user_id=user_id,
                    request_id=request_id,
                    success=response.status == 200,
                    status_code=response.status,
                    latency_ms=latency_ms
                )
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        result.has_answer = bool(data.get("answer"))
                        result.has_sources = bool(data.get("sources"))
                    except:
                        pass
                else:
                    result.error = f"HTTP {response.status}"
                
                if self.verbose:
                    status = "✓" if result.success else "✗"
                    print(f"  {status} User {user_id}, Req {request_id}: {latency_ms:.0f}ms")
                
                return result
                
        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return RequestResult(
                user_id=user_id,
                request_id=request_id,
                success=False,
                status_code=0,
                latency_ms=latency_ms,
                error="Timeout"
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return RequestResult(
                user_id=user_id,
                request_id=request_id,
                success=False,
                status_code=0,
                latency_ms=latency_ms,
                error=str(e)
            )
    
    async def simulate_user(
        self,
        session: aiohttp.ClientSession,
        user_id: int
    ) -> List[RequestResult]:
        """Simula un usuario haciendo múltiples requests."""
        results = []
        
        if self.duration_seconds:
            # Modo duración: hacer requests hasta que pase el tiempo
            request_id = 0
            while not self._stop_event.is_set():
                result = await self.make_request(session, user_id, request_id)
                results.append(result)
                request_id += 1
                # Pequeña pausa entre requests (simula usuario real)
                await asyncio.sleep(random.uniform(0.1, 0.5))
        else:
            # Modo requests fijas
            for request_id in range(self.requests_per_user):
                result = await self.make_request(session, user_id, request_id)
                results.append(result)
                # Pequeña pausa entre requests
                await asyncio.sleep(random.uniform(0.05, 0.2))
        
        return results
    
    async def run(self) -> LoadTestResults:
        """Ejecuta el test de carga completo."""
        print(f"\n{'='*60}")
        print(f"🚀 RAF Chatbot - Load Test")
        print(f"{'='*60}")
        print(f"URL: {self.base_url}")
        print(f"Usuarios concurrentes: {self.num_users}")
        if self.duration_seconds:
            print(f"Duración: {self.duration_seconds} segundos")
        else:
            print(f"Requests por usuario: {self.requests_per_user}")
        print(f"RAG ID: {self.rag_id}")
        print(f"{'='*60}\n")
        
        # Verificar que el servidor está disponible
        print("Verificando conexión al servidor...")
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status != 200:
                        print(f"✗ Servidor no disponible (HTTP {response.status})")
                        return self.results
                    print(f"✓ Servidor disponible\n")
        except Exception as e:
            print(f"✗ Error conectando al servidor: {e}")
            return self.results
        
        print(f"Iniciando test con {self.num_users} usuarios...\n")
        
        start_time = time.perf_counter()
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            if self.duration_seconds:
                # Modo duración
                async def stop_after_duration():
                    await asyncio.sleep(self.duration_seconds)
                    self._stop_event.set()
                
                asyncio.create_task(stop_after_duration())
            
            # Crear tareas para todos los usuarios
            tasks = [
                self.simulate_user(session, user_id)
                for user_id in range(self.num_users)
            ]
            
            # Ejecutar todas las tareas concurrentemente
            all_results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        
        # Agregar resultados
        self.results.total_duration_s = end_time - start_time
        
        for user_results in all_results:
            for result in user_results:
                self.results.total_requests += 1
                self.results.latencies_ms.append(result.latency_ms)
                
                if result.success:
                    self.results.successful_requests += 1
                    if result.has_answer:
                        self.results.requests_with_answer += 1
                    if result.has_sources:
                        self.results.requests_with_sources += 1
                else:
                    self.results.failed_requests += 1
                    if result.error:
                        self.results.errors.append(result.error)
        
        return self.results
    
    def print_results(self):
        """Imprime los resultados del test."""
        r = self.results
        
        print(f"\n{'='*60}")
        print(f"📊 RESULTADOS DEL TEST DE CARGA")
        print(f"{'='*60}\n")
        
        # Resumen general
        print("📈 Resumen General:")
        print(f"   Total requests:     {r.total_requests}")
        print(f"   Exitosas:           {r.successful_requests} ({r.success_rate:.1f}%)")
        print(f"   Fallidas:           {r.failed_requests}")
        print(f"   Duración total:     {r.total_duration_s:.2f}s")
        print(f"   Throughput:         {r.requests_per_second:.2f} req/s")
        
        # Latencias
        print(f"\n⏱️  Latencias:")
        print(f"   Promedio:           {r.avg_latency_ms:.2f} ms")
        print(f"   Mínima:             {r.min_latency_ms:.2f} ms")
        print(f"   Máxima:             {r.max_latency_ms:.2f} ms")
        print(f"   P50 (mediana):      {r.p50_latency_ms:.2f} ms")
        print(f"   P95:                {r.p95_latency_ms:.2f} ms")
        print(f"   P99:                {r.p99_latency_ms:.2f} ms")
        
        # Calidad de respuestas
        if r.successful_requests > 0:
            print(f"\n✅ Calidad de Respuestas:")
            print(f"   Con respuesta:      {r.requests_with_answer} ({r.requests_with_answer/r.successful_requests*100:.1f}%)")
            print(f"   Con fuentes:        {r.requests_with_sources} ({r.requests_with_sources/r.successful_requests*100:.1f}%)")
        
        # Errores
        if r.errors:
            print(f"\n❌ Errores ({len(r.errors)}):")
            error_counts = {}
            for error in r.errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            for error, count in sorted(error_counts.items(), key=lambda x: -x[1])[:5]:
                print(f"   - {error}: {count}x")
        
        # Evaluación
        print(f"\n{'='*60}")
        print("📋 EVALUACIÓN:")
        
        if r.success_rate >= 99:
            print("   ✅ Tasa de éxito: EXCELENTE")
        elif r.success_rate >= 95:
            print("   ✓ Tasa de éxito: BUENA")
        elif r.success_rate >= 90:
            print("   ⚠️ Tasa de éxito: ACEPTABLE")
        else:
            print("   ❌ Tasa de éxito: NECESITA MEJORAS")
        
        if r.p95_latency_ms <= 500:
            print("   ✅ Latencia P95: EXCELENTE (<500ms)")
        elif r.p95_latency_ms <= 1000:
            print("   ✓ Latencia P95: BUENA (<1s)")
        elif r.p95_latency_ms <= 3000:
            print("   ⚠️ Latencia P95: ACEPTABLE (<3s)")
        else:
            print("   ❌ Latencia P95: LENTA (>3s)")
        
        if r.requests_per_second >= 50:
            print("   ✅ Throughput: ALTO (>50 req/s)")
        elif r.requests_per_second >= 20:
            print("   ✓ Throughput: MEDIO (>20 req/s)")
        elif r.requests_per_second >= 10:
            print("   ⚠️ Throughput: BAJO (>10 req/s)")
        else:
            print("   ❌ Throughput: MUY BAJO (<10 req/s)")
        
        print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Load Test para RAF Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    # 100 usuarios, 10 requests cada uno
    python scripts/load_test.py --users 100 --requests 10
    
    # 50 usuarios durante 60 segundos
    python scripts/load_test.py --users 50 --duration 60
    
    # Test rápido
    python scripts/load_test.py --users 10 --requests 5
    
    # Con verbose
    python scripts/load_test.py --users 5 --requests 3 --verbose
        """
    )
    
    parser.add_argument(
        "--users", "-u",
        type=int,
        default=10,
        help="Número de usuarios concurrentes (default: 10)"
    )
    parser.add_argument(
        "--requests", "-r",
        type=int,
        default=10,
        help="Requests por usuario (default: 10)"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=None,
        help="Duración en segundos (ignora --requests si se especifica)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8001",
        help="URL base del servidor (default: http://localhost:8001)"
    )
    parser.add_argument(
        "--rag-id",
        type=str,
        default="default",
        help="RAG ID para las queries (default: 'default')"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout por request en segundos (default: 30)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar cada request individual"
    )
    
    args = parser.parse_args()
    
    tester = LoadTester(
        base_url=args.url,
        num_users=args.users,
        requests_per_user=args.requests,
        duration_seconds=args.duration,
        rag_id=args.rag_id,
        timeout_seconds=args.timeout,
        verbose=args.verbose
    )
    
    await tester.run()
    tester.print_results()


if __name__ == "__main__":
    asyncio.run(main())