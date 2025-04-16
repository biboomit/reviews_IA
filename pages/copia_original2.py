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
from selenium.webdriver.common.keys import Keys
from funciones import login
import os
import requests
import openai
import requests
from io import BytesIO
from PIL import Image
import base64
import re

st.set_page_config(page_title="Facebook Ads Analyzer", layout="wide")

with st.sidebar:
    st.page_link('app.py', label='App reviews analyzer', icon='🔥')
    st.page_link('pages/copia_original2.py', label='📈 Facebook ads library scraping')


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
            background: linear-gradient(135deg, #1E90FF, #0A2647);
            border-radius: 7px;
            box-shadow: 0px 4px 10px rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
        }}

        .navbar img {{
            max-width: 120px;
            animation: fadeInUp 1s ease-out;
        }}

        .navbar h1 {{
            font-size: 36px;
            color: white;
            font-weight: bold;
            margin: 0;
            flex-grow: 1;
            text-align: center;
            overflow: hidden;
            white-space: nowrap;
            border-right: none;
            width: 0;
            animation: typing 3s steps(40) forwards, fadeInUp 1s ease-out;
        }}

        /* 🔹 Personalización del botón "Ingresar" */
        div.stButton > button {{
            background-color: #1E90FF !important;
            color: white !important;
            font-size: 16px !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }}

        div.stButton > button:hover {{
            background-color: gold !important;
            transform: scale(1.05);
        }}

        div.stButton > button:active {{
            transform: scale(0.95);
        }}

        /* 🔹 Estilos KPI */
        .kpi-box {{
            background: linear-gradient(135deg, #1E90FF, #0A2647);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
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
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(30, 144, 255, 0.7);
        }}

        /* 🔹 Estilos para Insights */
        .custom-insights-box {{
            background: linear-gradient(135deg, #1E90FF, #0A2647) !important;
            color: white !important;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            animation: fadeInUp 0.5s ease-out;
        }}

        .custom-insights-box h2, 
        .custom-insights-box h3 {{
            color: gold !important;
            margin-bottom: 12px;
            border-bottom: 2px solid rgba(255, 215, 0, 0.3);
            padding-bottom: 5px;
        }}

        .custom-insights-box ul {{
            margin-left: 25px;
            line-height: 1.8;
            padding-left: 15px;
        }}

        .custom-insights-box li {{
            margin-bottom: 8px;
            font-size: 16px;
            position: relative;
        }}

        .custom-insights-box li::before {{
            content: "•";
            color: gold;
            font-size: 20px;
            position: absolute;
            left: -15px;
            top: -1px;
        }}
        
        /* 🔹 Estilos para tabs de brand inputs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 24px;
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(30, 144, 255, 0.1);
            border-radius: 6px 6px 0 0;
            padding: 10px 16px;
            font-weight: 500;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: rgba(30, 144, 255, 0.2);
            color: #1E90FF;
            font-weight: 600;
            border-bottom: 2px solid #1E90FF;
        }}
        
        /* 🔹 Estilos para color picker */
        .color-box {{
            width: 30px;
            height: 30px;
            display: inline-block;
            margin-right: 5px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}

        /* Estilos para tarjetas de insights */
        .insight-card {{
            background: linear-gradient(135deg, #1E90FF, #0A2647);
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            color: white !important;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            animation: fadeInUp 0.5s ease-out;
        }}
        
        .insight-card h3 {{
            color: gold !important;
            margin-bottom: 15px;
            font-size: 20px;
            font-weight: bold;
            border-bottom: 2px solid rgba(255, 215, 0, 0.3);
            padding-bottom: 8px;
        }}
        
        .insight-card h2 {{
            color: gold !important;
            margin: 25px 0 15px 0;
            font-size: 22px;
            font-weight: bold;
            border-bottom: 2px solid rgba(255, 215, 0, 0.5);
            padding-bottom: 8px;
        }}
        
        .insight-card ul {{
            list-style-type: none;
            padding-left: 5px;
            margin-left: 10px;
        }}
        
        .insight-card ul li {{
            margin-bottom: 12px;
            position: relative;
            padding-left: 20px;
            line-height: 1.5;
        }}
        
        .insight-card ul li:before {{
            content: "•";
            color: gold;
            font-size: 18px;
            position: absolute;
            left: 0;
            top: 0px;
        }}
        
        .insight-card b, .insight-card strong {{
            color: gold;
            font-weight: bold;
        }}
        
        /* Estilo para el expander */
        .streamlit-expanderHeader {{
            font-weight: bold;
            color: #1E90FF !important;
            background-color: rgba(30, 144, 255, 0.1);
            border-radius: 5px;
        }}
        
        .streamlit-expanderContent {{
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 0 0 5px 5px;
            max-height: none !important;
            overflow: visible !important;
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

def get_chromedriver_path() -> str:
    return shutil.which('chromedriver')

#CHROMEDRIVER_PATH = os.path.join(current_dir, 'chromedriver.exe')
CHROMEDRIVER_PATH = get_chromedriver_path()

# Diccionario de países soportados
COUNTRY_MAP = {
    "Argentina": "AR", "Belice": "BZ", "Bolivia": "BO", "Brasil": "BR", "Chile": "CL",
    "Colombia": "CO", "Costa Rica": "CR", "Cuba": "CU", "Ecuador": "EC",
    "El Salvador": "SV", "Estados Unidos": "US", "Guatemala": "GT", "Honduras": "HN",
    "México": "MX", "Nicaragua": "NI", "Panamá": "PA", "Paraguay": "PY", "Perú": "PE",
    "Puerto Rico": "PR", "República Dominicana": "DO", "Uruguay": "UY", "Venezuela": "VE"
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

# Directorio para almacenar información de la marca
brand_dir = "brand_assets"
os.makedirs(brand_dir, exist_ok=True)

def clear_temp_images():
    """Elimina todas las imágenes en la carpeta temporal antes de guardar nuevas."""
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

def get_advertiser_suggestions(country_code, domain):
    """Extrae el texto y el logo de los elementos específicos de la clase"""
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country={country_code}&q={domain}&search_type=keyword_unordered&media_type=all"
    driver.get(url)
    
    data = []
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Buscar y hacer clic en el campo de búsqueda para activar el dropdown
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='search']"))
        )
        search_input.click()
        
        # Esperar a que aparezcan los resultados del dropdown
        time.sleep(3)
        
        # Buscar los elementos li que contienen los resultados
        advertiser_list_items = driver.find_elements(By.XPATH, "//li[@role='option']")
        
        for item in advertiser_list_items:
            try:
                # Extraer el ID de página del atributo id del li
                li_id = item.get_attribute("id")
                page_id = None
                if li_id and "pageID:" in li_id:
                    page_id = li_id.split("pageID:")[1].strip()
                
                # Extraer el nombre del anunciante
                ad_text_element = item.find_element(By.XPATH, ".//div[@aria-level='3']")
                ad_text = ad_text_element.text if ad_text_element else "Unknown Advertiser"
                
                # Extraer la URL del logo
                logo_element = item.find_element(By.XPATH, ".//img[contains(@class, 'xz74otr')]")
                logo_url = logo_element.get_attribute("src") if logo_element else None
                
                data.append({
                    "name": ad_text, 
                    "logo": logo_url,
                    "page_id": page_id
                })
            except Exception as e:
                print(f"Error extrayendo datos del elemento: {e}")
                continue
                
    except Exception as e:
        driver.save_screenshot("error_final.png")
        return [f"Error: {str(e)}"]
    finally:
        driver.quit()
    
    return data



def extract_ads(country_code, selected_advertiser):
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
    options.add_argument("--lang=en-US")
    options.add_argument("Accept-Language=en-US")

    
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    # Determina URL basada en el tipo de selected_advertiser
    if isinstance(selected_advertiser, dict):
        advertiser_name = selected_advertiser['name']
        # Si tenemos page_id, usarlo para una búsqueda más precisa
        if 'page_id' in selected_advertiser and selected_advertiser['page_id']:
            url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={country_code}&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id={selected_advertiser['page_id']}"
        else:
            url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={country_code}&q={advertiser_name}&search_type=keyword_unordered&media_type=all"
    else:
        # Si es un string, usarlo directamente
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={country_code}&q={selected_advertiser}&search_type=keyword_unordered&media_type=all"
    
    driver.get(url)
    current_url = driver.current_url
    if f"country={country_code}" not in current_url:
        corrected_url = re.sub(r"country=\w\w", f"country={country_code}", current_url)
        driver.get(corrected_url)

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

def save_uploaded_file(uploaded_file, directory, filename=None):
    """Guarda un archivo subido en el directorio especificado"""
    if uploaded_file is not None:
        if not filename:
            filename = uploaded_file.name
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath
    return None

def get_openai_insights_and_images(df_ads, brand_info, OPENAI_API_KEY, ASSISTANT_ID):
    """Generar insights y propuestas creativas + imágenes nuevas usando OpenAI y DALL·E."""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        thread = client.beta.threads.create()

        # Extraer imágenes del competidor - solo usamos URLs para evitar problemas
        competitor_image_urls = [url for url in df_ads["Image URL"].dropna().tolist() if url.startswith("http")]
        competitor_image_urls = competitor_image_urls[:3]  # Limitamos a 3 para evitar sobrecarga
        
        # Preparar información de la marca
        brand_name = brand_info.get("brand_name", "")
        brand_description = brand_info.get("brand_description", "")
        brand_colors = brand_info.get("brand_colors", [])
        colors_text = ", ".join([f"{name}: {code}" for name, code in brand_colors])

        # Crear el prompt solo con el texto
        prompt_text = (
            "Eres un experto en creatividad publicitaria. Analiza estos anuncios de un competidor "
            "y genera insights + propuestas visuales creativas superadoras para una marca.\n\n"
            f"📊 INFORMACIÓN DE LA MARCA DEL CLIENTE:\n"
            f"- Nombre: {brand_name}\n"
            f"- Descripción: {brand_description}\n"
            f"- Paleta de colores: {colors_text}\n\n"
            f"📊 INFORMACIÓN DEL COMPETIDOR:\n"
            f"- Total anuncios analizados: {len(df_ads)}\n"
            f"- Textos ejemplo: {' '.join(df_ads['Ad Text'].dropna().unique())[:1500]}\n\n"
            "📋 INSTRUCCIONES:\n"
            "1. Da insights sobre el estilo, tono, plataformas, patrones visuales y mensajes del COMPETIDOR.\n"
            "2. Analiza cómo la marca del CLIENTE puede diferenciarse positivamente.\n"
            "3. Propón 3 ideas creativas para nuevos anuncios que:\n"
            "   - Respeten la paleta de colores del cliente\n"
            "   - Sean coherentes con su identidad de marca\n"
            "   - Ofrezcan una propuesta de valor superior a la competencia\n"
            "   - Incluyan una descripción visual detallada y un texto publicitario sugerido\n"
        )

        # Solo usamos texto e imágenes de URLs web (no base64)
        message_content = [{"type": "text", "text": prompt_text}]
        
        # Añadir URLs de competidores
        for url in competitor_image_urls:
            if url and url.startswith("http"):
                message_content.append({"type": "image_url", "image_url": {"url": url}})

        # Enviar y correr análisis
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_content
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        with st.spinner("🔄 Analizando anuncios y generando propuestas adaptadas a tu marca..."):
            while run.status != "completed":
                time.sleep(2)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        # Obtener respuesta de texto
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        full_text = messages.data[0].content[0].text.value

        # Extraer prompts creativos para imágenes usando regex más flexibles
        idea_prompts = []
        # Buscar patrones que podrían indicar ideas numeradas
        patterns = [
            r"\d+\.\s+(.*?)(?=\d+\.|$)",  # Formato: "1. Texto de idea"
            r"(?:Idea|Propuesta)\s+\d+[:.\s]+(.*?)(?=(?:Idea|Propuesta)\s+\d+|$)",  # Formato: "Idea 1: Texto"
            r"(?<=\n)[-•]\s+(.*?)(?=\n[-•]|\n\n|$)"  # Formato con viñetas: "- Texto" o "• Texto"
        ]
        
        for pattern in patterns:
            found_ideas = re.findall(pattern, full_text, re.DOTALL)
            if found_ideas:
                for idea in found_ideas:
                    clean_idea = idea.strip()
                    if len(clean_idea.split()) > 10:  # Asegurarse que sea suficientemente descriptiva
                        idea_prompts.append(clean_idea)
                # Si encontramos con un patrón, no seguir buscando
                break
                
        # Si no encontramos ideas con ningún patrón, tomar párrafos como ideas
        if not idea_prompts:
            paragraphs = re.split(r'\n\n+', full_text)
            for p in paragraphs:
                if len(p.split()) > 20:  # Párrafos suficientemente largos
                    idea_prompts.append(p.strip())
        
        # Limitar a máximo 3 ideas
        idea_prompts = idea_prompts[:3]
        
        # Mejorar prompts para DALL-E
        clean_prompts = []
        for i, prompt in enumerate(idea_prompts):
            # Añadir referencia a la marca y colores
            enhanced_prompt = f"Advertisement for {brand_name} brand using their color palette ({colors_text}): {prompt}"
            clean_prompts.append(enhanced_prompt)

        # Generar imágenes con DALL·E
        image_responses = []
        
        if clean_prompts:
            for i, prompt in enumerate(clean_prompts):
                with st.spinner(f"Generando imagen {i+1}..."):
                    try:
                        image = client.images.generate(
                            model="dall-e-3",
                            prompt=prompt,
                            n=1,
                            size="1024x1024"
                        )
                        image_url = image.data[0].url
                        image_responses.append({"prompt": prompt, "url": image_url})
                    except Exception as img_error:
                        st.error(f"Error generando imagen {i+1}: {str(img_error)}")

        # Devolver los resultados
        return {
            "insights_text": full_text,
            "creative_images": image_responses
        }

    except Exception as e:
        st.error(f"Error durante el análisis y generación de imágenes: {e}")
        return f"Error: {e}"


# Inicializar session_state si no existe
if 'advertisers' not in st.session_state:
    st.session_state.advertisers = []
if 'selected_advertiser' not in st.session_state:
    st.session_state.selected_advertiser = None
if 'df_ads' not in st.session_state:
    st.session_state.df_ads = None
if "selected_country" not in st.session_state:
    st.session_state.selected_country = list(COUNTRY_MAP.keys())[0]  # default = Argentina
if "brand_info" not in st.session_state:
    st.session_state.brand_info = {
        "brand_name": "",
        "brand_description": "",
        "brand_colors": [],
        "logo_path": None,
        "own_ads_paths": []
    }

# Streamlit UI - Parte de las pestañas
st.title("📢 Facebook Ads Analyzer")

# Definición simple de pestañas para evitar problemas
tab_brand, tab_search = st.tabs(["✨ Tu marca", "🎯 Búsqueda de anuncios"])

# Primera pestaña - Tu marca
with tab_brand:
    st.header("💼 Información de tu marca")
    st.markdown("Completa los datos de tu marca para obtener anuncios personalizados")
    
    # Brand Name
    brand_name = st.text_input(
        "Nombre de tu marca", 
        value=st.session_state.brand_info.get("brand_name", ""),
        key="brand_name_input"
    )
    
    # Brand Description
    brand_description = st.text_area(
    "Descripción de tu marca (productos, servicios, público objetivo, valores, etc.)",
        value=st.session_state.brand_info.get("brand_description", ""),
        height=150,
        key="brand_description_input"
    )
    
    # Logo Upload
    st.subheader("Logo de tu marca")
    logo_file = st.file_uploader("Sube el logo de tu marca", type=["jpg", "jpeg", "png"], key="logo_uploader")
    
    if logo_file is not None:
        logo_path = save_uploaded_file(logo_file, brand_dir, f"brand_logo.{logo_file.name.split('.')[-1]}")
        st.image(logo_path, width=150)
    else:
        logo_path = st.session_state.brand_info.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            logo_path = None
    
    # Color Palette
    st.subheader("Paleta de colores de tu marca")
    
    # Mostrar la paleta actual
    if st.session_state.brand_info.get("brand_colors"):
        st.markdown("#### Colores actuales:")
        cols = st.columns(len(st.session_state.brand_info["brand_colors"]))
        for i, (color_name, color_hex) in enumerate(st.session_state.brand_info["brand_colors"]):
            cols[i].markdown(
                f'<div style="display: flex; flex-direction: column; align-items: center;">'
                f'<div class="color-box" style="background-color: {color_hex};"></div>'
                f'<div style="font-size: 12px; margin-top: 5px;">{color_name}</div>'
                f'<div style="font-size: 10px;">{color_hex}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
    # Agregar nuevos colores
    with st.expander("Agregar un nuevo color a la paleta"):
        col1, col2 = st.columns(2)
        with col1:
            new_color_name = st.text_input("Nombre del color (ej. Principal, Secundario)", key="new_color_name")
        with col2:
            new_color_hex = st.color_picker("Selecciona el color", "#1E90FF")
        
        if st.button("Agregar color a la paleta", key="add_color_btn"):
            if new_color_name and new_color_hex:
                current_colors = st.session_state.brand_info.get("brand_colors", [])
                current_colors.append((new_color_name, new_color_hex))
                st.session_state.brand_info["brand_colors"] = current_colors
                st.rerun()
    
    # Botón para eliminar todos los colores
    if st.session_state.brand_info.get("brand_colors") and st.button("Eliminar todos los colores", key="clear_colors_btn"):
        st.session_state.brand_info["brand_colors"] = []
        st.rerun()
    
    # Upload Own Ads
    st.subheader("Tus anuncios actuales (opcional)")
    st.markdown("Sube ejemplos de tus anuncios actuales para mejorar las recomendaciones")
    
    own_ad_files = st.file_uploader(
        "Sube imágenes de tus anuncios actuales", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key="own_ads_uploader"
    )
    
    own_ads_paths = []
    if own_ad_files:
        for i, ad_file in enumerate(own_ad_files):
            ad_path = save_uploaded_file(
                ad_file, 
                brand_dir, 
                f"own_ad_{i}_{ad_file.name}"
            )
            own_ads_paths.append(ad_path)
        
        # Mostrar las imágenes subidas
        cols = st.columns(min(3, len(own_ads_paths)))
        for i, ad_path in enumerate(own_ads_paths[:3]):  # Mostrar máximo 3
            cols[i].image(ad_path, caption=f"Anuncio {i+1}", use_container_width=True)
    else:
        own_ads_paths = st.session_state.brand_info.get("own_ads_paths", [])
        if own_ads_paths:
            # Mostrar anuncios guardados anteriormente
            valid_paths = [p for p in own_ads_paths if os.path.exists(p)]
            if valid_paths:
                cols = st.columns(min(3, len(valid_paths)))
                for i, ad_path in enumerate(valid_paths[:3]):
                    cols[i].image(ad_path, caption=f"Anuncio {i+1}", use_container_width=True)
            else:
                own_ads_paths = []
    
    # Guardar toda la información de la marca
    if st.button("💾 Guardar información de marca", key="save_brand_btn"):
        st.session_state.brand_info = {
            "brand_name": brand_name,
            "brand_description": brand_description,
            "brand_colors": st.session_state.brand_info.get("brand_colors", []),
            "logo_path": logo_path,
            "own_ads_paths": own_ads_paths
        }
        st.success("✅ Información de marca guardada correctamente!")
        
        # Verificar si la información está completa
        if not (brand_name and brand_description and st.session_state.brand_info.get("brand_colors") and logo_path):
            st.warning("⚠️ Algunos campos están incompletos. Para obtener mejores resultados, completa todos los campos.")

# Definir la segunda pestaña - Búsqueda de anuncios
with tab_search:
    st.header("🔍 Buscar anuncios de la competencia")
    st.markdown("Busca y analiza anuncios de tus competidores para generar insights comparativos")
    
    # Selección de país
    selected_country = st.selectbox(
        "Select a country",
        list(COUNTRY_MAP.keys()),
        index=list(COUNTRY_MAP.keys()).index(st.session_state.selected_country),
        key="select_country_input"
    )
    if selected_country != st.session_state.selected_country:
        st.session_state.selected_country = selected_country

    # Usar siempre el valor del session_state
    country_code = COUNTRY_MAP[st.session_state.selected_country]

    # Input para nombre del advertiser
    advertiser_name = st.text_input("Enter the advertiser's name", "", key="advertiser_name_input")

    # Botón para buscar advertisers
    if st.button("Search advertiser", key="search_advertiser_btn"):
        with st.spinner("🔄 Searching for advertisers..."):
            try:
                advertisers = get_advertiser_suggestions(country_code, advertiser_name)

                if not advertisers or (isinstance(advertisers, list) and len(advertisers) == 1 and isinstance(advertisers[0], str) and advertisers[0].startswith("Error")):
                    st.error("🚫 No advertisers found. Try another keyword.")
                    st.stop()

                st.session_state.advertisers = advertisers
                st.session_state.selected_advertiser = None
                st.session_state.df_ads = None
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error while searching advertisers: {str(e)}")
                st.stop()

    # Mostrar dropdown si hay advertisers encontrados
    if st.session_state.advertisers:
        advertiser_names = ["Select the desired advertiser..."] + [ad["name"] for ad in st.session_state.advertisers]

        selected_name = st.selectbox(
            "Select the desired advertiser",
            advertiser_names,
            index=0,
            key="advertiser_dropdown"
        )

        if selected_name != "Select the desired advertiser...":
            selected_advertiser = next(
                (ad for ad in st.session_state.advertisers if ad["name"] == selected_name),
                None
            )

            if selected_advertiser and (
                st.session_state.selected_advertiser is None
                or selected_advertiser["name"] != st.session_state.selected_advertiser["name"]
            ):
                st.session_state.selected_advertiser = selected_advertiser
                st.session_state.df_ads = None
                st.rerun()


    # Mostrar detalle del advertiser seleccionado
    if st.session_state.selected_advertiser:
        st.image(st.session_state.selected_advertiser["logo"], width=80)

        # Mostrar botón para buscar anuncios
        if st.button("Search ads", key="search_ads_btn"):
            with st.spinner(f"🔎 Extracting ads from {st.session_state.selected_advertiser['name']}..."):
                try:
                    st.session_state.df_ads = extract_ads(country_code, st.session_state.selected_advertiser)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error while extracting ads: {str(e)}")
                    st.stop()

    # Mostrar resultados si hay anuncios extraídos
    if st.session_state.df_ads is not None and not st.session_state.df_ads.empty:
        df_ads = st.session_state.df_ads

        if "Start Date" in df_ads.columns:
            df_ads["Start Date"] = pd.to_datetime(df_ads["Start Date"], errors='coerce')

        df_ads.to_excel('df_ads.xlsx', index=False)
        st.success("✅ Ads extracted successfully!")

        if len(df_ads) > 0 and "Start Date" in df_ads.columns and "Image Path" in df_ads.columns:
            df_top_ads = df_ads.sort_values("Start Date").head(min(5, len(df_ads)))
            st.subheader("🏆 Top Performing Ads")
            columns = st.columns(min(5, len(df_top_ads)))
            for col, (_, row) in zip(columns, df_top_ads.iterrows()):
                if row["Image Path"] != "No Image" and os.path.exists(row["Image Path"]):
                    col.image(row["Image Path"], caption=row["Ad ID"], use_container_width=True)

        # Verificar que la información de marca esté completa antes de generar insights
        brand_info = st.session_state.brand_info
        brand_info_complete = (
            brand_info.get("brand_name") and 
            brand_info.get("brand_description") and 
            brand_info.get("brand_colors") and 
            brand_info.get("logo_path")
        )
        
        # Mostrar opciones de OpenAI insights
        if "OPENAI_API_KEY" in st.secrets and "ASSISTANT_ID" in st.secrets:
            OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
            ASSISTANT_ID = st.secrets["ASSISTANT_ID"]

            if not brand_info_complete:
                st.warning("⚠️ Para generar insights personalizados, completa la información de tu marca en la pestaña 'Tu marca'.")
            
            # Modificar esta parte para evitar el error de clave duplicada
            generate_insights = st.button(
                "💡 Generate Insights", 
                key=f"generate_insights_btn_{hash(str(st.session_state.df_ads.shape))}", 
                disabled=not brand_info_complete
            )
            
            if generate_insights:
                output_placeholder = st.empty()
                output_placeholder.info("Generating insights based on your brand and competitor ads, please wait...")
                
                insights = get_openai_insights_and_images(df_ads, st.session_state.brand_info, OPENAI_API_KEY, ASSISTANT_ID)
                
                # Mostrar los insights generados de manera simple, como texto plano
                if isinstance(insights, dict) and "insights_text" in insights:
                    output_placeholder.empty()  # Limpiamos el placeholder anterior
                    output_placeholder.markdown("### 📊 Análisis de Anuncios")
                    output_placeholder.info(insights["insights_text"])  # Usar st.info para obtener un formato similar a tu ejemplo
                    
                    # Mostrar las imágenes generadas si existen
                    if "creative_images" in insights and insights["creative_images"]:
                        st.markdown("### 🖼️ Propuestas Creativas")
                        
                        # Crear una columna para cada imagen generada
                        image_cols = st.columns(len(insights["creative_images"]))
                        
                        for i, img_data in enumerate(insights["creative_images"]):
                            with image_cols[i]:
                                # Mostrar la imagen
                                st.image(img_data["url"], caption=f"Propuesta {i+1}", use_container_width=True)
                                
                                # Mostrar descripción en un expander simple
                                with st.expander(f"Ver descripción completa"):
                                    st.write(img_data["prompt"])
                else:
                    output_placeholder.error("No se pudieron generar insights. Por favor, intenta nuevamente.")
        else:
            st.warning("To generate insights, configure the API keys in Streamlit secrets.")