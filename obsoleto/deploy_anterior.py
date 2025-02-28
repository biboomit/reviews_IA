import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from functions import login, render_kpi, fetch_app_data, fetch_reviews, get_openai_insights, fetch_ios_reviews
from google_play_scraper import app, reviews, search
import plotly.graph_objects as go
import plotly.express as px
from wordcloud import WordCloud
import base64
import requests
import numpy as np
from app_store_scraper import AppStore  # Asegúrate de tener instalada esta librería

# Cargar estilos CSS
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Configurar la página
st.set_page_config(page_title="Boomit - Social Intelligence", layout="wide")

# Cargar CSS
load_css()

# Verificar autenticación
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# Mostrar mensaje de bienvenida
if st.session_state.get("show_welcome", False):
    st.success(f"✅ Bienvenido, {st.session_state['username']}")

# Cargar stopwords desde un archivo externo
with open("stopwords.txt", "r", encoding="utf-8") as f:
    custom_stopwords = set(word.strip() for word in f.readlines())

# Cargar imagen del logo
logo_path = "company_logo.png"
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 17px;">
        <img src="data:image/png;base64,{base64.b64encode(open(logo_path, 'rb').read()).decode()}" width="120">
        <h1 style="margin: 5;">Boomit - Social Intelligence</h1>
    </div>
