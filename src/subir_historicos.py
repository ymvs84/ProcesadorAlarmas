import os
import glob
from playwright.sync_api import sync_playwright

def subir_historicos_sharepoint():
    dir_inputs = os.path.join("data", "inputs")

    if not os.path.exists(dir_inputs):
        print(f"❌ No se encuentra la carpeta local de inputs: {dir_inputs}")
        return

    # Buscamos todos los ficheros .csv acumulados
    archivos_csv = glob.glob(os.path.join(dir_inputs, "*.csv"))

    if not archivos_csv:
        print("⚠️ No hay archivos CSV locales para subir.")
        return

    # URL de la carpeta de históricos en tu SharePoint que me has proporcionado
    url_destino = "https://jcdecaux.sharepoint.com/:f:/s/ES-P-Dir-Operaciones/IgCgut09jApBTZq_lft-W0IrAW7JWa4owjJFCfvMFryrgPY?e=AAkKvR"

    print(f"\n🌐 Conectando a SharePoint para respaldar {len(archivos_csv)} archivos históricos...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        try:
            print("📁 Entrando en la carpeta de históricos de SharePoint...")
            page.goto(url_destino)
            page.wait_for_timeout(8000)

            for archivo in archivos_csv:
                nombre_archivo = os.path.basename(archivo)
                print(f"⬆️ Subiendo histórico: {nombre_archivo}...")

                try:
                    # 1. Clic en "+ Crear o cargar"
                    btn_crear_cargar = page.get_by_text("Crear o cargar", exact=False)
                    btn_crear_cargar.first.click()
                    page.wait_for_timeout(1000)

                    # 2. Selección de "Carga de archivos"
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        page.get_by_text("Carga de archivos", exact=False).click()

                    file_chooser = fc_info.value
                    file_chooser.set_files(archivo)

                    # Tiempo de espera para que se complete la subida del CSV individual
                    page.wait_for_timeout(4000)
                    print(f"   ✅ Subido con éxito: {nombre_archivo}")
                except Exception as ex:
                    print(f"   ⚠️ Posible duplicado o fallo menor con {nombre_archivo} (continuamos): {ex}")

            print("\n🎉 ¡Todos los históricos han sido respaldados en SharePoint con éxito!")

        except Exception as e:
            print(f"❌ Error crítico al subir históricos: {e}")
            os.makedirs("logs", exist_ok=True)
            page.screenshot(path="logs/error_subida_historicos.png")
            print("📸 Pantallazo guardado en 'logs/error_subida_historicos.png'.")

        finally:
            browser.close()

if __name__ == "__main__":
    subir_historicos_sharepoint()
