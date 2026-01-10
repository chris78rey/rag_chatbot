# Lecciones Aprendidas - Template para Nuevas Lecciones

**Usar este template para documentar nuevas lecciones aprendidas.**

---

## 🎯 Problema Identificado

**[Título corto del problema]**

Descripción clara del problema observado:
- ¿Qué no funcionaba?
- ¿En qué subproyecto?
- ¿Cuál fue el síntoma inicial?

```
[Ejemplo de error o comportamiento incorrecto]
```

---

## 🔍 Causa Raíz

**Análisis sistemático de por qué ocurrió el problema**

### 1. [Primer Factor Contributivo]

Explicación detallada de cómo este factor contribuyó.

```python
# ❌ INCORRECTO - Ejemplo de código problemático
```

### 2. [Segundo Factor Contributivo]

Explicación adicional.

### 3. [Diagrama o Flujo del Problema]

```
[Visualización del flujo que muestra el problema]
```

---

## ✅ Solución Implementada

### Paso 1: [Primera Solución Parcial]

```python
# ✓ CÓDIGO CORREGIDO
[Mostrar cambio específico]
```

### Paso 2: [Segunda Parte de la Solución]

Explicación de por qué esta parte es necesaria.

### Paso 3: [Verificación]

```bash
# Comando para validar que funciona
```

---

## 🛡️ Principios Preventivos Clave

### P1: [Principio General sobre el Tema]

Explicación del principio.

```python
# ❌ MAL - Anti-pattern
# ✓ BIEN - Patrón correcto
```

### P2: [Segundo Principio Relacionado]

Contexto adicional donde aplica.

### P3: [Variaciones o Casos Especiales]

Cuándo aplican los principios y cuándo no.

---

## 🚨 Señales de Activación (Trigger Detection)

### Señal 1: [Síntoma Observable #1]

```
[Ejemplo de log, error, o comportamiento]
```

Esto significa: [Explicación de qué está pasando]

### Señal 2: [Síntoma Observable #2]

Cómo identificarlo y qué hacer.

### Señal 3: [Síntoma Observable #3]

Patrón que indica este problema.

---

## 💻 Código Reutilizable

### Componente: [Nombre Descriptivo]

```python
"""
[Descripción del componente]
Reutilizable para [casos de uso]
"""

[Código completo y funcional]

# Uso:
[Ejemplo de uso]
```

### Script: `scripts/[nombre-validacion].py`

```python
#!/usr/bin/env python3
"""
[Descripción de qué valida este script]
Uso: python scripts/[nombre].py
"""

[Código completo del script]
```

### Script: `scripts/[nombre-diagnostico].sh`

```bash
#!/bin/bash

# [Descripción del script bash]
# Uso: bash scripts/[nombre].sh

[Script completo]
```

---

## 📋 Checklist de Implementación

### Antes de [hacer la tarea/agregar feature]

- [ ] [Tarea preparatoria 1]
- [ ] [Tarea preparatoria 2]
- [ ] [Requisito 3]
- [ ] [Requisito 4]

### En revisión de código

```python
# Preguntas a hacer:
1. ¿[Pregunta de validación 1]? → [Respuesta esperada]
2. ¿[Pregunta de validación 2]? → [Respuesta esperada]
3. ¿[Pregunta de validación 3]? → [Respuesta esperada]
```

### En operación / mantenimiento

```bash
# Ciclo típico
[Comando 1]
[Comando 2]
[Comando 3]
[Verificación]
```

---

## 🔗 Anti-Patterns a Evitar

### ❌ Anti-Pattern 1: [Nombre del Anti-pattern]

```python
# ❌ MAL - Esto no funciona
[Código incorrecto]
```

Problema: [Por qué es malo]

### ❌ Anti-Pattern 2: [Otro Anti-pattern]

```python
# ❌ MAL
[Código problemático]
```

### ✓ Solución

```python
# ✓ BIEN
[Código correcto]
```

---

## 💡 Best Practices

### BP1: [Mejor Práctica #1]

```python
# ✓ PATRÓN RECOMENDADO
[Código de ejemplo]
```

Ventajas:
- [Ventaja 1]
- [Ventaja 2]

### BP2: [Mejor Práctica #2]

Explicación y contexto.

---

## 📈 Impacto de la Solución

| Métrica | Antes | Después |
|---------|-------|---------|
| [Métrica 1] | [Valor antes] | [Valor después] |
| [Métrica 2] | [Valor antes] | [Valor después] |
| [Métrica 3] | [Valor antes] | [Valor después] |

---

## 🧪 Tests Relacionados

### Test File: `tests/test_[topic].py`

```python
#!/usr/bin/env python3
"""
Tests para validar [topic]
Ejecutar: pytest tests/test_[topic].py -v
"""

class TestMyFeature:
    """Suite de tests."""
    
    def test_case_1(self):
        """Descripción de qué valida este test."""
        # Arrange
        # Act
        # Assert
    
    def test_case_2(self):
        """Otro test."""
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 🔗 Referencias a Otros Documentos

- Ver: `LESSONS-LEARNED-##-TOPIC.md` (relación con otra lección)
- Ver: `docs/[related-doc].md` (documentación relacionada)
- Código: `[filepath]` (implementación referenciada)

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | YYYY-MM-DD | Documento inicial |
| 1.1 | YYYY-MM-DD | [Cambio] |

---

## ✨ Key Takeaway

> **"[Frase memorable que resume la lección aprendida. Máximo 2 líneas.]"**

```python
# Patrón ganador
[Código de ejemplo del patrón recomendado]
```

---

## 📚 Recursos Adicionales

### Documentación Oficial
- [Link a documentación oficial]
- [Otra referencia útil]

### Ejemplos en el Proyecto
- `[Archivo de ejemplo 1]` - [Descripción]
- `[Archivo de ejemplo 2]` - [Descripción]

### Referencias Externas
- [URL externa 1] - [Descripción]
- [URL externa 2] - [Descripción]

---

## ❓ FAQ

### P: ¿Cuándo debo aplicar esta lección?

R: [Respuesta clara]

### P: ¿Y si tengo casos especiales?

R: [Explicación de excepciones]

### P: ¿Cómo validar que funcionó?

R: [Pasos de validación]

---

## 🎓 Lecciones Relacionadas

- Lección XX: [Tema relacionado]
- Lección YY: [Otro tema relacionado]

---
