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
import urllib.parse
# from translations import translations

# =========================
# 🎨 Cargar estilos CSS
# =========================
# def load_css():
#     with open("styles.css") as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# =========================
# 🏗️ Configurar la página
# =========================
st.set_page_config(page_title="Boomit - Social Intelligence", layout="wide")
# load_css()

with st.sidebar:
    st.page_link('app.py', label='App reviews analyzer', icon='📊')
    st.page_link('pages/📈 Facebook ads library scraping.py', label='📈 Facebook ads library scraping')


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
# 🏢 Cargar imagen del logo principal
# =========================
logo_path = "company_logo.png"
# st.markdown(f"""
#     <div style="display: flex; align-items: center; gap: 17px;">
#         <img src="data:image/png;base64,{base64.b64encode(open(logo_path, 'rb').read()).decode()}" width="120">
#         <h1 style="margin: 5;">Boomit - Social Intelligence</h1>
#     </div>
# """, unsafe_allow_html=True)

# =========================
# 🔐 Verificar autenticación
# =========================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    login()
    st.stop()


# =========================
# 🌍 Selección del país y apps
# =========================
country_mapping = {
    "Argentina": "ar", "Belice": "bz", "Bolivia": "bo", "Brasil": "br", "Chile": "cl",
    "Colombia": "co", "Costa Rica": "cr", "Cuba": "cu", "Ecuador": "ec",
    "El Salvador": "sv", "Estados Unidos": "us", "Guatemala": "gt", "Honduras": "hn",
    "México": "mx", "Nicaragua": "ni", "Panamá": "pa", "Paraguay": "py", "Perú": "pe",
    "Puerto Rico": "pr", "República Dominicana": "do", "Uruguay": "uy", "Venezuela": "ve"
}

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    selected_country = st.selectbox("🌍 Select the country:", list(country_mapping.keys()), key="selected_country")
with col2:
    app1_name = st.text_input("🔎 Enter the main app:", key="app1_name")
with col3:
    app2_name = st.text_input("🏆 Enter the competitor's app:", key="app2_name")

country = country_mapping.get(selected_country)

df_reviews = pd.DataFrame()

if st.button("🔍 Search reviews"):
    with st.spinner("🔄 Searching reviews, please wait..."):
        # =========================
        # 🔄 Función para obtener reseñas
        # =========================
        def fetch_reviews(app_name, app_label, type_client):
            app_id, app_data = fetch_app_data(app_name, country)
            if app_id and app_data:
                df = fetch_all_reviews(app_id, country, app_name, type_client, days=60)
                df["app"] = app_label
                return df, app_data.get("icon")
            return pd.DataFrame(), None

# =========================
# 📥 Cargar reseñas de ambas apps con verificación de estado
# =========================
if app1_name or app2_name and country:
    if (
        "last_app1_name" not in st.session_state or
        "last_app2_name" not in st.session_state or
        "last_country" not in st.session_state or
        st.session_state["last_app1_name"] != app1_name or
        st.session_state["last_app2_name"] != app2_name or
        st.session_state["last_country"] != country
    ):
        df_reviews_client = pd.DataFrame()
        df_reviews_competitor = pd.DataFrame()

        # ============================
        # 🚀 Obtener Reviews del Cliente
        # ============================
        app_id_android, _ = fetch_app_data(urllib.parse.quote(app1_name), urllib.parse.quote(country))
        app_id_ios, _ = fetch_app_data(urllib.parse.quote(app1_name), urllib.parse.quote(country))
        df_reviews_client = fetch_all_reviews(
            app_id_android=app_id_android,
            country_android=country,
            app_name_ios=app1_name if app_id_ios else None,
            type_client='cliente',
            days=90
        )
        df_reviews_client['app'] = app1_name

        # ============================
        # 🏆 Obtener Reviews de la Competencia
        # ============================
        app_id_android, _ = fetch_app_data(urllib.parse.quote(app2_name), urllib.parse.quote(country))
        app_id_ios, _ = fetch_app_data(urllib.parse.quote(app2_name), urllib.parse.quote(country))
        df_reviews_competitor = fetch_all_reviews(
            app_id_android=app_id_android,
            country_android=country,
            app_name_ios=app2_name if app_id_ios else None,
            type_client='competidor',
            days=90
        )
        df_reviews_competitor['app'] = app2_name

        df_reviews = pd.concat([df_reviews_client, df_reviews_competitor], ignore_index=True)
        df_reviews.to_excel('df_reviews.xlsx', index=False)
        st.session_state["df_reviews"] = df_reviews
        st.session_state["df_reviews_client"] = df_reviews_client
        st.session_state["df_reviews_competitor"] = df_reviews_competitor
        st.session_state["last_app1_name"] = app1_name
        st.session_state["last_app2_name"] = app2_name
        st.session_state["last_country"] = country
    else:
        df_reviews = st.session_state.get("df_reviews", pd.DataFrame())

