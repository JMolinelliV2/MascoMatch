# Mediciones de la mejora de IA

Medidas el 15–16 de octubre de 2026 en Docker Desktop, Linux x86_64, CPU local. La VM tenía 20 CPU lógicas y 15,46 GiB disponibles; Gemma usó tres threads y los modelos visuales dos. No son mediciones del futuro VPS ni una estimación de precisión sobre casos reales.

## Archivos

| Archivo | Contenido |
| --- | --- |
| `gemma-benchmark.json` | Prompt anterior; tres configuraciones, tres textos y cuatro entradas visuales por configuración; cold/warm y dos solicitudes simultáneas. |
| `gemma-optimized.json` | Experimento con TEXT v2 y VISION v2, dos repeticiones. **TEXT v2 fue rechazado**: omitió un color secundario y produjo texto libre en inglés. Se conserva como evidencia del experimento, no como resultado final de texto. |
| `gemma-text-final.json` | TEXT v3 final: seis extracciones, 28 comprobaciones de atributos conocidos y cero discrepancias. |
| `visual-resources.json` | Carga e inferencia CPU por componente en procesos separados, RSS y tiempo de CPU. Los picos no deben sumarse como si fueran simultáneos. |
| `ai-smoke-production.json` | PostgreSQL/PostGIS/pgvector + Redis + SeaweedFS + worker visual + Gemma reales; ocho trabajos visuales y texto/imagen, con datos temporales y SMTP desactivado. |

VISION v2 se mantiene: ocho extracciones válidas y ocho comprobaciones de especie correctas. Los restantes atributos visuales no tienen ground truth completo. No se calculó una tasa general de alucinación a partir de esas ocho comprobaciones.

## Comparación final

| Medida | Anterior | Final |
| --- | ---: | ---: |
| Contexto / salida máxima | 8192 / 4096 | 4096 / 768 |
| Lado máximo VLM | 1024 | 1024 |
| Keep-alive | 5m | 15m |
| Texto p50 / p95 | 38,87 / 48,36 s | 35,13 / 40,98 s |
| Visión p50 / p95 | 80,08 / 82,79 s | 68,45 / 75,50 s |
| Texto JSON válido | 3/3 | 6/6 |
| Visión JSON válido | 4/4 | 8/8 |
| Errores de especie en imagen | 1/4 | 0/8 |
| Dos solicitudes de texto simultáneas, tiempo total | 75,80 s | 71,96 s |

La alternativa de 768 px no mejoró consistentemente la visión: p95 87,90 s. Se eligió 1024 px para conservar detalles. El sistema anterior ya limitaba algunas fotos a 1024 px; no se atribuye esta mejora a reducir fotografías de teléfono sin límite.

Las muestras son pequeñas, con repeticiones y prompts diferentes. Los percentiles describen estas ejecuciones; no constituyen una prueba estadística de mejora universal. En ambas configuraciones Ollama procesó una generación a la vez. Dos peticiones concurrentes no duplicaron el rendimiento, por lo que se mantiene `OLLAMA_NUM_PARALLEL=1`.

Los benchmarks de cold-start descargan deliberadamente el modelo de RAM. Ejecutarlos en una ventana de mantenimiento o un entorno separado. Los comandos reproducibles están en [operación de IA](../ai-production.md).
