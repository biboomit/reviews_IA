import streamlit as st
import pandas as pd
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from funciones import login
import os
import requests
import openai
import requests
from io import BytesIO
from PIL import Image
import base64

st.set_page_config(page_title="Facebook Ads Analyzer", layout="wide")

logo_path = "company_logo.png"
st.markdown(
    f"""
    <style>
        /* 🔥 Animaciones */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes typing {{
            from {{
                width: 0;
            }}
            to {{
                width: 100%;
            }}
        }}

        /* 🔹 Navbar completamente transparente */
        .navbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 20px;
            background: linear-gradient(135deg, #1E90FF, #0A2647); /* 🔥 Barra completamente invisible */
            border-radius: 7px; /* 🔹 Sin bordes */
            box-shadow: 0px 4px 10px rgba(255, 255, 255, 0.1); /* 🔥 Vuelve a agregar sombra tenue */
            margin-bottom: 20px;
        }}

        .navbar img {{
            max-width: 120px;
            animation: fadeInUp 1s ease-out;
        }}

        .navbar h1 {{
            font-size: 36px;  /* 🔹 Tamaño del título */
            color: white; /* 🔹 Asegura que el texto sea legible */
            font-weight: bold;
            margin: 0;
            flex-grow: 1;
            text-align: center;
            overflow: hidden;
            white-space: nowrap;
            border-right: none; /* 🔹 Elimina la barra blanca del final */
            width: 0;
            animation: typing 3s steps(40) forwards, fadeInUp 1s ease-out;
        }}

        /* 🔹 Personalización del botón "Ingresar" en el Login */
        div.stButton > button {{
            background-color: #1E90FF !important;  /* 🔵 Azul brillante */
            color: white !important;  /* 🔹 Texto en blanco */
            font-size: 16px !important;
            font-weight: bold !important;
            border-radius: 8px !important; /* 🔹 Bordes redondeados */
            padding: 10px 20px !important;
            border: none !important;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }}

        /* 🔥 Efecto hover cuando el usuario pasa el mouse */
        div.stButton > button:hover {{
            background-color: gold !important; /* 🔵 Azul más oscuro en hover */
            transform: scale(1.05); /* 🔹 Hace que el botón crezca un poco */
        }}

        /* 🔥 Efecto click */
        div.stButton > button:active {{
            transform: scale(0.95); /* 🔹 Reduce un poco el tamaño cuando se hace click */
        }}

        /* 🔹 Restaurar los estilos de KPI con hover dinámico */
        .kpi-box {{
             background: linear-gradient(135deg, #1E90FF, #0A2647); /* 🔵 Degradado azul */
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3); /* 🔹 Sombra más fuerte */
            width: 180px;
            height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
            font-family: 'Arial', sans-serif;
            transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
        }}

        .kpi-box:hover {{
            transform: scale(1.05); /* 🔥 Efecto de crecimiento */
            box-shadow: 0 8px 20px rgba(30, 144, 255, 0.7); /* 🔵 Brillo azul claro */        }}

        .kpi-title {{
            font-size: 16px;
            font-weight: bold;
            margin: 0;
         }}

                /* 🔹 Valores numéricos en las tarjetas KPI */
        .kpi-value {{
            font-size: 30px;
            font-weight: bold;
         }}

    </style>
    <div class="navbar">
    <img src="data:image/png;base64,{base64.b64encode(open(logo_path, 'rb').read()).decode()}" width="130" height="45" />
        <h1>{'Boomit - Social Intelligence'}</h1>
    </div>
    
    """,
    unsafe_allow_html=True
)

# =========================
# 🔐 Verificar autenticación
# =========================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    login()
    st.stop()


# Define la ruta al chromedriver en la misma carpeta donde está el .py
def get_chromedriver_path() -> str:
    return shutil.which('chromedriver')

#CHROMEDRIVER_PATH = os.path.join(current_dir, 'chromedriver.exe')
CHROMEDRIVER_PATH = get_chromedriver_path()

# Diccionario de países soportados
COUNTRY_MAP = {
    "Mexico": "MX",
    "Argentina": "AR",
    "Chile": "CL",
    "Colombia": "CO",
    "Ecuador": "EC",
    "Peru": "PE",
    "Uruguay": "UY",
    "Paraguay": "PY",
    "Bolivia": "BO",
    "Venezuela": "VE",
    "Brazil": "BR",
    "United States": "US",
    "Canada": "CA",
    "Spain": "ES",
    "France": "FR",
    "Germany": "DE",
    "Italy": "IT",
    "United Kingdom": "GB",
    "Australia": "AU",
    "New Zealand": "NZ",
    "Japan": "JP",
    "China": "CN",
    "India": "IN",
    "South Korea": "KR",
    "Russia": "RU",
    "South Africa": "ZA"
}

# Diccionario para identificar plataformas
PLATFORM_MAP = {
    "-135px -351px": "Instagram",
    "-34px -222px": "Facebook",
    "-68px -189px": "Audience Network",
    "-148px -351px": "Messenger"
}