""", unsafe_allow_html=True)

# Selección del país y app
country_mapping = {
    "Argentina": "ar",
    "Chile": "cl",
    "Colombia": "co",
    "Ecuador": "ec",
    "El Salvador": "sv",
    "Estados Unidos": "us",
    "Guatemala": "gt",
    "Honduras": "hn",
    "México": "mx",
    "Nicaragua": "ni",
    "Panamá": "pa",
    "Paraguay": "py",
    "Perú": "pe"
}
col1, col2, col3 = st.columns([2, 2, 1])  # Tres columnas, la última más angosta para el logo
with col1:
    selected_country = st.selectbox("🌍 Seleccione el país de la tienda:", list(country_mapping.keys()), key="selected_country")
with col2:
    app_name = st.text_input("🔎 Ingrese el nombre de la aplicación:", key="app_name")

# Ocultar mensaje de bienvenida si se selecciona un país y una app
if selected_country and app_name:
    if st.session_state.get("show_welcome", False):
        st.session_state["show_welcome"] = False
        st.rerun()

    country = country_mapping[selected_country]
    app_id, app_data = fetch_app_data(app_name, country)

    if app_id and app_data:
        app_logo = app_data.get("icon", None)
        st.session_state["app_logo"] = app_logo  # Guardar el logo en la sesión
        downloads = app_data.get("installs", "No disponible")
        timestamp = app_data.get("updated", None)
        last_release_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if isinstance(timestamp, int) else "No disponible"

        # Obtener reseñas de Android
        df_reviews_android = fetch_reviews(app_id, country)
        df_reviews_android["source"] = "Android"

        # Obtener el app_id de iOS usando la API de iTunes Search
        ios_app_id = None
        url = f"https://itunes.apple.com/search?term={app_name}&country=us&entity=software"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["resultCount"] > 0:
                ios_app_id = data["results"][0]["trackId"]  # Obtener el App ID de iOS
                print(f"App ID de iOS para '{app_name}': {ios_app_id}")

        # Obtener reseñas de iOS si se encontró el app_id
        df_reviews_ios = pd.DataFrame()
        if ios_app_id:
            df_reviews_ios = fetch_ios_reviews(app_name, ios_app_id)

        # Combinar reseñas de Android e iOS
        if not df_reviews_ios.empty:
            df_reviews = pd.concat([df_reviews_android, df_reviews_ios], ignore_index=True)
        else:
            df_reviews = df_reviews_android

        # Guardar el DataFrame combinado en la sesión
        st.session_state["df_reviews"] = df_reviews
        st.session_state["last_app_id"] = app_id

        # Filtro de fuente de datos (Android, iOS o ambas)
        source_filter = st.radio("Seleccione la fuente de datos:", ["Ambas", "Android", "iOS"], index=0, horizontal=True)

        # Aplicar el filtro de fuente de datos
        if source_filter == "Android":
            df_reviews = df_reviews[df_reviews["source"] == "Android"]
        elif source_filter == "iOS":
            df_reviews = df_reviews[df_reviews["source"] == "iOS"]

        # Filtro de fechas (solo para ajustes manuales)
        col1, col2, col3 = st.columns([2, 2, 1])  # Agregar una tercera columna para el logo
        with col1:
            start_date = st.date_input("📅 Desde:", value=df_reviews["at"].min().date())
        with col2:
            end_date = st.date_input("📅 Hasta:", value=df_reviews["at"].max().date())
        with col3:
            if st.session_state.get("app_logo"):
                st.image(st.session_state["app_logo"], width=80)  # Mostrar el logo

        # Aplicar el filtro de fechas manual
        df_filtered = df_reviews.copy()  # Copiar siempre los datos originales
        df_filtered = df_filtered[(df_filtered["at"] >= pd.to_datetime(start_date)) & 
                                (df_filtered["at"] <= pd.to_datetime(end_date))]

        # Gráfico de evolución
        st.markdown("---")
        st.markdown("### 📊 Selecciona el nivel de agregación:")
        agg_option = st.radio("", ["Diario", "Semanal", "Mensual", "Anual"], index=1, horizontal=True)

        if agg_option == "Diario":
            df_filtered["date"] = pd.to_datetime(df_filtered["at"]).dt.date  # Convertir a date
            grouped_counts = df_filtered.groupby("date").size().reset_index(name="Cantidad de Reseñas")
            grouped_avg_score = df_filtered.groupby("date")["score"].mean().reset_index(name="Calificación Promedio")

            # Convertir las fechas a datetime nuevamente para asegurar el formato
            grouped_counts['date'] = pd.to_datetime(grouped_counts['date'])
            grouped_avg_score['date'] = pd.to_datetime(grouped_avg_score['date'])

        elif agg_option == "Semanal":
            df_filtered["date"] = df_filtered["at"].dt.to_period("W").apply(lambda r: r.start_time)
        elif agg_option == "Mensual":
            df_filtered["date"] = df_filtered["at"].dt.to_period("M").apply(lambda r: r.start_time)
        elif agg_option == "Anual":
            df_filtered["date"] = df_filtered["at"].dt.to_period("Y").apply(lambda r: r.start_time)

        df_filtered["date"] = pd.to_datetime(df_filtered["date"], errors='coerce')
        grouped_counts = df_filtered.groupby("date").size().reset_index(name="Cantidad de Reseñas")
        grouped_avg_score = df_filtered.groupby("date")["score"].mean().reset_index(name="Calificación Promedio")

        # Crear el gráfico de evolución
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=grouped_counts['date'], y=grouped_counts['Cantidad de Reseñas'], name='Cantidad de Reseñas',
            marker=dict(color='red'), opacity=0.7, yaxis='y1',
            text=grouped_counts['Cantidad de Reseñas'], textposition='outside'
        ))
        fig1.add_trace(go.Scatter(
            x=grouped_avg_score['date'], y=grouped_avg_score['Calificación Promedio'], mode='lines+markers+text',
            name='Calificación Promedio', line=dict(color='blue', width=2), yaxis='y2',
            text=grouped_avg_score['Calificación Promedio'].round(2), textposition='top center'
        ))
        fig1.update_layout(
            title="📈 Evolución de reseñas", xaxis=dict(title="Fecha", tickangle=-45),
            yaxis=dict(title="Cantidad de Reseñas", side='left'),
            yaxis2=dict(title="Calificación Promedio", overlaying='y', side='right'),
            legend=dict(x=0, y=1.1, orientation="h"), barmode="group"
        )

        if agg_option == "Diario":
            fig1.update_xaxes(
                tickformat="%d-%m",  # Formato de día y mes
                tickangle=-45,  # Ángulo para mejorar la legibilidad
                nticks=min(20, len(grouped_counts)))  # Limitar el número de etiquetas
        elif agg_option == "Anual":
            fig1.update_xaxes(tickformat="%Y")

        # Mostrar el gráfico
        st.plotly_chart(fig1, use_container_width=True)

        # Gráficos adicionales (distribución de calificaciones y nube de palabras)
        col1, col2 = st.columns(2)
        df_reviews['score_label'] = df_reviews['score'].apply(lambda x: f'{int(x)}⭐')
        with col1:
            st.markdown("### 📊 Distribución de Calificaciones")
            df_filtered['score_label'] = df_filtered['score'].apply(lambda x: f'{int(x)}⭐')
            fig_hist = px.histogram(df_filtered, x='score_label', nbins=5, title="", text_auto=True)
            fig_hist.update_layout(height=400, bargap=0.1, xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            st.markdown("### ☁️ Nube de Palabras en Reseñas")
            text = " ".join(str(review) for review in df_filtered["content"].dropna())
            if text.strip():  # Verificar si hay texto disponible
                wordcloud = WordCloud(width=800, height=450, background_color='white', stopwords=custom_stopwords).generate(text)
                st.image(wordcloud.to_array(), use_container_width=True)
            else:
                st.warning("No hay suficiente texto para generar la nube de palabras.")

        # Análisis de OpenAI
        if not df_reviews.empty:
            st.markdown("---")
            st.markdown("### 🤖 Análisis de Boomit One AI sobre las Reseñas")
            if "content" in df_reviews.columns:
                filtered_reviews = df_reviews[(df_reviews["at"] >= pd.to_datetime(start_date)) & 
                                        (df_reviews["at"] <= pd.to_datetime(end_date))]
                date_range_text = f"Las siguientes reviews corresponden al período desde {start_date} hasta {end_date}.\n\n"
                comments_text = date_range_text + "\n".join(filtered_reviews["content"].dropna().head(50).tolist()).strip()
                if comments_text:
                    if st.button("Comenzar análisis"):
                        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
                        ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
                        insights = get_openai_insights(comments_text, OPENAI_API_KEY, ASSISTANT_ID)
                        st.markdown("#### 🔍 Insights Generados")
                        st.info(insights)
                else:
                    st.warning("No hay suficientes comentarios para generar insights.")