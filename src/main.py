"""
=============================================================================
 Proyecto: Pipeline de Automatización de Alarmas Orange
 Autor: Yago Menéndez (ymvs84)
 Descripción: Orquestador end-to-end de ingesta, respaldo y consolidación.
=============================================================================
"""

import os
import glob
import pandas as pd
import re
import subprocess

def limpiar_numero_estricto(cadena):
    if pd.isna(cadena):
        return ""
    return re.sub(r'\D', '', str(cadena))

def procesar_datos_alarmas():
    # Configuración de rutas
    RUTA_SRC = os.path.dirname(os.path.abspath(__file__))
    RUTA_BASE = os.path.dirname(RUTA_SRC)

    DIR_DATA = os.path.join(RUTA_BASE, "data")
    DIR_INPUTS = os.path.join(DIR_DATA, "inputs")
    DIR_MAESTRO = os.path.join(DIR_DATA, "maestro")
    DIR_OUTPUTS = os.path.join(DIR_DATA, "outputs")

    PATH_MAESTRO_LOCAL = os.path.join(DIR_MAESTRO, "Listado Mobiliario Digital NT_2025.xlsx")

    EXCEPCIONES_MANUALES = {
        "8934011032604070575": "Taller",
        "8934011032604070591": "Taller",
        "8934011032604070583": "Taller",
        "8934011032604070526": "Taller",
        "8034011032604070567": "Taller",
        "8934011032604070609": "Taller",
        "8934013132428191884": "Taller",
        "8934013132428101933": "CCD",
        "8934076179016310768": "CCD",
        "8934013132428192874": "CCD",
        "8934011032604070534": "Jaula de Pruebas"
    }

    excepciones_limpias = {limpiar_numero_estricto(k): v for k, v in EXCEPCIONES_MANUALES.items()}

    print("\n🚀 Iniciando el procesador de datos...")
    os.makedirs(DIR_INPUTS, exist_ok=True)
    os.makedirs(DIR_MAESTRO, exist_ok=True)
    os.makedirs(DIR_OUTPUTS, exist_ok=True)

    patron_csv = os.path.join(DIR_INPUTS, "*.csv")
    archivos_csv = glob.glob(patron_csv)

    if not archivos_csv:
        print(f"⚠️ No se ha encontrado ningún archivo .csv en {DIR_INPUTS}.")
        return

    print(f"📦 Procesando {len(archivos_csv)} archivo(s) de alarmas...")
    lista_dfs = []

    for archivo in archivos_csv:
        try:
            df_temp = pd.read_csv(archivo, sep=';', encoding='utf-8', dtype=str, on_bad_lines='skip')
            if not df_temp.empty:
                df_temp = df_temp.dropna(how='all')
                lista_dfs.append(df_temp)
        except Exception as e:
            print(f"   ❌ Error leyendo {os.path.basename(archivo)}: {e}")

    if not lista_dfs:
        print("❌ Datos de alarmas vacíos o corruptos.")
        return

    df_total = pd.concat(lista_dfs, ignore_index=True)
    df_total.columns = df_total.columns.str.strip()

    if 'ICCID' not in df_total.columns:
        print("❌ Error crítico: No se encuentra la columna 'ICCID' en los CSVs.")
        return

    col_fecha_original = df_total.columns[12]
    df_total['Año'] = df_total[col_fecha_original].str.slice(0, 4)
    df_total['Mes'] = df_total[col_fecha_original].str.slice(5, 7)
    df_total = df_total[df_total[col_fecha_original] != col_fecha_original]
    df_total['ICCID_KEY'] = df_total['ICCID'].apply(limpiar_numero_estricto)

    print(f"📊 {len(df_total)} registros de alarmas unificados en memoria.")

    mapeo_maestro = {}
    if os.path.exists(PATH_MAESTRO_LOCAL):
        print(f"🔄 Buscando coincidencias en la pestaña del Maestro...")
        try:
            df_maestro = pd.read_excel(
                PATH_MAESTRO_LOCAL,
                sheet_name='Detalle DIGITAL Actual 2024',
                engine='openpyxl',
                dtype=str
            )
            df_maestro.columns = df_maestro.columns.str.strip()

            for _, fila in df_maestro.iterrows():
                mupi = fila.get('ID DIGITAL SAP')
                if pd.isna(mupi):
                    continue
                sim_orange = limpiar_numero_estricto(fila.get('SIM ORANGE'))
                sim_tlf = limpiar_numero_estricto(fila.get('SIM TELEFÓNICA'))

                if sim_orange and len(sim_orange) > 5:
                    mapeo_maestro[sim_orange] = str(mupi)
                if sim_tlf and len(sim_tlf) > 5:
                    mapeo_maestro[sim_tlf] = str(mupi)
        except Exception as e:
            print(f"   ❌ Error leyendo el Excel maestro: {e}")
    else:
        print(f"⚠️ Maestro no encontrado en {PATH_MAESTRO_LOCAL}. Usando solo excepciones.")

    mapeo_maestro.update(excepciones_limpias)

    print("🔍 Asignando nombres de MUPIs...")
    df_total['ID DIGITAL SAP'] = df_total['ICCID_KEY'].map(mapeo_maestro)

    columnas_originales = list(df_total.columns)
    if 'ICCID_KEY' in columnas_originales:
        columnas_originales.remove('ICCID_KEY')
    columnas_originales.remove('ID DIGITAL SAP')
    columnas_originales.remove(col_fecha_original)

    col_1_csv = columnas_originales.pop(0)
    col_2_csv = columnas_originales.pop(0)

    nuevo_orden = ['ID DIGITAL SAP', col_1_csv, col_2_csv, col_fecha_original] + columnas_originales
    df_final = df_total[nuevo_orden]

    coincidencias = df_final['ID DIGITAL SAP'].notna().sum()
    print(f"   ✅ Validación terminada: {coincidencias} de {len(df_final)} alarmas asignadas.")

    ruta_salida = os.path.join(DIR_OUTPUTS, "Control_Alarmas_Orange.xlsx")
    print(f"\n💾 Escribiendo archivo consolidado final...")
    try:
        with pd.ExcelWriter(ruta_salida, engine='openpyxl') as writer:
            df_final.to_excel(writer, sheet_name='Consolidado_Alarmas', index=False)
        print(f"🎉 ¡Proceso completado! Archivo en: {ruta_salida}")
    except Exception as e:
        print(f"❌ Error al escribir en disco: {e}")


