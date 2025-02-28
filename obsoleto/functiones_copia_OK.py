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
from app_store_scraper import AppStore  # Asegúrate de instalar esta librería: pip install app-store-scraper

# Cargar estilos CSS desde el archivo externo
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
def login():
    """Función para manejar el inicio de sesión."""
    st.title("🔐 Iniciar sesión")
    username = st.text_input("Correo electrónico", key="user_input")
    password = st.text_input("Contraseña", type="password", key="pass_input", help="Ingrese su contraseña")
    login_button = st.button("Ingresar")

    if login_button:
        if username in st.secrets["users"] and st.secrets["users"][username] == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["show_welcome"] = True
            st.rerun()
        else:
            st.error("❌ Correo o contraseña incorrectos")

def render_kpi(title, value):
    """Función para renderizar los KPIs con formato."""
    return f"""
        <div class="kpi-box">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """

def fetch_app_data(app_name, country):
    """Obtener datos de la aplicación desde Google Play Store."""
    search_results = search(app_name, lang="es", country=country)
    if search_results:
        app_id = search_results[0]['appId']
        
        # Crear dos columnas y mostrar el mensaje en la primera
        app_data = app(app_id, lang='es', country=country)
                # Obtener número de descargas (instalaciones)
        return app_id, app_data  # Devuelve tanto el ID como los datos de la aplicación como las decargas
    else:
        st.error("❌ No se encontró la aplicación en Google Play Store.")
        return None, None


def get_openai_insights(comments_text, OPENAI_API_KEY, ASSISTANT_ID):
    """Generar insights usando OpenAI."""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=comments_text
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        with st.spinner("🔄 Generando insights, por favor espera..."):
            while run.status != "completed":
                time.sleep(2)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value
        return response_text
    except Exception as e:
        return f"Error al obtener insights de OpenAI: {e}"




def fetch_all_reviews(app_id_android, country_android, app_name_ios, days=45):
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

    # Función interna para obtener el ID de la aplicación iOS
    def get_ios_app_id(app_name, country):
        try:
            url = f"https://itunes.apple.com/search?term={app_name}&country={country}&entity=software"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data["resultCount"] > 0:
                    ios_app_id = data["results"][0]["trackId"]
                    return ios_app_id
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    # Función interna para obtener reseñas de Android
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
                time.sleep(2)
            except Exception:
                break

        df_reviews_android = pd.DataFrame(all_reviews)
        if df_reviews_android.empty or not {"at", "content", "score"}.issubset(df_reviews_android.columns):
            return pd.DataFrame()

        df_reviews_android = df_reviews_android[["at", "content", "score"]].copy()
        df_reviews_android["at"] = pd.to_datetime(df_reviews_android["at"]).dt.date
        df_reviews_android["source"] = "Android"

        return df_reviews_android

    # Obtener reseñas de Android primero
    df_reviews_android = fetch_android_reviews(app_id_android, country_android, days)
    android_reviews_count = len(df_reviews_android)

    # Obtener el ID de iOS
    ios_app_id = get_ios_app_id(app_name_ios, country_android)
    if ios_app_id is None:
        ios_reviews_count = 0
    else:
        # Función interna para obtener reseñas de iOS
        def fetch_ios_reviews(app_name, country, days, ios_app_id):
            """
            Obtiene reseñas de iOS con control de bucle infinito basado en el incremento total.
            """
            try:
                fecha_inicio = datetime.now() - timedelta(days=days)
                fecha_inicio = datetime(fecha_inicio.year, fecha_inicio.month, fecha_inicio.day, 0, 0, 0)

                app_ios = AppStore(country=country, app_name=app_name, app_id=ios_app_id)

                total_reviews = 0
                max_attempts = 5

                for attempt in range(max_attempts):
                    app_ios.review(how_many=500, after=fecha_inicio, sleep=0.4)
                    current_total = len(app_ios.reviews)


                    # Si no hubo incremento desde el último intento, salir
                    if current_total == total_reviews:
                        break
                    total_reviews = current_total

                # Convertir las reseñas a DataFrame
                reviews_df = pd.DataFrame(app_ios.reviews)
                if reviews_df.empty:
                    return pd.DataFrame()

                # Formatear el DataFrame
                df_reviews_ios = pd.DataFrame({
                    "at": pd.to_datetime(reviews_df["date"]).dt.date,
                    "content": reviews_df["review"],
                    "score": reviews_df["rating"],
                    "source": "iOS"
                })

                return df_reviews_ios

            except Exception as e:
                st.error(f"⚠️ Error al obtener reseñas de iOS: {e}")
                return pd.DataFrame()

        df_reviews_ios = fetch_ios_reviews(app_name_ios, country_android, days, ios_app_id)
        ios_reviews_count = len(df_reviews_ios)

    # Concatenar los resultados
    df_reviews = pd.concat([df_reviews_android, df_reviews_ios], ignore_index=True)

    # Obtener el logo de la aplicación de Android
    app_logo = None
    try:
        app_data = app(app_id_android, lang='es', country=country_android)
        app_logo = app_data.get("icon", None)
    except Exception:
        pass

    # Mostrar mensaje final combinado en un único rectángulo verde que ocupe toda la anchura
    st.markdown(
        f"""
        <div style="background-color: #228B22; color: white; padding: 20px; border-radius: 10px; text-align: left; width: 100%; display: flex;">
            <div style="flex: 4;">
                ✅ App encontrada Android: {app_name_ios} (ID: {app_id_android}) en {country_android} | Reseñas descargadas: {android_reviews_count} <br>
                ✅ App encontrada iOS: {app_name_ios} (ID: {ios_app_id if ios_app_id else 'No encontrado'}) en {country_android} | Reseñas descargadas: {ios_reviews_count}
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
        st.markdown(render_kpi("💬  Reseñas IOS", f"{total_reviews_ios:,}"), unsafe_allow_html=True)