# Directorio temporal para almacenar imágenes
temp_dir = "temp_images"
os.makedirs(temp_dir, exist_ok=True)

def clear_temp_images():
    """Elimina todas las imágenes en la carpeta temporal antes de guardar nuevas."""
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

#@st.cache_data
def extract_ads(country_code, domain):
    """Extrae anuncios desde la biblioteca de anuncios de Facebook"""
    
    # Limpiar imágenes previas
    clear_temp_images()
    
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country={country_code}&q={domain}&search_type=keyword_unordered&media_type=all"
    driver.get(url)
    
    ads_data = []
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        ads = driver.find_elements(By.XPATH, "//div[contains(@class, '_7jvw x2izyaf x1hq5gj4 x1d52u69')]")

        # for ad in ads:
        #     span_elements = ad.find_elements(By.TAG_NAME, "span")
        #     for span in span_elements:
        #         print("SPAN TEXT:", span.text)
        
        for index, ad in enumerate(ads):
            try:
                #ad_id = ad.find_element(By.XPATH, ".//span[contains(text(), 'Identificador de la biblioteca')]").text.replace("Identificador de la biblioteca: ", "").strip() #REEMPLAZAR ESTA PARTE PARA CORRER EN LOCAL
                ad_id = ad.find_element(By.XPATH, ".//span[contains(text(), 'Library ID')]").text.replace("Library ID: ", "").strip() #webdriver en ingles
                
            except NoSuchElementException:
                ad_id = "No ID"
                
            platforms = set()
            try:
                platform_elements = ad.find_elements(By.XPATH, ".//div[contains(@class, 'xtwfq29')]")
                for element in platform_elements:
                    style = element.get_attribute("style")
                    if "mask-position" in style:
                        mask_position = style.split("mask-position: ")[-1].split(";")[0].strip()                                      
                        if mask_position in PLATFORM_MAP:
                            platforms.add(PLATFORM_MAP[mask_position])
            except NoSuchElementException:
                pass
            
            try:
                #start_date = ad.find_element(By.XPATH, ".//span[contains(text(), 'En circulación desde')]").text.replace("En circulación desde ", "").replace("el ", "").strip()
                start_date = ad.find_element(By.XPATH, ".//span[contains(text(), 'Started running on')]").text.replace("Started running on ", "").replace("el ", "").strip()
                
            except NoSuchElementException:
                start_date = "No Date"
            
            try:
                ad_text = ad.find_element(By.XPATH, ".//div[contains(@class, '_4ik4 _4ik5')]//div[@style='white-space: pre-wrap;']/span").text.strip()
            except NoSuchElementException:
                ad_text = "No Text"
            
            try:
                status = ad.find_element(By.XPATH, ".//span[contains(@class, 'x8t9es0')]").text.strip()
            except NoSuchElementException:
                status = "No Status"
            
            try:
                image_element = ad.find_element(By.XPATH, ".//img[contains(@class, 'x1ll5gia x19kjcj4 xh8yej3')]")
                image_url = image_element.get_attribute("src").strip()
                image_path = os.path.join(temp_dir, f"{ad_id}.jpg")
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    with open(image_path, "wb") as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)
                else:
                    image_path = "No Image"
            except NoSuchElementException:
                image_url = "No Image"
                image_path = "No Image"
            
            ad_info = {
                "Ad ID": ad_id,
                "Start Date": start_date,
                "Ad Text": ad_text,
                "Status": status,
                "Image URL": image_url,
                "Image Path": image_path,
            }
            
            for platform in PLATFORM_MAP.values():
                ad_info[platform] = 1 if platform in platforms else 0
            
            ads_data.append(ad_info)
    except Exception as e:
        st.error(f"Error detectando anuncios: {e}")
    finally:
        driver.quit()
    
    return pd.DataFrame(ads_data)


def fetch_images_from_urls(image_urls):
    """Descarga imágenes desde una lista de URLs y las convierte en Base64 para OpenAI."""
    images_base64 = []
    
    for url in image_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                buffered = BytesIO()
                img.save(buffered, format="JPEG")  # Convertir a JPEG para reducir tamaño
                img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                images_base64.append({"url": url, "image_base64": img_base64})
        except Exception as e:
            print(f"⚠ Error al descargar imagen {url}: {e}")
    
    return images_base64


