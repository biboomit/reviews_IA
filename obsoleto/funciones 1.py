import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from wordcloud import WordCloud
from google_play_scraper import app, reviews, search
import time
import requests
from datetime import datetime, timedelta
import openai
from bs4 import BeautifulSoup
import base64
from app_store_scraper.app_store import AppStore 

# Cargar estilos CSS desde el archivo externo
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



        
def login(t):
    """Función para manejar el inicio de sesión con traducción."""
    st.title(f"🔐 {t('login_title')}")
    username = st.text_input(t('email'), key="user_input")
    password = st.text_input(t('password'), type="password", key="pass_input", help=t('password_help'))
    login_button = st.button(t('login_button'))

    if login_button:
        if username in st.secrets["users"] and st.secrets["users"][username] == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["show_welcome"] = True
            st.success(t('login_success'))
            time.sleep(1.5)
            st.rerun()
        else:
            st.error(t('login_error'))



def render_kpi(title, value):
    """Genera una tarjeta KPI con efecto hover dinámico."""
    return f"""
    <div class="kpi-box">
        <p class="kpi-title">{title}</p>
        <span class="kpi-value">{value}</span>
    </div>
    """


def fetch_app_data(app_name, country):
    """Obtener datos de la aplicación desde Google Play Store."""
    search_results = search(app_name, lang="es", country=country)
    if search_results:
        app_id = search_results[0]['appId']
        app_data = app(app_id, lang='es', country=country)
        return app_id, app_data
    else:
        st.error(t('no_app_found'))  # Usar la función t() para el mensaje de error
        return None, None


def get_openai_insights(comments_text, OPENAI_API_KEY, ASSISTANT_ID, t):
    """Generar insights usando OpenAI."""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"{t('openai_instruction')}\n\n{comments_text}"

        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        with st.spinner(t('generating_insights')):
            while run.status != "completed":
                time.sleep(2)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value
        return response_text
    except Exception as e:
        return f"Error al obtener insights de OpenAI: {e}"




