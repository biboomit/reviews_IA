import streamlit as st
from funciones import login
import base64

st.set_page_config(page_title="Home", layout="wide")

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

st.title("🏠 Página Principal")
st.write("Bienvenido a la aplicación principal. Usa el menú de la izquierda para navegar.")