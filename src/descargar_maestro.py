import os
from playwright.sync_api import sync_playwright

def descargar_maestro_sharepoint():
    ruta_maestro = os.path.join("data", "maestro")
    os.makedirs(ruta_maestro, exist_ok=True)

    archivo_salida = os.path.join(ruta_maestro, "Listado Mobiliario Digital NT_2025.xlsx")
    url_original = "https://jcdecaux.sharepoint.com/:x:/s/ES-P-Dir-Operaciones/IQBS92iz-5fRR4PVSfxm3dPwAV5DYW2u58jSqDLoHvmWFsc?e=5wE5a4"
    url_descarga = url_original + "&download=1"

    print("\n🌐 Conectando a SharePoint de forma segura...")

    with sync_playwright() as p:
        # Lanzamos el navegador
        browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        try:
            print("⬇️ Solicitando archivo Maestro...")

            # Usamos un bloque expect_download más robusto, permitiendo que la navegación ocurra
            with page.expect_download(timeout=45000) as download_info:
                # Navegamos indicando que no necesitamos que la interfaz gráfica termine de renderizar
                page.goto(url_descarga, wait_until="commit", timeout=45000)

            download = download_info.value

            # Limpiamos el anterior si existe para evitar conflictos
            if os.path.exists(archivo_salida):
                os.remove(archivo_salida)

            download.save_as(archivo_salida)
            print(f"✅ ¡Archivo Maestro descargado y actualizado con éxito en: {archivo_salida}!")

        except Exception as e:
            print(f"❌ Fallo al descargar el Maestro: {e}")
            os.makedirs("logs", exist_ok=True)
            page.screenshot(path="logs/error_maestro.png")
            print("📸 Pantallazo guardado en 'logs/error_maestro.png'.")

        finally:
            browser.close()

if __name__ == "__main__":
    descargar_maestro_sharepoint()
