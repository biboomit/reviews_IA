import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from funciones import login, fetch_app_data, fetch_all_reviews  # Simplificado
import plotly.graph_objects as go
import base64
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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
    "Argentina": "ar", "Chile": "cl", "Colombia": "co", "Ecuador": "ec",
    "El Salvador": "sv", "Estados Unidos": "us", "Guatemala": "gt", "Honduras": "hn",
    "México": "mx", "Nicaragua": "ni", "Panamá": "pa", "Paraguay": "py", "Perú": "pe"
}
col1, col2 = st.columns([2, 2])
with col1:
    selected_country = st.selectbox("🌍 Seleccione el país de la tienda:", list(country_mapping.keys()), key="selected_country")
with col2:
    app_name = st.text_input("🔎 Ingrese el nombre de la aplicación:", key="app_name")

# Obtener y almacenar reseñas solo si cambia el app_name o el país
country = country_mapping.get(selected_country)
if app_name and country:
    if (
        "last_app_name" not in st.session_state or
        "last_country" not in st.session_state or
        st.session_state["last_app_name"] != app_name or
        st.session_state["last_country"] != country
    ):
        app_id_android, app_data = fetch_app_data(app_name, country)
        if app_id_android and app_data:
            with st.spinner("⏳ Descargando reseñas..."):
                df_reviews = fetch_all_reviews(app_id_android, country, app_name, days=60)
            st.session_state["df_reviews"] = df_reviews
            st.session_state["last_app_name"] = app_name
            st.session_state["last_country"] = country
        else:
            st.error("❌ No se encontró la aplicación.")
            st.stop()
    else:
        df_reviews = st.session_state.get("df_reviews", pd.DataFrame())

    if not df_reviews.empty:
        source_filter = st.radio("Seleccione la fuente de datos:", ["Ambas", "Android", "iOS"], index=0, horizontal=True)

        # Filtrar por fuente dinámicamente
        if source_filter != "Ambas":
            df_filtered = df_reviews[df_reviews["source"] == source_filter]
        else:
            df_filtered = df_reviews.copy()

        if not df_filtered.empty:
            # Filtros de fecha dinámicos
            min_date, max_date = df_filtered["at"].min(), df_filtered["at"].max()
            
            # Validar que las fechas son válidas
            if pd.isna(min_date) or pd.isna(max_date):
                st.warning("⚠️ No hay reseñas disponibles para las fechas seleccionadas o para la fuente elegida.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("📅 Desde:", value=min_date, min_value=min_date, max_value=max_date, key="start_date")
                with col2:
                    end_date = st.date_input("📅 Hasta:", value=max_date, min_value=min_date, max_value=max_date, key="end_date")

                # Aplicar filtro sin recargar todo
                df_filtered = df_filtered[(df_filtered["at"] >= start_date) & (df_filtered["at"] <= end_date)]

                # Actualizar las métricas en las tarjetas
                st.markdown("---")
                st.markdown(
                    """
                    <div class="kpi-box">
                        <div class="kpi-title">📊 Métricas de la Aplicación</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                st.markdown("")
                st.markdown("")
                # Renderizar KPIs dinámicos con 6 columnas
                from funciones import render_dynamic_kpis
                render_dynamic_kpis(df_filtered)
                st.markdown("---")

                # Agregación dinámica
                agg_option = st.radio("### 📊 Selecciona el nivel de agregación:", ["Diario", "Semanal", "Mensual", "Anual"], index=1, horizontal=True)

                if agg_option == "Diario":
                    df_filtered["date"] = df_filtered["at"]
                elif agg_option == "Semanal":
                    df_filtered["date"] = df_filtered["at"].apply(lambda x: x - timedelta(days=x.weekday()))
                elif agg_option == "Mensual":
                    df_filtered["date"] = df_filtered["at"].apply(lambda x: x.replace(day=1))
                elif agg_option == "Anual":
                    df_filtered["date"] = df_filtered["at"].apply(lambda x: x.replace(month=1, day=1))

                grouped_counts = df_filtered.groupby("date").size().reset_index(name="Cantidad de Reseñas")
                grouped_avg_score = df_filtered.groupby("date")["score"].mean().reset_index(name="Calificación Promedio")

                # Generar gráfico dinámico sin recargar todo
                fig = go.Figure()

                # Agregar barras con etiquetas enteras
                fig.add_trace(go.Bar(
                    x=grouped_counts['date'], 
                    y=grouped_counts['Cantidad de Reseñas'], 
                    name='Cantidad de Reseñas', 
                    marker=dict(color='red'),
                    text=grouped_counts['Cantidad de Reseñas'].apply(lambda x: f"{int(x)}"),  # Valores enteros
                    textposition='outside'
                ))

                # Agregar línea con etiquetas decimales con 1 decimal
                fig.add_trace(go.Scatter(
                    x=grouped_avg_score['date'], 
                    y=grouped_avg_score['Calificación Promedio'], 
                    mode='lines+markers+text', 
                    name='Calificación Promedio', 
                    line=dict(color='blue'),
                    text=grouped_avg_score['Calificación Promedio'].apply(lambda x: f"{x:.1f}"),  # Decimal con 1 decimal
                    textposition='top center'
                ))

                fig.update_layout(
                    title="📈 Evolución de Score y reseñas", 
                    xaxis_title="Fecha", 
                    yaxis_title="Cantidad de Reseñas", 
                    yaxis=dict(tickformat=',d'),  # Formato entero para el eje Y principal
                    margin=dict(l=40, r=40, t=60, b=40)
                )

                st.plotly_chart(fig, use_container_width=True)

                # **Histograma y Nube de Palabras**
                if not df_filtered.empty:
                    col1, col2 = st.columns(2)

                    # Agregar columna para etiquetas de puntajes (estrellas)
                    df_filtered['score_label'] = df_filtered['score'].apply(lambda x: f'{int(x)}⭐')

                    with col1:
                        st.markdown("### 📊 Distribución de Calificaciones")
                        # Crear histograma con etiquetas
                        fig_hist = px.histogram(df_filtered, x='score_label', nbins=5, title="Distribución de Calificaciones", text_auto=True)

                        # Ajustar el diseño
                        fig_hist.update_layout(
                            height=410,
                            bargap=0.1,
                            xaxis_title="Calificación",
                            yaxis_title="Cantidad",
                            margin=dict(l=40, r=40, t=60, b=40)
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)

                    with col2:
                        st.markdown("### ☁️ Nube de Palabras en Reseñas")

                        # Generar texto concatenando las reseñas
                        text = " ".join(str(review) for review in df_filtered["content"].dropna())

                        # Cargar stopwords desde el archivo stopwords.txt
                        stopwords = set()
                        try:
                            with open("stopwords.txt", "r", encoding="utf-8") as f:
                                stopwords = set(line.strip() for line in f if line.strip())
                        except FileNotFoundError:
                            st.warning("⚠️ No se encontró el archivo stopwords.txt. Se generará la nube sin stopwords personalizados.")
                        except Exception as e:
                            st.error(f"❌ Ocurrió un error al cargar los stopwords: {e}")

                        # Generar y mostrar la nube de palabras si hay texto
                        if text:
                            wordcloud = WordCloud(
                                width=800, height=450, background_color='white',
                                stopwords=stopwords
                            ).generate(text)

                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis("off")
                            st.pyplot(fig)
                        else:
                            st.warning("⚠️ No hay suficientes datos para generar una nube de palabras.")

        else:
            st.warning("⚠️ No hay reseñas disponibles para mostrar. Intente seleccionar otra aplicación o fuente.")