if __name__ == "__main__":
    print("==================================================")
    print(" 🎯 PIPELINE DE ALARMAS ORANGE - INICIANDO SISTEMA ")
    print("==================================================")

    # 1. PASO 1: Descargar nuevos correos de Outlook
    print("\n[Paso 1/5] Ejecutando bot de descarga de correos...")
    try:
        subprocess.run(["python", "src/descargar_alarmas.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en el descargador de correos: {e}")
        exit(1)

    # 2. PASO 2: Respaldar los ficheros CSV históricos en SharePoint
    print("\n[Paso 2/5] Subiendo ficheros de alarmas a la nube (SharePoint)...")
    try:
        subprocess.run(["python", "src/subir_historicos.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Advertencia: No se pudieron respaldar los históricos: {e}")

    # 3. PASO 3: Descargar el Maestro actualizado desde SharePoint
    print("\n[Paso 3/5] Descargando maestro actualizado desde SharePoint...")
    try:
        subprocess.run(["python", "src/descargar_maestro.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Advertencia: Falló la descarga del maestro, se usará el local: {e}")

    # 4. PASO 4: Procesar todo con Pandas y generar el Excel
    print("\n[Paso 4/5] Ejecutando procesamiento y consolidación de datos...")
    procesar_datos_alarmas()

    # 5. PASO 5: Subir el informe final consolidado de vuelta a SharePoint
    print("\n[Paso 5/5] Subiendo informe final consolidado a SharePoint...")
    try:
        subprocess.run(["python", "src/subir_sharepoint.py"], check=True)
        print("\n✨ ¡PIPELINE EJECUTADO DE PUNTA A PUNTA CON ÉXITO! ✨")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Advertencia: No se pudo subir el informe final: {e}")
