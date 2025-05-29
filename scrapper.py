import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from mongo_utils import insertar_propiedades

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Crear driver Chrome configurado para scraping
# Incluye supresión de WebGL para evitar errores de rasterización

def crear_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-gpu")  # evitar errores GPU
    chrome_options.add_argument("--disable-webgl")  # evitar WebGL software fallback
    chrome_options.add_argument("--disable-software-rasterizer")  # evitar fallback de rasterización
    chrome_options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
    })
    return webdriver.Chrome(options=chrome_options)

# Extrae los datos de una propiedad usando un driver externo
def extraer_datos_detallados(driver, url):
    try:
        driver.set_page_load_timeout(10)
        driver.get(url)
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jsx-952467510.technical-sheet"))
        )
        html = driver.page_source
        driver.execute_script("window.stop();")
        soup = BeautifulSoup(html, "html.parser")

        contenedor_info = soup.find("div", class_="jsx-952467510 technical-sheet")
        precio_raw = soup.find("span", class_="ant-typography price heading heading-3 high")
        administracion_raw = soup.find("span", class_="ant-typography commonExpenses body body-regular body-1 medium")
        ubicacion_raw = soup.find("p", class_="jsx-3623903256 body body-regular medium")
        ubicacion = ubicacion_raw.get_text(strip=True) if ubicacion_raw else "No disponible"
        print(f"🔗 Procesando URL: {url}")
        print(ubicacion.split(","))
        if( len(ubicacion.split(",")) < 3):
            barrio = "N/A"
            ciudad = ubicacion.split(",")[0].strip() if ubicacion else "No disponible"
            departamento = ubicacion.split(",")[1].strip()
        else:
            barrio = ubicacion.split(",")[0] if ubicacion else "No disponible"
            ciudad = ubicacion.split(",")[1].strip() if ubicacion else "No disponible"
            departamento = ubicacion.split(",")[2].strip() if ubicacion else "No disponible"
        
        info_items = contenedor_info.find_all("div") if contenedor_info else []
        datos = [item.get_text(strip=True) for item in info_items if item.get_text(strip=True)]
        precio = precio_raw.get_text(strip=True) if precio_raw else "No disponible"

        if administracion_raw:
            administracion_texto = administracion_raw.get_text(strip=True)
            administracion = administracion_texto.split("$ ")[-1].strip() if "$ " in administracion_texto else "No disponible"
        else:
            administracion = "N/A"

        datos_organizados = {
            "Enlace": url,
            "Precio": precio,
            "Administración": administracion,
            "Barrio": barrio,
            "Ciudad": ciudad,
            "Municipio": departamento,
            "Tipo": "Venta" if "venta" in url else "Arriendo"
        }

        i = 0
        while i < len(datos) - 2:
            if datos[i] == "•":
                clave_actual = datos[i + 1].strip()
                valor = datos[i + 2].strip()
                if valor == "¡Pregúntale!":
                    valor = "N/A"
                datos_organizados[clave_actual] = valor
                i += 3
            else:
                i += 1
        return datos_organizados

    except Exception as e:
        print(f"❌ Error en {url}: {e}")
        return None

# Recolecta y guarda datos de propiedades desde la paginación de FincaRaíz
# Reutiliza un solo driver de detalle por cada 2 páginas

def obtener_datos_propiedades(pagina_url, tipo):
    pagina_actual = 1
    paginas = 50
    total_propiedades = 0
    tiempos_paginas = []
    driver_detalle = crear_driver()

    while pagina_actual <= paginas:
        print(f"🔍 Página {pagina_actual}: {pagina_url}")
        inicio_pagina = time.time()
        propiedades_pagina = []

        driver = crear_driver()
        try:
            driver.set_page_load_timeout(15)
            driver.get(pagina_url)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "listingsWrapper"))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            contenedor = soup.find("section", class_="listingsWrapper")
            tarjetas = contenedor.find_all("div", class_="listingCard") if contenedor else []
        except Exception as e:
            print(f"❌ Error al procesar la página {pagina_actual}: {e}")
            driver.quit()
            break
        driver.quit()

        for tarjeta in tarjetas:
            enlace = tarjeta.find("a", class_="lc-cardCover")
            if enlace and "href" in enlace.attrs:
                url = "https://www.fincaraiz.com.co" + enlace["href"]
                datos = extraer_datos_detallados(driver_detalle, url)
                if datos:
                    propiedades_pagina.append(datos)

        if pagina_actual % 2 == 0:
            driver_detalle.quit()
            driver_detalle = crear_driver()

        if propiedades_pagina:
            insertar_propiedades(propiedades_pagina, tipo)
            print(f"✔ Guardadas {len(propiedades_pagina)} propiedades de la página {pagina_actual}")
        else:
            print(f"⚠ No se extrajeron propiedades válidas de la página {pagina_actual}")

        fin_pagina = time.time()
        duracion = fin_pagina - inicio_pagina
        tiempos_paginas.append(duracion)
        total_propiedades += len(propiedades_pagina)

        print(f"⏱ Tiempo de página {pagina_actual}: {duracion:.2f} segundos")
        if len(propiedades_pagina) > 0:
            promedio = duracion / len(propiedades_pagina)
            print(f"📊 Tiempo promedio por propiedad: {promedio:.2f} segundos\n")
        else:
            print("📊 Tiempo promedio por propiedad: N/A\n")

        pagina_actual += 1
        pagina_url = f"https://www.fincaraiz.com.co/{tipo}/casas-y-apartamentos/usados/pagina{pagina_actual}"
        time.sleep(1)

    driver_detalle.quit()
    print(f"🔚 {tipo.upper()}: {total_propiedades} propiedades extraídas")
    if tiempos_paginas:
        tiempo_total = sum(tiempos_paginas)
        print(f"📈 Tiempo promedio por página: {tiempo_total / len(tiempos_paginas):.2f} segundos\n")

# Iniciar proceso completo
start_time = time.time()
obtener_datos_propiedades("http://fincaraiz.com.co/venta/casas-y-apartamentos/usados", "venta")
obtener_datos_propiedades("http://fincaraiz.com.co/arriendo/casas-y-apartamentos/usados", "arriendo")
end_time = time.time()
print(f"🟢 Tiempo total de ejecución: {end_time - start_time:.2f} segundos")