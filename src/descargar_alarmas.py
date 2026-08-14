import os
from playwright.sync_api import sync_playwright
import re

def extraer_multiples_adjuntos():
    os.makedirs("data/inputs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        try:
            print("🌍 Entrando en la bandeja de entrada...")
            page.goto("https://outlook.office.com/mail/")
            page.wait_for_timeout(8000)

            print("📁 Entrando en la carpeta 'Orange_Alarmas'...")
            page.get_by_text("Orange_Alarmas").click()
            page.wait_for_timeout(5000)

            print("📩 Seleccionando el primer correo para iniciar la lectura...")
            lista_correos = page.locator("div[role='option']")
            if lista_correos.count() == 0:
                print("⚠️ La carpeta está vacía.")
                return

            lista_correos.first.click()
            page.wait_for_timeout(3000)

            correo_actual = 1
            archivos_existentes_seguidos = 0

            while True:
                print(f"\n--- Procesando correo {correo_actual} ---")

                texto_pantalla = page.locator("body").inner_text()
                match_fecha = re.search(r'ALARMS_(\d{8})', texto_pantalla)

                if match_fecha:
                    fecha_str = match_fecha.group(1)
                    if int(fecha_str) < 20260801:
                        print(f"🛑 Correo antiguo detectado (Fecha: {fecha_str}). ¡Freno de mano por fecha tirado!")
                        break

                adjuntos = page.locator("text=ALARMS_")
                if adjuntos.count() == 0:
                    print("⚠️ No hay archivo ALARMS_ en este correo.")
                else:
                    print("👀 Abriendo vista previa...")
                    adjuntos.last.click()
                    page.wait_for_timeout(4000)

                    try:
                        with page.expect_download(timeout=10000) as download_info:
                            page.get_by_text("Descargar").click()

                        download = download_info.value
                        nombre_real = download.suggested_filename
                        ruta_final = os.path.join("data", "inputs", nombre_real)

                        if os.path.exists(ruta_final):
                            print(f"⏭️ El archivo '{nombre_real}' ya existe. Cancelando descarga...")
                            download.cancel()

                            archivos_existentes_seguidos += 1
                            if archivos_existentes_seguidos >= 5:
                                print("🛑 5 archivos repetidos seguidos. Asumimos que estamos al día. ¡Freno inteligente activado!")
                                break
                        else:
                            download.save_as(ruta_final)
                            print(f"✅ ¡Descargado y guardado! -> {nombre_real}")
                            archivos_existentes_seguidos = 0

                    except Exception as e:
                        print("❌ Ocurrió un error al intentar descargar este adjunto.")

                    print("❌ Cerrando la vista previa...")
                    try:
                        botones_cerrar = page.locator("[aria-label='Cerrar'], [aria-label='Close'], [title='Cerrar'], [title='Close']")
                        if botones_cerrar.count() > 0:
                            botones_cerrar.last.click(timeout=3000)
                        else:
                            page.keyboard.press("Escape")
                    except:
                        page.keyboard.press("Escape")
                    page.wait_for_timeout(2000)

                # --- PASAR AL SIGUIENTE CORREO (DOBLE BLINDAJE) ---
                correo_activo = page.locator("div[role='option'][aria-selected='true']")
                if correo_activo.count() > 0:
                    id_correo_actual = correo_activo.first.get_attribute("id")
                    print("⬇️ Bajando con la flecha...")
                    correo_activo.first.press("ArrowDown")
                    page.wait_for_timeout(2000)

                    correo_activo_nuevo = page.locator("div[role='option'][aria-selected='true']")
                    id_correo_nuevo = correo_activo_nuevo.first.get_attribute("id") if correo_activo_nuevo.count() > 0 else None

                    if id_correo_actual == id_correo_nuevo:
                        print("⚠️ La flecha fue ignorada. Haciendo clic forzado...")
                        correos_visibles = page.locator("div[role='option']").all()
                        movido = False
                        for i, c in enumerate(correos_visibles):
                            if c.get_attribute("id") == id_correo_actual:
                                if i + 1 < len(correos_visibles):
                                    correos_visibles[i + 1].click(force=True)
                                    movido = True
                                    break
                        if not movido:
                            print("🔚 Se ha tocado el fondo absoluto de la carpeta de correos.")
                            break
                        page.wait_for_timeout(2000)
                else:
                    page.locator("div[role='option']").first.click(force=True)
                    page.wait_for_timeout(2000)

                correo_actual += 1
            print("\n🎉 ¡DESCARGA DE CORREOS FINALIZADA!")
        except Exception as e:
            print(f"❌ Fallo en la descarga de correos: {e}")
            page.screenshot(path="logs/error_paginacion.png")
        finally:
            browser.close()

if __name__ == "__main__":
    extraer_multiples_adjuntos()
