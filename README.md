# 🚀 Pipeline Automatizado de Consolidación de Alarmas (Orange)

> **Autor:** Yago Menéndez ([@ymvs84](https://github.com/ymvs84))
> **Rol:** Cloud Operations & Backend Engineer | JCDecaux

Sistema de ingeniería de datos diseñado para la ingesta, procesamiento, consolidación y publicación automatizada de alarmas de dispositivos de red (Orange). El pipeline opera de forma totalmente desatendida, eliminando la intervención manual y garantizando la trazabilidad de los datos.

---

## 🛠️ Arquitectura del Sistema (Pipeline End-to-End)

El flujo de ejecución consta de 5 fases secuenciales:

1. **Ingesta Inteligente de Correos (`descargar_alarmas.py`):** Conexión automatizada a Outlook mediante automatización web (Playwright) con un algoritmo de parada inteligente para optimizar tiempos de descarga.
2. **Respaldo de Históricos (`subir_historicos.py`):** Copia de seguridad automática de todos los ficheros `.csv` crudos en el repositorio centralizado de SharePoint.
3. **Sincronización del Maestro (`descargar_maestro.py`):** Descarga dinámica de la última versión oficial del inventario de dispositivos desde SharePoint.
4. **Procesamiento de Datos (`main.py`):** Motor basado en `Pandas` para la limpieza, unificación y cruce de datos contra el Maestro, aplicando diccionarios de excepciones técnicas (Taller, CCD, Jaula de Pruebas) y logrando un **100% de éxito en la asignación de dispositivos**.
5. **Publicación Ejecutiva (`subir_sharepoint.py`):** Subida y sincronización automática del informe consolidado (`Control_Alarmas_Orange.xlsx`) de vuelta a SharePoint.

---

## 📂 Estructura del Proyecto

```text
ProcesadorAlarmas/
│
├── data/
│   ├── inputs/          # Ficheros CSV de alarmas descargados
│   ├── maestro/         # Fichero maestro de inventario actualizado
│   └── outputs/         # Informe final consolidado (Excel)
│
├── logs/                # Registros de ejecución (logs) y evidencias de error
├── src/
│   ├── descargar_alarmas.py
│   ├── descargar_maestro.py
│   ├── subir_historicos.py
│   ├── subir_sharepoint.py
│   └── main.py          # Director de orquesta (Pipeline completo)
│
├── .venv/               # Entorno virtual de Python
├── auth.json            # Credenciales de sesión securizadas para automatización web
└── README.md

```

## ⚙️ Requisitos y Dependencias

* **Python 3.10+**
* **Pandas** (Procesamiento y análisis de datos)
* **Openpyxl** (Manipulación de ficheros Excel)
* **Playwright** (Automatización web para la integración con SharePoint y Outlook)

---

## 🔄 Automatización (Desatendido 24/7)

El sistema está configurado mediante tareas programadas del sistema operativo (`cron`) para ejecutarse de forma autónoma en segundo plano (habitualmente en horario nocturno), asegurando que los datos estén listos al inicio de cada jornada laboral sin requerir intervención humana.
