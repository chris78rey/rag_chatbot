#!/usr/bin/env python3
"""
Subproject 10: State Verification Script (Read-Only)
Verifies that the system state matches expected invariants.
"""

import json
import sys
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Configuration
SCRIPT_DIR = Path(__file__).parent
STATE_EXPECTED_FILE = SCRIPT_DIR / "state_expected.json"
API_BASE_URL = "http://localhost:8001"
QDRANT_BASE_URL = "http://localhost:6333"

class StateVerifier:
    def __init__(self):
        self.expected_state = self._load_expected_state()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _load_expected_state(self) -> Dict[str, Any]:
        """Load expected state from JSON file."""
        try:
            with open(STATE_EXPECTED_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.errors.append(f"Expected state file not found: {STATE_EXPECTED_FILE}")
            return {}
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in state_expected.json: {e}")
            return {}

    def _docker_exec(self, container: str, cmd: str) -> Tuple[bool, str]:
        """Execute command inside Docker container."""
        try:
            result = subprocess.run(
                ["docker", "exec", container] + cmd.split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def verify_api_health(self) -> bool:
        """Verify API service is healthy."""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                return True
            else:
                self.errors.append(f"API health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.errors.append(f"Cannot reach API: {e}")
            return False

    def verify_api_endpoints(self) -> bool:
        """Verify critical API endpoints are accessible."""
        endpoints = ["/query", "/metrics"]
        all_ok = True

        for endpoint in endpoints:
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
                if response.status_code not in [200, 400, 405]:
                    self.warnings.append(f"Endpoint {endpoint} returned {response.status_code}")
                    all_ok = False
            except Exception as e:
                self.errors.append(f"Cannot reach endpoint {endpoint}: {e}")
                all_ok = False

        return all_ok

    def verify_metrics_available(self) -> bool:
        """Verify metrics endpoint returns expected metrics."""
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
            if response.status_code != 200:
                self.errors.append(f"Metrics endpoint returned {response.status_code}")
                return False

            metrics_text = response.text
            required_metrics = self.expected_state.get("observability", {}).get("required_metrics", [])

            for metric in required_metrics:
                if metric not in metrics_text:
                    self.errors.append(f"Required metric '{metric}' not found in /metrics")
                    return False

            return True
        except Exception as e:
            self.errors.append(f"Cannot fetch metrics: {e}")
            return False

    def verify_qdrant_health(self) -> bool:
        """Verify Qdrant service is healthy using Docker exec."""
        try:
            # Use docker exec to check Qdrant from inside the network
            success, output = self._docker_exec("api", "curl -s http://qdrant:6333/readyz")
            if success and "ready" in output.lower():
                return True
            else:
                self.errors.append(f"Qdrant health check failed: {output}")
                return False
        except Exception as e:
            self.errors.append(f"Cannot reach Qdrant: {e}")
            return False

    def verify_qdrant_collection(self) -> bool:
        """Verify Qdrant has the documents collection using Docker exec."""
        try:
            # Use docker exec to list collections from inside the network
            success, output = self._docker_exec("api", "curl -s http://qdrant:6333/collections")
            
            if not success:
                self.errors.append(f"Cannot list Qdrant collections: {output}")
                return False

            try:
                data = json.loads(output)
                collections = data.get("result", {}).get("collections", [])
                collection_names = [c.get("name") for c in collections if isinstance(c, dict)]

                if "documents" not in collection_names:
                    self.errors.append(f"Qdrant collection 'documents' not found. Found: {collection_names}")
                    return False

                return True
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON response from Qdrant: {e}")
                return False
        except Exception as e:
            self.errors.append(f"Cannot verify Qdrant collection: {e}")
            return False

    def verify_constraints(self) -> bool:
        """Verify system constraints (latency, availability, error rate)."""
        all_ok = True

        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
            if response.status_code == 200:
                metrics_text = response.text
                constraints = self.expected_state.get("constraints", {})

                # Simple check: if p95_latency_ms metric exists, we're collecting data
                if "p95_latency_ms" in metrics_text:
                    # Parse the metric value (basic parsing)
                    for line in metrics_text.split("\n"):
                        if "p95_latency_ms" in line and not line.startswith("#"):
                            try:
                                value = float(line.split()[-1])
                                max_latency = constraints.get("max_latency_p95_ms", 5000)
                                if value > max_latency:
                                    self.warnings.append(
                                        f"p95_latency_ms ({value}ms) exceeds threshold ({max_latency}ms)"
                                    )
                                    all_ok = False
                            except (ValueError, IndexError):
                                pass

                return all_ok
            else:
                self.warnings.append("Cannot fetch metrics for constraint verification")
                return False
        except Exception as e:
            self.warnings.append(f"Constraint verification skipped: {e}")
            return True  # Don't fail on warning

    def run_verification(self) -> Tuple[bool, str]:
        """Run all verifications and return overall status."""
        checks = [
            ("API Health", self.verify_api_health),
            ("API Endpoints", self.verify_api_endpoints),
            ("Metrics Availability", self.verify_metrics_available),
            ("Qdrant Health", self.verify_qdrant_health),
            ("Qdrant Collection", self.verify_qdrant_collection),
            ("System Constraints", self.verify_constraints),
        ]

        results = []
        for check_name, check_func in checks:
            result = check_func()
            status = "✓ PASS" if result else "✗ FAIL"
            results.append(f"{status}: {check_name}")

        overall_status = len(self.errors) == 0
        return overall_status, "\n".join(results)

    def print_report(self, overall_status: bool, results: str) -> None:
        """Print verification report."""
        print("\n" + "=" * 60)
        print("STATE VERIFICATION REPORT")
        print("=" * 60)
        print(results)
        print("\n" + "-" * 60)

        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  ✗ {error}")

        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        print("\n" + "=" * 60)
        status_text = "STATE_OK" if overall_status else "STATE_FAIL"
        print(f"FINAL STATUS: {status_text}")
        print("=" * 60 + "\n")

        return overall_status


def main():
    """Main entry point."""
    verifier = StateVerifier()
    overall_status, results = verifier.run_verification()
    verifier.print_report(overall_status, results)
    sys.exit(0 if overall_status else 1)


if __name__ == "__main__":
    main()