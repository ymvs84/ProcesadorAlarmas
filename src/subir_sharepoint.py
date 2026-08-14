import os
import re
from playwright.sync_api import sync_playwright

def subir_archivo_sharepoint():
    ruta_archivo = os.path.join("data", "outputs", "Control_Alarmas_Orange.xlsx")

    if not os.path.exists(ruta_archivo):
        print(f"❌ No se encuentra el archivo para subir en: {ruta_archivo}")
        return

    url_destino = "https://jcdecaux.sharepoint.com/:f:/s/ES-P-Dir-Operaciones/IgDQiML3aEsUSZP1gJjmkNegAZadPo-eWtmGcGy2L984gRQ?e=xSYyvX"

    print("\n🌐 Conectando a SharePoint para subir el informe final...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        try:
            print("📁 Entrando en la carpeta destino...")
            page.goto(url_destino)
            page.wait_for_timeout(8000)

            print("⬆️ Desplegando menú de carga y seleccionando archivo...")

            # 1. Hacemos clic en el botón "+ Crear o cargar"
            btn_crear_cargar = page.get_by_text("Crear o cargar", exact=False)
            btn_crear_cargar.first.click()
            page.wait_for_timeout(1500)

            # 2. Esperamos y seleccionamos "Carga de archivos" capturando el selector de ficheros
            with page.expect_file_chooser(timeout=10000) as fc_info:
                page.get_by_text("Carga de archivos", exact=False).click()

            file_chooser = fc_info.value
            file_chooser.set_files(ruta_archivo)

            print("⏳ Subiendo y gestionando reemplazo si existe...")
            page.wait_for_timeout(5000)

            # 3. Si SharePoint avisa de que el archivo ya existe, pinchamos en "Reemplazar" o "Replace"
            try:
                btn_reemplazar = page.get_by_role("button", name=re.compile("Reemplazar|Replace", re.IGNORECASE))
                if btn_reemplazar.count() > 0:
                    btn_reemplazar.first.click()
                    print("🔄 Archivo existente reemplazado con éxito.")
                    page.wait_for_timeout(3000)
            except:
                pass # Si no salta el aviso de duplicado, continúa sin problema

            print("✅ ¡Archivo subido y sincronizado con éxito en SharePoint!")

        except Exception as e:
            print(f"❌ Error al subir: {e}")
            os.makedirs("logs", exist_ok=True)
            page.screenshot(path="logs/error_subida.png")
            print("📸 Pantallazo guardado en 'logs/error_subida.png'.")

        finally:
            browser.close()

if __name__ == "__main__":
    subir_archivo_sharepoint()