# =========================
# 🔎 Selector de fuente y aplicación
# =========================
if not df_reviews.empty:
    # Agregar estilos CSS para reducir el espacio entre título y selector
    st.markdown(
        """
        <style>
        h4 {
            margin-bottom: 0px !important; /* Reduce espacio debajo del título */
        }
        div[data-testid="stRadio"] {
            margin-top: -10px !important; /* Reduce espacio sobre los selectores */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div style="margin-bottom: -80px;"><h4>🔎 Select the data source:</h4></div>', unsafe_allow_html=True)
    source_filter = st.radio("", ["All", "Android", "iOS"], index=0, horizontal=True)

    st.markdown('<div style="margin-bottom: -80px;"><h4>🔎 Select the app to analyze:</h4></div>', unsafe_allow_html=True)
    app_filter = st.radio("", [app1_name, app2_name], index=0, horizontal=True)

    df_filtered = df_reviews.copy()

    if source_filter != 'All':
        df_filtered = df_filtered[df_filtered["source"] == source_filter]

    if app_filter:
        df_filtered = df_filtered[df_filtered["app"] == app_filter]

    # =========================
    # 🎛️ FILTROS DE FECHAS EN BARRA LATERAL
    # =========================
    with st.sidebar:
        st.markdown("## 📅 Filtro de Fechas")

        if not df_filtered.empty:
            min_date, max_date = df_filtered["at"].min(), df_filtered["at"].max()

            if pd.isna(min_date) or pd.isna(max_date):
                st.warning("⚠️ No reviews available for the selected dates or the chosen source.")
            else:
                start_date = st.date_input("📅 From:", value=min_date, min_value=min_date, max_value=max_date, key="start_date_sidebar")
                end_date = st.date_input("📅 To:", value=max_date, min_value=min_date, max_value=max_date, key="end_date_sidebar")

                # Filtrar los datos según las fechas seleccionadas
                df_filtered = df_filtered[(df_filtered["at"] >= start_date) & (df_filtered["at"] <= end_date)]

    if not df_filtered.empty:
        # =========================
        # 📊 Mostrar KPIs dinámicos
        # =========================
        st.markdown("---")
        render_dynamic_kpis(df_filtered)
        st.markdown("---")
        
        # =========================
        # 📊 SELECTOR DE NIVEL DE AGREGACIÓN ARRIBA DEL GRÁFICO
        # =========================
        st.markdown('<div style="margin-bottom: -80px;"><h4>📊 Selecciona el nivel de agregación:</h4></div>', unsafe_allow_html=True)
        agg_option = st.radio("", ["Daily", "Weekly", "Monthly", "Yearly"], index=1, horizontal=True)

        # Aplicar nivel de agregación seleccionado
        if agg_option == "Daily":
            df_filtered["date"] = df_filtered["at"]
        elif agg_option == "Weekly":
            df_filtered["date"] = df_filtered["at"].apply(lambda x: x - timedelta(days=x.weekday()))
        elif agg_option == "Monthly":
            df_filtered["date"] = df_filtered["at"].apply(lambda x: x.replace(day=1))
        elif agg_option == "Yearly":
            df_filtered["date"] = df_filtered["at"].apply(lambda x: x.replace(month=1, day=1))
        
        # =========================
        # 📈 Gráficos de cantidad y promedio de reseñas
        # =========================
        grouped_counts = df_filtered.groupby("date").size().reset_index(name="Number of reviews")
        grouped_avg_score = df_filtered.groupby("date")["score"].mean().reset_index(name="Average rating")
        
        fig = go.Figure()

        # Agregar barras con etiquetas enteras
        fig.add_trace(go.Bar(
            x=grouped_counts['date'], 
            y=grouped_counts['Number of reviews'], 
            name='Number of reviews', 
            marker=dict(color='red'),
            text=grouped_counts['Number of reviews'].apply(lambda x: f"{int(x)}"),
            textposition='outside'
        ))

        # Agregar línea con etiquetas decimales con 1 decimal
        fig.add_trace(go.Scatter(
            x=grouped_avg_score['date'], 
            y=grouped_avg_score['Average rating'], 
            mode='lines+markers+text', 
            name='Average rating', 
            line=dict(color='blue'),
            text=grouped_avg_score['Average rating'].apply(lambda x: f"{x:.1f}"),
            textposition='top center'
        ))

        fig.update_layout(
            title="📈 Review evolution", 
            xaxis_title="Date", 
            yaxis_title="Number of reviews", 
            yaxis=dict(tickformat=',d'),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # 🤖 ANÁLISIS CON OPENAI
    # =========================
    st.markdown("---")
    st.markdown("### 🤖 Boomit One AI Analysis of Reviews")

    df_reviews_client = st.session_state.get("df_reviews_client", pd.DataFrame())
    df_reviews_competitor = st.session_state.get("df_reviews_competitor", pd.DataFrame())

    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
    openai.api_key = OPENAI_API_KEY

    def get_openai_insights(prompt):
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            thread = client.beta.threads.create()
            client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)

            run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)

            with st.spinner("🔄 Generating insights, please wait..."):
                while run.status != "completed":
                    time.sleep(2)
                    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            messages = client.beta.threads.messages.list(thread_id=thread.id)
            return messages.data[0].content[0].text.value

        except Exception as e:
            return f"Error while fetching insights from OpenAI: {e}"

    # Distribución horizontal clara de botones
    col_buttons = st.columns(4)

    # Placeholder único para los resultados
    output_placeholder = st.empty()

    with col_buttons[0]:
        analisis_general_clicked = st.button("🔍 Reviews Analysis")

    with col_buttons[1]:
        recomendaciones_clicked = st.button("💡 Recommendations")

    with col_buttons[2]:
        analisis_competencia_clicked = st.button("📊 Competitor Analysis")

    with col_buttons[3]:
        analisis_reviews_recientes = st.button("📈 Recent reviews Analysis")

    # Manejo del clic en los botones y mostrar resultado en la columna única
    if analisis_general_clicked:
        if not df_reviews_client.empty:
            comments_text = "\n".join(df_reviews_client["content"].dropna().tolist()).strip()
            prompt = f"Realiza un análisis general breve sobre estos comentarios, sin incluir recomendaciones:\n\n{comments_text}"
            insights = get_openai_insights(prompt)
            output_placeholder.markdown("#### 📌 Análisis General")
            output_placeholder.info(insights)
        else:
            output_placeholder.warning("⚠️ No hay suficientes comentarios del cliente para analizar.")

    elif recomendaciones_clicked:
        if not df_reviews_client.empty:
            comments_text = "\n".join(df_reviews_client["content"].dropna().tolist()).strip()
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

    elif analisis_reviews_recientes:
        if not df_reviews_client.empty:
            # Asegurarse de que la columna 'at' sea datetime
            df_reviews_client["at"] = pd.to_datetime(df_reviews_client["at"])

            # Filtrar por los últimos 90 días
            fecha_actual = datetime.now()
            hace_90_dias = fecha_actual - timedelta(days=90)
            df_ultimos_90 = df_reviews_client[df_reviews_client["at"] >= hace_90_dias]

            if df_ultimos_90.empty:
                output_placeholder.warning("⚠️ No hay suficientes comentarios en los últimos 90 días para generar recomendaciones.")
            else:
                # Dividir entre últimos 30 días y los 60 anteriores
                hace_30_dias = fecha_actual - timedelta(days=30)
                df_ultimos_30 = df_ultimos_90[df_ultimos_90["at"] >= hace_30_dias]
                df_anteriores_60 = df_ultimos_90[
                    (df_ultimos_90["at"] < hace_30_dias)
                ]

                comentarios_ultimos_30 = "\n".join(df_ultimos_30["content"].dropna().tolist()).strip()
                comentarios_anteriores_60 = "\n".join(df_anteriores_60["content"].dropna().tolist()).strip()

                prompt = (
                    "Quiero que analices los comentarios de una app móviles divididos en dos períodos:\n\n"
                    "1. **Últimos 30 días**:\n"
                    f"{comentarios_ultimos_30}\n\n"
                    "2. **60 días anteriores a ese período**:\n"
                    f"{comentarios_anteriores_60}\n\n"
                    "Con base en esta comparación, dame principalmente insights sobre que cambios impactaron en la percepcion del usuario sobre la app, ya sea una evolucion positiva o negativa. Tambien dame recomendaciones **concretas y accionables** que reflejen los cambios en el feedback reciente. "
                    "No incluyas un análisis general. Resalta oportunidades de mejora o problemas nuevos que hayan surgido."
                )

                insights = get_openai_insights(prompt)
                output_placeholder.markdown("#### 📌 Recomendaciones")
                output_placeholder.info(insights)
        else:
            output_placeholder.warning("⚠️ No hay suficientes comentarios para generar recomendaciones.")


    st.markdown("---")
    st.markdown("")

    # **Histograma y Nube de Palabras**
    if not df_filtered.empty:
        col1, col2 = st.columns(2)

        # Agregar columna para etiquetas de puntajes (estrellas)
        df_filtered['score_label'] = df_filtered['score'].apply(lambda x: f'{int(x)}⭐')

        with col1:
            st.markdown("### 📊 Rating Distribution")
            fig_hist = px.histogram(df_filtered, x='score_label', nbins=5, title="Rating Distribution", text_auto=True)
            fig_hist.update_layout(
                height=410,
                bargap=0.1,
                xaxis_title="Rating",
                yaxis_title="Quantity",
                margin=dict(l=40, r=40, t=60, b=40)
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            st.markdown("### ☁️ Word cloud in reviews")
            text = " ".join(str(review) for review in df_filtered["content"].dropna())

            # Cargar stopwords desde el archivo stopwords.txt
            stopwords = set()
            try:
                with open("stopwords.txt", "r", encoding="utf-8") as f:
                    stopwords = set(line.strip() for line in f if line.strip())
            except FileNotFoundError:
                st.warning("⚠️ The file stopwords.txt was not found. The word cloud will be generated without custom stopwords.")
            except Exception as e:
                st.error(f"❌ An error occurred while loading the stopwords: {e}")

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
                st.warning("⚠️ There is not enough data to generate a word cloud.")
        # =========================
        # 🗂️ TABLA DE COMENTARIOS DINÁMICA
        # =========================
        st.markdown("---")
        st.markdown("### 📝 Comments table")

        # Selector para elegir el tipo de comentarios
        comment_option = st.selectbox("📌 Select the type of comments:", ["Recientes", "Mejores", "Peores"])

        # Evitar cálculos innecesarios si el dataframe está vacío
        if not df_filtered.empty:
            # Crear una copia optimizada sin manipulación innecesaria
            comments = df_filtered[['at', 'score', 'content', 'source']].copy()

            # Aplicar el filtro elegido
            if comment_option == "Recientes":
                comments = comments.sort_values(by='at', ascending=False).head(10)
            elif comment_option == "Mejores":
                comments = comments.sort_values(by='score', ascending=False).head(10)
            else:  # Peores
                comments = comments.sort_values(by='score', ascending=True).head(10)

            # Convertir las calificaciones a estrellas solo si se muestran
            comments["score"] = comments["score"].apply(lambda x: "⭐" * int(x) if not pd.isna(x) else "Sin calificación")

            # Renombrar columnas
            comments = comments.rename(columns={
                "at": "Date",
                "score": "Rate",
                "content": "Comment",
                "source": "Platform"
            })

            # Mostrar la tabla optimizada
            st.data_editor(
                comments,
                use_container_width=True,
                hide_index=True,
                disabled=True,
                column_config={
                    "Platform": st.column_config.TextColumn("Platform", width="100px")
                }
            )

        else:
            st.warning("⚠️ No hay comentarios disponibles.")

    else:
        st.warning("⚠️ No reviews available to display. Please try selecting another app or source.")
else:
    st.stop()
