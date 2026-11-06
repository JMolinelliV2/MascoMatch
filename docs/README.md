# Documentación de MascoMatch

Revisada contra el repositorio el **5 de noviembre de 2026**. Las guías describen lo implementado; la disponibilidad de un servicio externo se comprueba en cada instalación.

## Elegir la guía

| Necesidad | Documento |
| --- | --- |
| Entender todos los recorridos y sus permisos | [Flujos del sistema](FLUJOS_DEL_SISTEMA.md) |
| Entender las tecnologías, los datos y la arquitectura | [Arquitectura](architecture.md) |
| Mantener componentes, estilos, formularios y mapas | [Frontend](frontend.md) |
| Administrar usuarios, publicaciones, denuncias y coincidencias | [Administración](admin-operations.md) |
| Interpretar visitas, conversiones, respuestas e impacto | [Contrato de métricas](analytics.md) |
| Instalar, operar y evaluar los modelos locales | [IA local](ai-production.md) |
| Consultar procedencia, revisiones y licencias de modelos | [Modelos de terceros](third-party-models.md) |
| Instalar por primera vez en un VPS | [Puesta en producción paso a paso](puesta-en-produccion-paso-a-paso.md) |
| Actualizar, diagnosticar, enviar correo y respaldar | [Operación del servidor](production.md) |
| Configurar B2 y recuperar información en otro servidor | [Respaldos externos](backblaze-backup.md) |
| Configurar y comprobar los aportes puntuales | [Mercado Pago](mercado-pago-configuracion.md) |
| Consultar mediciones técnicas antiguas con su contexto | [Benchmarks históricos](benchmarks/README.md) |

Para levantar el entorno local y ejecutar las comprobaciones habituales, empezar por el [README del repositorio](../README.md).

## Cómo mantener esta carpeta

- El comportamiento de las personas usuarias se explica en **Flujos del sistema**. Las guías técnicas enlazan ese documento y describen sus propios contratos y comandos.
- El procedimiento inicial de producción y la operación diaria tienen guías separadas. B2 y Mercado Pago conservan sus procedimientos específicos.
- Las estructuras y restricciones exactas se consultan en el código enlazado, los archivos de configuración y OpenAPI. No se mantiene una segunda copia exhaustiva de cada endpoint o catálogo.
- Los informes de entregas, capturas, resultados puntuales de pruebas y listas de archivos modificados pertenecen al historial de Git. No se acumula una guía por cada cambio visual o funcional.
- Los JSON de benchmarks se conservan como evidencia fechada, sin alterar sus resultados. No representan el estado actual de las pruebas, el tráfico del VPS ni la precisión del sistema.
- No se guardan contraseñas, claves, contactos privados, volcados de base ni respaldos en esta carpeta.