def get_openai_insights(df_ads, OPENAI_API_KEY, ASSISTANT_ID):
    """Generar insights usando OpenAI con imágenes y datos de anuncios."""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        thread = client.beta.threads.create()
        
        # Extraer URLs válidas de imágenes (solo URLs públicas)
        image_urls = [url for url in df_ads["Image URL"].dropna().tolist() if url.startswith("http")]
        image_urls = image_urls[:9]  # Limitar a 9 imágenes para evitar errores de OpenAI
        
        print(df_ads[[col for col in PLATFORM_MAP.values()]].sum().to_dict()) #mutear

        prompt_text = (
            "Analiza la estrategia de anuncios de un competidor en Meta Ads y proporciona insights relevantes "
            "para identificar tácticas exitosas que puedan ser aprovechadas o adaptadas en nuestra estrategia publicitaria.\n\n"
            f"📊 **Total de anuncios analizados:** {len(df_ads)}\n"
            #f"📌 **Distribución de anuncios por plataforma:** {df_ads[[col for col in PLATFORM_MAP.values()]].sum().to_dict()}\n"
            f"📝 **Ejemplo de textos utilizados en los anuncios más antiguos:**\n{' '.join(df_ads['Ad Text'].dropna().unique())[:2000]}\n\n"
            
            "🔍 **Objetivos del análisis:**\n"
            "- ¿Cuáles son los principales enfoques en los textos publicitarios del competidor?\n"
            "- ¿Qué tipo de mensajes y llamados a la acción están utilizando?\n"
            "- ¿En qué plataformas están priorizando su inversión publicitaria?\n"
            "- ¿Cómo varían sus anuncios según la plataforma utilizada?\n"
            "- ¿Se observa un patrón en la duración de los anuncios más exitosos?\n"
            "- ¿Se están repitiendo ciertos mensajes o hay una alta diversidad creativa?\n"
            "- ¿Qué insights se pueden extraer para mejorar nuestra estrategia basándonos en estas observaciones?\n\n"
            
            "📸 **Análisis visual de los anuncios:**\n"
            "- ¿Cuáles son los colores predominantes en los anuncios?\n"
            "- ¿Los anuncios son más visuales o dependen del texto?\n"
            "- ¿Se observan patrones en el estilo de diseño?\n"
            "- ¿Los anuncios usan imágenes de productos, testimonios, ilustraciones u otros elementos gráficos?\n"
            "- ¿Cómo se pueden adaptar estos elementos visuales a nuestra estrategia sin perder autenticidad?\n\n"
            
            "🎯 **Conclusión:**\n"
            "- Basado en este análisis, ¿qué tácticas podríamos considerar incorporar en nuestra estrategia?\n"
            "- ¿Qué aspectos parecen funcionar mejor en la estrategia del competidor?\n"
            "- ¿Qué oportunidades o áreas de mejora podríamos explotar para diferenciarnos?\n"
            "Aquí tienes algunas imágenes de los anuncios de la competencia. Analízalas y proporciona insights:"
        )

        # Crear mensaje con texto y las imágenes como `image_url`
        message_content = [{"type": "text", "text": prompt_text}]
        message_content += [{"type": "image_url", "image_url": {"url": url}} for url in image_urls]

        # Enviar solicitud al assistant
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_content
        )
        
        # Ejecutar la solicitud
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        with st.spinner("🔄 Generating insights, please wait..."):
            while run.status != "completed":
                time.sleep(2)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        # Obtener la respuesta
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        return messages.data[0].content[0].text.value
    except Exception as e:
        return f"Error retrieving insights from OpenAI: {e}"


# Streamlit UI
st.title("📢 Facebook Ads Analyzer")

# Selección de país
selected_country = st.selectbox("Select a country", list(COUNTRY_MAP.keys()))
country_code = COUNTRY_MAP[selected_country]

# Campo para ingresar dominio
advertiser_domain = st.text_input("Enter the advertiser's domain", "alige.com.mx")

# Botón para iniciar scraping
if st.button("Search ads"):
    with st.spinner("🔄 Searching ads, please wait..."):
        df_ads = extract_ads(country_code, advertiser_domain)
        st.session_state.df_ads = df_ads  # Guardar en session_state

# Verificar si hay datos almacenados en la sesión
if "df_ads" in st.session_state and not st.session_state.df_ads.empty:
    df_ads = st.session_state.df_ads
    df_ads["Start Date"] = pd.to_datetime(df_ads["Start Date"], errors='coerce')
    df_ads.to_excel('df_ads.xlsx', index=False)

    st.success(f"Ads found!")
    #st.dataframe(df_ads)

    # Mostrar imágenes del Top 5 de mayor duración en una fila
    df_top_ads = df_ads.sort_values("Start Date").head(5)
    st.subheader("🏆 Most valuable ads")
    col1, col2, col3, col4, col5 = st.columns(5)

    for col, (_, row) in zip([col1, col2, col3, col4, col5], df_top_ads.iterrows()):
        if row["Image Path"] != "No Image":
            col.image(row["Image Path"], caption=row["Ad ID"], use_container_width=True)

    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    ASSISTANT_ID = st.secrets["ASSISTANT_ID"]

    if st.button("💡 Generate Insights"):

        output_placeholder = st.empty()

        insights = get_openai_insights(df_ads, OPENAI_API_KEY, ASSISTANT_ID)

        output_placeholder.markdown("#### 📊 Insights Generated")
        output_placeholder.info(insights)



