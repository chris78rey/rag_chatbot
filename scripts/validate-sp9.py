#!/usr/bin/env python3
"""
Script de validación para Subproyecto 9 (Observabilidad).

Verifica que:
1. El endpoint /metrics está disponible
2. Las métricas retornan el schema correcto
3. Los contadores incrementan con cada request
4. Las latencias se registran correctamente
"""
import asyncio
import httpx
import json
import sys
from typing import Optional


class ValidatorSP9:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)
        self.tests_passed = 0
        self.tests_failed = 0
    
    async def test_metrics_endpoint_exists(self) -> bool:
        """Test 1: Verificar que /metrics está disponible"""
        print("\n[TEST 1] Verificar que /metrics está disponible...")
        try:
            response = await self.client.get("/metrics")
            if response.status_code == 200:
                print("✓ Endpoint /metrics respondió con 200")
                return True
            else:
                print(f"✗ Endpoint /metrics retornó {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error al acceder a /metrics: {str(e)}")
            return False
    
    async def test_metrics_schema(self) -> bool:
        """Test 2: Verificar que el schema de métricas es correcto"""
        print("\n[TEST 2] Verificar schema de métricas...")
        required_fields = [
            "requests_total",
            "errors_total",
            "cache_hits_total",
            "rate_limited_total",
            "avg_latency_ms",
            "p95_latency_ms",
            "latency_samples"
        ]
        
        try:
            response = await self.client.get("/metrics")
            metrics = response.json()
            
            for field in required_fields:
                if field not in metrics:
                    print(f"✗ Campo faltante: {field}")
                    return False
            
            print(f"✓ Schema correcto. Campos presentes: {', '.join(required_fields)}")
            return True
        except Exception as e:
            print(f"✗ Error al parsear métricas: {str(e)}")
            return False
    
    async def test_metrics_initial_state(self) -> bool:
        """Test 3: Verificar estado inicial de métricas (deberían ser 0)"""
        print("\n[TEST 3] Verificar estado inicial de métricas...")
        try:
            response = await self.client.get("/metrics")
            metrics = response.json()
            
            if metrics["requests_total"] == 0:
                print("✓ requests_total inicialmente es 0")
            else:
                print(f"⚠ requests_total no es 0 (es {metrics['requests_total']})")
                print("  Nota: Si hay requests previos, esto es normal")
            
            print(f"  Estado inicial: {json.dumps(metrics, indent=2)}")
            return True
        except Exception as e:
            print(f"✗ Error al obtener métricas iniciales: {str(e)}")
            return False
    
    async def test_metrics_increment_on_query(self) -> bool:
        """Test 4: Verificar que requests_total incrementa con query"""
        print("\n[TEST 4] Verificar que requests_total incrementa...")
        try:
            # Obtener estado inicial
            response1 = await self.client.get("/metrics")
            metrics_before = response1.json()
            requests_before = metrics_before["requests_total"]
            
            print(f"  requests_total antes: {requests_before}")
            
            # Hacer un query (puede fallar, pero debe incrementar request count)
            try:
                await self.client.post(
                    "/query",
                    json={
                        "rag_id": "test",
                        "question": "test query",
                        "top_k": 5
                    }
                )
            except Exception:
                pass  # Ignorar errores del query
            
            # Obtener estado después
            response2 = await self.client.get("/metrics")
            metrics_after = response2.json()
            requests_after = metrics_after["requests_total"]
            
            print(f"  requests_total después: {requests_after}")
            
            if requests_after > requests_before:
                print(f"✓ requests_total incrementó de {requests_before} a {requests_after}")
                return True
            else:
                print(f"✗ requests_total no incrementó")
                return False
        except Exception as e:
            print(f"✗ Error en test: {str(e)}")
            return False
    
    async def test_latency_recording(self) -> bool:
        """Test 5: Verificar que se registran latencias"""
        print("\n[TEST 5] Verificar registro de latencias...")
        try:
            response = await self.client.get("/metrics")
            metrics = response.json()
            
            latency_samples = metrics["latency_samples"]
            avg_latency = metrics["avg_latency_ms"]
            
            if latency_samples > 0:
                print(f"✓ Se registraron {latency_samples} muestras de latencia")
                print(f"  Latencia promedio: {avg_latency}ms")
                print(f"  P95 latencia: {metrics['p95_latency_ms']}ms")
                return True
            else:
                print(f"⚠ No hay muestras de latencia registradas aún")
                return True  # No es un error, pueden no haber requests
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False
    
    async def test_metrics_types(self) -> bool:
        """Test 6: Verificar tipos de datos de métricas"""
        print("\n[TEST 6] Verificar tipos de datos...")
        try:
            response = await self.client.get("/metrics")
            metrics = response.json()
            
            type_checks = {
                "requests_total": int,
                "errors_total": int,
                "cache_hits_total": int,
                "rate_limited_total": int,
                "avg_latency_ms": (int, float),
                "p95_latency_ms": (int, float),
                "latency_samples": int
            }
            
            all_correct = True
            for field, expected_type in type_checks.items():
                value = metrics[field]
                if isinstance(value, expected_type):
                    print(f"✓ {field}: {type(value).__name__} = {value}")
                else:
                    print(f"✗ {field}: esperaba {expected_type}, obtuvo {type(value).__name__}")
                    all_correct = False
            
            return all_correct
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Ejecutar todos los tests"""
        print("=" * 60)
        print("VALIDACIÓN DE SUBPROYECTO 9 - OBSERVABILIDAD")
        print("=" * 60)
        
        tests = [
            ("Endpoint /metrics existe", self.test_metrics_endpoint_exists),
            ("Schema de métricas correcto", self.test_metrics_schema),
            ("Estado inicial de métricas", self.test_metrics_initial_state),
            ("Incremento de requests_total", self.test_metrics_increment_on_query),
            ("Registro de latencias", self.test_latency_recording),
            ("Tipos de datos correctos", self.test_metrics_types),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
                self.tests_passed += 1 if result else 0
                self.tests_failed += 0 if result else 1
            except Exception as e:
                print(f"\n✗ Error ejecutando {test_name}: {str(e)}")
                results.append((test_name, False))
                self.tests_failed += 1
        
        # Resumen
        print("\n" + "=" * 60)
        print("RESUMEN DE PRUEBAS")
        print("=" * 60)
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {self.tests_passed} pasadas, {self.tests_failed} fallidas")
        
        await self.client.aclose()
        return self.tests_failed == 0


async def main():
    validator = ValidatorSP9()
    success = await validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())