def fetch_all_reviews(app_id_android, country_android, app_name_ios, days=45, t=None):

    """
    Obtener y combinar reseñas de Android e iOS en un único DataFrame.

    Parámetros:
        app_id_android (str): ID de la aplicación en Google Play Store.
        country_android (str): Código de país para Google Play Store.
        app_name_ios (str): Nombre de la aplicación en la App Store.
        days (int): Número de días hacia atrás para obtener reseñas (por defecto 60).

    Retorna:
        pd.DataFrame: DataFrame combinado con las reseñas de ambas plataformas.
    """
    def get_ios_app_id(app_name, country):
        try:
            url = f"https://itunes.apple.com/search?term={app_name}&country={country}&entity=software"
            response = requests.get(url)
            response.raise_for_status()  # Lanza una excepción si el código de estado no es 200
            data = response.json()
            if data["resultCount"] > 0:
                return data["results"][0]["trackId"]
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Error al obtener el ID de iOS: {e}")
            return None
        except Exception as e:
            st.error(f"⚠️ Error inesperado al obtener el ID de iOS: {e}")
            return None

    def fetch_android_reviews(app_id, country, days):
        all_reviews = []
        continuation_token = None
        max_iterations = 10
        date_limit = datetime.today() - timedelta(days=days)

        for _ in range(max_iterations):
            try:
                result, continuation_token = reviews(app_id, lang='es', country=country, count=200, continuation_token=continuation_token)
                for review in result:
                    review_date = pd.to_datetime(review["at"])
                    if review_date >= date_limit:
                        all_reviews.append(review)
                    else:
                        continuation_token = None
                        break
                if not continuation_token:
                    break
                time.sleep(2)  # Evitar rate limiting
            except Exception as e:
                st.error(f"⚠️ Error al obtener reseñas de Android: {e}")
                break

        if not all_reviews:
            return pd.DataFrame()

        df_reviews_android = pd.DataFrame(all_reviews)
        if not {"at", "content", "score"}.issubset(df_reviews_android.columns):
            return pd.DataFrame()

        df_reviews_android = df_reviews_android[["at", "content", "score"]].copy()
        df_reviews_android["at"] = pd.to_datetime(df_reviews_android["at"]).dt.date
        df_reviews_android["source"] = "Android"

        return df_reviews_android

    def fetch_ios_reviews(app_name, country, days, ios_app_id):
        try:
            fecha_inicio = datetime.now() - timedelta(days=days)
            fecha_inicio = datetime(fecha_inicio.year, fecha_inicio.month, fecha_inicio.day, 0, 0, 0)

            app_ios = AppStore(country=country, app_name=app_name, app_id=ios_app_id)
            total_reviews = 0
            max_attempts = 5

            for attempt in range(max_attempts):
                app_ios.review(how_many=400, after=fecha_inicio, sleep=0.7)
                current_total = len(app_ios.reviews)
                if current_total == total_reviews:
                    break
                total_reviews = current_total

            if not app_ios.reviews:
                return pd.DataFrame()

            # Crear DataFrame correctamente desde la lista de reseñas
            df_reviews_ios = pd.DataFrame(app_ios.reviews)
            
            # Renombrar las columnas para que coincidan con las demás
            if not df_reviews_ios.empty:
                df_reviews_ios = df_reviews_ios.rename(columns={"date": "at", "review": "content", "rating": "score"})
                df_reviews_ios["at"] = pd.to_datetime(df_reviews_ios["at"]).dt.date
                df_reviews_ios["source"] = "iOS"
            else:
                df_reviews_ios = pd.DataFrame()

            return df_reviews_ios

        except Exception as e:
            st.error(f"⚠️ Error al obtener reseñas de iOS: {e}")
            return pd.DataFrame()

    # Obtener reseñas de Android
    df_reviews_android = fetch_android_reviews(app_id_android, country_android, days)
    android_reviews_count = len(df_reviews_android)

    # Obtener el ID de iOS
    ios_app_id = get_ios_app_id(app_name_ios, country_android)
    df_reviews_ios = pd.DataFrame()
    ios_reviews_count = 0

    if ios_app_id:
        df_reviews_ios = fetch_ios_reviews(app_name_ios, country_android, days, ios_app_id)
        ios_reviews_count = len(df_reviews_ios)

    # Concatenar los resultados
    df_reviews = pd.concat([df_reviews_android, df_reviews_ios], ignore_index=True)

    # Obtener el logo de la aplicación de Android
    app_logo = None
    try:
        app_data = app(app_id_android, lang='es', country=country_android)
        app_logo = app_data.get("icon", None)
    except Exception as e:
        st.error(f"⚠️ Error al obtener el logo de la aplicación: {e}")
    

        # Mensajes traducidos
    android_message = t('app_found_android').format(
        app_name=app_name_ios, 
        app_id=app_id_android, 
        country=country_android, 
        count=android_reviews_count
    )
    
    ios_message = t('app_found_ios').format(
        app_name=app_name_ios,
        app_id=ios_app_id if ios_app_id else t('app_not_found_ios'),
        country=country_android,
        count=ios_reviews_count
    )

    # Mostrar mensaje final
    st.markdown(
        f"""
        <div style="background-color: #228B22; color: white; padding: 20px; border-radius: 10px; text-align: left; width: 100%; display: flex;">
            <div style="flex: 4;">
                {android_message} <br>
                {ios_message}
            </div>
            <div style="flex: 1; text-align: center;">
                <img src="{app_logo}" alt="App Logo" style="max-width: 100px; max-height: 70px;">
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    return df_reviews

    

def render_dynamic_kpis(df_filtered):
    """Renderiza KPIs dinámicos para calificaciones y cantidad de reseñas por fuente en 6 columnas."""
    # Calcular KPIs generales
    avg_score_total = df_filtered['score'].mean() if not df_filtered.empty else 0
    total_reviews = len(df_filtered)

    # Calcular KPIs por fuente
    avg_score_android = df_filtered[df_filtered['source'] == 'Android']['score'].mean() if not df_filtered.empty else 0
    total_reviews_android = len(df_filtered[df_filtered['source'] == 'Android'])

    avg_score_ios = df_filtered[df_filtered['source'] == 'iOS']['score'].mean() if not df_filtered.empty else 0
    total_reviews_ios = len(df_filtered[df_filtered['source'] == 'iOS'])

    # Formatear para evitar NaN
    avg_score_total = round(avg_score_total, 2) if not pd.isna(avg_score_total) else 0
    avg_score_android = round(avg_score_android, 2) if not pd.isna(avg_score_android) else 0
    avg_score_ios = round(avg_score_ios, 2) if not pd.isna(avg_score_ios) else 0

    # Renderizar KPIs en una fila de 6 columnas
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(render_kpi("⭐ Score Gral", f"{avg_score_total:.2f}"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_kpi("💬 Total Reseñas", f"{total_reviews:,}"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_kpi("⭐ Score And", f"{avg_score_android:.2f}"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_kpi("💬 Reseñas And", f"{total_reviews_android:,}"), unsafe_allow_html=True)
    with col5:
        st.markdown(render_kpi("⭐ Score IOS", f"{avg_score_ios:.2f}"), unsafe_allow_html=True)
    with col6:
        st.markdown(render_kpi("💬 Reseñas IOS", f"{total_reviews_ios:,}"), unsafe_allow_html=True)