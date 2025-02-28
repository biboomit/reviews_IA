import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from funciones import login, fetch_app_data, fetch_all_reviews, render_dynamic_kpis
import plotly.graph_objects as go
import plotly.express as px
from wordcloud import WordCloud
import base64
import matplotlib.pyplot as plt
from io import BytesIO
import requests
import openai
import time 
from config import client_mapping, competencia_config
import urllib.parse
from translations import translations

# Primero define page_config con título genérico
st.set_page_config(page_title="Boomit", layout="wide")

# Guardar el idioma en la sesión y evitar que Streamlit lo resetee
if 'language' not in st.session_state:
    st.session_state['language'] = "Español"

selected_language = st.sidebar.selectbox(
    "🌐 Idioma / Language", ["Español", "English"], 
    index=0 if st.session_state['language'] == "Español" else 1
)

# Solo actualizar la variable de sesión si realmente cambió el idioma
if selected_language != st.session_state['language']:
    st.session_state['language'] = selected_language
    st.rerun()  # <- ⚠️ Esto fuerza la recarga solo cuando se cambia el idioma

# Asignar el idioma seleccionado a la variable lang
lang = 'es' if st.session_state['language'] == "Español" else 'en'

def t(key):
    return translations[lang].get(key, key)


# =====================================
# 🚀 Navbar Superior Mejorada con Animación de Título
# =====================================
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
        <h1>{t('page_title')}</h1>
    </div>
    
    """,
    unsafe_allow_html=True
)

# =====================================
# 🔐 Verificar autenticación
# =====================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login(t)
    st.stop()

# =====================================
# 🌍 Selección del país y app
# =====================================

country_mapping = {
    "Argentina": "ar", "Chile": "cl", "Colombia": "co", "Ecuador": "ec",
    "El Salvador": "sv", "Estados Unidos": "us", "Guatemala": "gt", "Honduras": "hn",
    "México": "mx", "Nicaragua": "ni", "Panamá": "pa", "Paraguay": "py", "Perú": "pe",
    "República Dominicana": "do"
}


col1, col2 = st.columns([2, 2])
with col1:
    selected_country = st.selectbox("🌍 Seleccione el país de la tienda:", list(country_mapping.keys()), key="selected_country")
with col2:
    # Agregar un placeholder inicial vacío
    app_name = st.selectbox(
        "🔎 Ingrese el nombre de la aplicación:",
        ["Selecciona una aplicación..."] + list(client_mapping.keys()),  # Agregar opción vacía
        key="selected_client"
    )

# Verificar si el usuario ha seleccionado una aplicación válida
if app_name == "Selecciona una aplicación...":
    st.warning("Por favor, seleccione una aplicación.")
    app_name = None 

country = country_mapping.get(selected_country)
client_data = client_mapping.get(app_name, {})

# =====================================
# 📊 Lógica de la aplicación
# =====================================
if app_name and country:
    if (
        "last_app_name" not in st.session_state or
        "last_country" not in st.session_state or
        st.session_state["last_app_name"] != app_name or
        st.session_state["last_country"] != country
    ):
        # 📥 DataFrames separados
        df_reviews_client = pd.DataFrame()
        df_reviews_competitor = pd.DataFrame()

        # ============================
        # 🚀 Obtener Reviews del Cliente
        # ============================
        if client_data:
            with st.spinner(f"⏳ Descargando reseñas de {app_name}..."):
                app_id_android = None
                app_id_ios = None
                places_ids = client_data.get("maps_place_id")

                # Obtener identificadores solo si tiene la fuente disponible
                if client_data.get("android") == 1:
                    app_id_android, _ = fetch_app_data(urllib.parse.quote(app_name), urllib.parse.quote(country))

                if client_data.get("ios") == 1:
                    app_id_ios, _ = fetch_app_data(urllib.parse.quote(app_name), urllib.parse.quote(country))

                # Llamar a la función fetch_all_reviews solo con las fuentes disponibles
                df_reviews_client = fetch_all_reviews(
                    app_id_android=app_id_android if app_id_android else None,
                    country_android=country,
                    app_name_ios=app_name if app_id_ios else None,
                    type_client='cliente',
                    places_ids=places_ids if client_data.get("web") == 1 else None,
                    days=60
                )

                # Agregar columnas adicionales para contexto
                if not df_reviews_client.empty:
                    df_reviews_client["Fuente"] = df_reviews_client["source"]
                    df_reviews_client["Cliente"] = app_name

        # ============================
        # 🚀 Obtener Reviews del Competidor
        # ============================
        competitor_name = client_data.get("competencia")
        competitor_data = competencia_config.get(competitor_name, {})

        if competitor_data:
            with st.spinner(f"⏳ Descargando reseñas del competidor {competitor_name}..."):
                comp_id_android = None
                comp_id_ios = None
                comp_places_ids = competitor_data.get("maps_place_id")

                # Obtener identificadores solo si tiene la fuente disponible
                if competitor_data.get("android") == 1:
                    comp_id_android, _ = fetch_app_data(urllib.parse.quote(competitor_name), urllib.parse.quote(country))

                if competitor_data.get("ios") == 1:
                    comp_id_ios, _ = fetch_app_data(urllib.parse.quote(competitor_name), urllib.parse.quote(country))

                # Llamar a la función fetch_all_reviews solo con las fuentes disponibles
                df_reviews_competitor = fetch_all_reviews(
                    app_id_android=comp_id_android if comp_id_android else None,
                    country_android=country,
                    app_name_ios=competitor_name if comp_id_ios else None,
                    type_client='competencia',
                    places_ids=comp_places_ids if competitor_data.get("web") == 1 else None,
                    days=60
                )

                # Agregar columnas adicionales para contexto
                if not df_reviews_competitor.empty:
                    df_reviews_competitor["Fuente"] = df_reviews_competitor["source"]
                    df_reviews_competitor["Cliente"] = competitor_name

        # Guardar en sesión de Streamlit
        st.session_state["df_reviews_client"] = df_reviews_client
        st.session_state["df_reviews_competitor"] = df_reviews_competitor

        # ACTUALIZAR SIEMPRE LOS VALORES "last_app_name" y "last_country" LUEGO DE DESCARGAR
        st.session_state["last_app_name"] = app_name
        st.session_state["last_country"] = country

    else:
        df_reviews_client = st.session_state.get("df_reviews_client", pd.DataFrame())
        df_reviews_competitor = st.session_state.get("df_reviews_competitor", pd.DataFrame())

    # Guardar archivos si hay datos
    if not df_reviews_client.empty:
        df_reviews_client.to_excel('df_reviews_client.xlsx', index=False)
    if not df_reviews_competitor.empty:
        df_reviews_competitor.to_excel('df_reviews_competitor.xlsx', index=False)


    st.markdown("")
    if not df_reviews_client.empty:
        # =========================
        # 🎛️ SELECTOR DE FUENTE EN EL CUERPO PRINCIPAL + LOGO APP
        # =========================
        st.markdown('<div style="margin-bottom: -60px;"><h4>🌐 Seleccione la fuente de datos:</h4></div>', unsafe_allow_html=True)
        source_filter = st.radio("", ["Todas", "Android", "iOS","Web"], index=0, horizontal=True)

        # Filtrar por fuente dinámicamente
        if source_filter != "Todas":
            df_filtered = df_reviews_client[df_reviews_client["source"] == source_filter]
        else:
            df_filtered = df_reviews_client.copy()

        # =========================
        # 🎛️ FILTROS DE FECHAS EN BARRA LATERAL
        # =========================
        with st.sidebar:
            st.markdown("## 📅 Filtro de Fechas")

            if not df_filtered.empty:
                min_date, max_date = df_filtered["at"].min(), df_filtered["at"].max()

                if pd.isna(min_date) or pd.isna(max_date):
                    st.warning("⚠️ No hay reseñas disponibles para las fechas seleccionadas o para la fuente elegida.")
                else:
                    start_date = st.date_input("📅 Desde:", value=min_date, min_value=min_date, max_value=max_date, key="start_date_sidebar")
                    end_date = st.date_input("📅 Hasta:", value=max_date, min_value=min_date, max_value=max_date, key="end_date_sidebar")

                    # Filtrar los datos según las fechas seleccionadas
                    df_filtered = df_filtered[(df_filtered["at"] >= start_date) & (df_filtered["at"] <= end_date)]

        if not df_filtered.empty:
            # =========================
            # 🔢 MÉTRICAS ARRIBA
            # =========================
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
            render_dynamic_kpis(df_filtered)
            st.markdown("---")

            # =========================
            # 📊 SELECTOR DE NIVEL DE AGREGACIÓN ARRIBA DEL GRÁFICO
            # =========================
            st.markdown('<div style="margin-bottom: -60px;"><h4>📊 Selecciona el nivel de agregación:</h4></div>', unsafe_allow_html=True)
            agg_option = st.radio("", ["Diario", "Semanal", "Mensual", "Anual"], index=1, horizontal=True)

            # Aplicar nivel de agregación seleccionado
            if agg_option == "Diario":
                df_filtered["date"] = df_filtered["at"]
            elif agg_option == "Semanal":
                df_filtered["date"] = df_filtered["at"].apply(lambda x: x - timedelta(days=x.weekday()))
            elif agg_option == "Mensual":
                df_filtered["date"] = df_filtered["at"].apply(lambda x: x.replace(day=1))
            elif agg_option == "Anual":
                df_filtered["date"] = df_filtered["at"].apply(lambda x: x.replace(month=1, day=1))

            # Generar gráfico dinámico
            grouped_counts = df_filtered.groupby("date").size().reset_index(name="Cantidad de Reseñas")
            grouped_avg_score = df_filtered.groupby("date")["score"].mean().reset_index(name="Calificación Promedio")

            fig = go.Figure()

            # Agregar barras con etiquetas enteras
            fig.add_trace(go.Bar(
                x=grouped_counts['date'], 
                y=grouped_counts['Cantidad de Reseñas'], 
                name='Cantidad de Reseñas', 
                marker=dict(color='red'),
                text=grouped_counts['Cantidad de Reseñas'].apply(lambda x: f"{int(x)}"),
                textposition='outside'
            ))

            # Agregar línea con etiquetas decimales con 1 decimal
            fig.add_trace(go.Scatter(
                x=grouped_avg_score['date'], 
                y=grouped_avg_score['Calificación Promedio'], 
                mode='lines+markers+text', 
                name='Calificación Promedio', 
                line=dict(color='blue'),
                text=grouped_avg_score['Calificación Promedio'].apply(lambda x: f"{x:.1f}"),
                textposition='top center'
            ))

            fig.update_layout(
                title="📈 Evolución de reseñas", 
                xaxis_title="Fecha", 
                yaxis_title="Cantidad de Reseñas", 
                yaxis=dict(tickformat=',d'),
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
                    fig_hist = px.histogram(df_filtered, x='score_label', nbins=5, title="Distribución de Calificaciones", text_auto=True)
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
                        
                # =========================
                # 🗂️ TABLA DE COMENTARIOS DINÁMICA
                # =========================
                st.markdown("---")
                st.markdown(f'<div class="animated"><h4>{t("comments_table")}</h4></div>', unsafe_allow_html=True)

                # Selector para elegir el tipo de comentarios
                comment_option = st.selectbox(t('comments_type'), [t('recent'), t('best'), t('worst')])

                # Evitar cálculos innecesarios si el dataframe está vacío
                if not df_filtered.empty:
                    # Crear una copia optimizada sin manipulación innecesaria
                    comments = df_filtered[['at', 'score', 'content', 'source']].copy()

                    # Aplicar el filtro elegido
                    if comment_option == t('recent'):
                        comments = comments.sort_values(by='at', ascending=False).head(10)
                    elif comment_option == t('best'):
                        comments = comments.sort_values(by='score', ascending=False).head(10)
                    else:  # Peores
                        comments = comments.sort_values(by='score', ascending=True).head(10)

                    # Convertir las calificaciones a estrellas solo si se muestran
                    comments["score"] = comments["score"].apply(lambda x: "⭐" * int(x) if not pd.isna(x) else "Sin calificación")

                    # Renombrar columnas
                    comments = comments.rename(columns={
                        "at": "Fecha",
                        "score": "Calificación",
                        "content": "Comentario",
                        "source": "Plataforma"
                    })

                    # Mostrar la tabla optimizada
                    st.data_editor(
                        comments,
                        use_container_width=True,
                        hide_index=True,
                        disabled=True,
                        column_config={
                            "Plataforma": st.column_config.TextColumn("Plataforma", width="100px")
                        }
                    )

                else:
                    st.warning("⚠️ No hay comentarios disponibles.")
                
                # =========================
                # 🤖 ANÁLISIS CON OPENAI
                # =========================
                st.markdown("---")
                st.markdown("### 🤖 Análisis de Boomit One AI sobre las Reseñas")

                OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
                ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
                openai.api_key = OPENAI_API_KEY

                def get_openai_insights(prompt):
                    try:
                        client = openai.OpenAI(api_key=OPENAI_API_KEY)
                        thread = client.beta.threads.create()
                        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)

                        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)

                        with st.spinner("🔄 Generando insights, por favor espera..."):
                            while run.status != "completed":
                                time.sleep(2)
                                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

                        messages = client.beta.threads.messages.list(thread_id=thread.id)
                        return messages.data[0].content[0].text.value

                    except Exception as e:
                        return f"Error al obtener insights de OpenAI: {e}"

                # Distribución horizontal clara de botones
                col_buttons = st.columns(3)

                # Placeholder único para los resultados
                output_placeholder = st.empty()

                with col_buttons[0]:
                    analisis_general_clicked = st.button("🔍 Análisis General")

                with col_buttons[1]:
                    recomendaciones_clicked = st.button("💡 Recomendaciones")

                with col_buttons[2]:
                    analisis_competencia_clicked = st.button("📊 Análisis Competencia")

                # Manejo del clic en los botones y mostrar resultado en la columna única
                if analisis_general_clicked:
                    if not df_reviews_client.empty:
                        comments_text = "\n".join(df_reviews_client["content"].dropna().head(50).tolist()).strip()
                        prompt = f"Realiza un análisis general breve sobre estos comentarios, sin incluir recomendaciones:\n\n{comments_text}"
                        insights = get_openai_insights(prompt)
                        output_placeholder.markdown("#### 📌 Análisis General")
                        output_placeholder.info(insights)
                    else:
                        output_placeholder.warning("⚠️ No hay suficientes comentarios del cliente para analizar.")

                elif recomendaciones_clicked:
                    if not df_reviews_client.empty:
                        comments_text = "\n".join(df_reviews_client["content"].dropna().head(50).tolist()).strip()
                        prompt = f"Dame recomendaciones concretas y accionables basadas en estos comentarios. No incluyas un análisis general:\n\n{comments_text}"
                        insights = get_openai_insights(prompt)
                        output_placeholder.markdown("#### 📌 Recomendaciones")
                        output_placeholder.info(insights)
                    else:
                        output_placeholder.warning("⚠️ No hay suficientes comentarios para generar recomendaciones.")

                elif analisis_competencia_clicked:
                    if not df_reviews_client.empty and not df_reviews_competitor.empty:
                        comments_client = "\n".join(df_reviews_client["content"].dropna().head(50).tolist()).strip()
                        comments_competitor = "\n".join(df_reviews_competitor["content"].dropna().head(30).tolist()).strip()
                        prompt = (
                            "Realiza un análisis comparativo breve entre los siguientes comentarios del cliente y del competidor, "
                            "destacando fortalezas y debilidades clave:\n\n"
                            f"Cliente:\n{comments_client}\n\nCompetidor:\n{comments_competitor}"
                        )
                        insights = get_openai_insights(prompt)
                        output_placeholder.markdown("#### 📌 Análisis Competitivo")
                        output_placeholder.info(insights)
                    else:
                        output_placeholder.warning("⚠️ No hay suficientes comentarios del cliente o del competidor para realizar el análisis.")


        else:
            st.warning("⚠️ No hay reseñas disponibles para mostrar. Intente seleccionar otra aplicación o fuente.")