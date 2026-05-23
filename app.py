import streamlit as st
import os
from conversor import hl7_to_fhir_universal

st.set_page_config(
    page_title="HL7 to FHIR | UPNA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'empezar' not in st.session_state:
    st.session_state.empezar = False

# 2. BLOQUE DE ESTILO (CSS) - CON EL AZUL DE PYTHON (#306998)
st.markdown("""<style>
.stApp {background-color: #f8f9fa;}

[data-testid="stSidebar"] {background-color: #306998;}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {padding-left: 1.5rem;padding-right: 1.5rem;}
[data-testid="stSidebar"] .stMarkdown,[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: white !important;
    font-weight: 700 !important;
}

.patient-box {
    background-color: #ffffff;
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #306998;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    margin-bottom: 10px;
}

.patient-label {
    color: #6c757d;
    font-size: 0.8rem;
    font-weight: bold;
    text-transform: uppercase;
}

.patient-value {
    color: #2c3e50;
    font-size: 1.05rem;
    font-weight: 600;
    word-wrap: break-word;
}

.upna-logo img {border-radius: 5px;background-color: white;padding: 3px;box-shadow: 0 1px 3px rgba(0,0,0,0.1);}

.stButton > button {
    width: 100%;
    border-radius: 10px;
    background-color: #306998 !important;
    color: white !important;
    border: none !important;
}

.ecg-scroll-container {
    width: 100%;
    overflow-x: auto;
    white-space: nowrap;
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px;
}

[data-testid="stFileUploader"] section {
    background-color: #1a365d !important;
    border: 2px solid #ffffff !important;
    border-radius: 12px !important;
    padding: 12px !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
}

[data-testid="stFileUploaderDropzone"] * {
    color: white !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background-color: #306998 !important;
    color: white !important;
    border: 1px solid white !important;
    border-radius: 8px !important;
}

[data-testid="stFileUploaderFile"] {
    background-color: #2b4c7e !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    padding: 8px !important;
}

[data-testid="stFileUploaderFile"] * {
    color: white !important;
}

[data-testid="stFileUploaderFile"] svg {
    fill: white !important;
    color: white !important;
}

button[aria-label="Remove file"] {
    background: transparent !important;
    border: none !important;
}

button[aria-label="Remove file"] svg {
    fill: white !important;
    color: white !important;
}

[data-testid="stFileUploader"] div {
    background-color: transparent;
}

[data-testid="stFileUploaderFile"] {
    background-color: #2b4c7e !important;
}

</style>
""", unsafe_allow_html=True)

if not st.session_state.empezar:
    col_titulo, col_logo = st.columns([6, 1])
    with col_titulo:
        st.title("🏥 Sistema de Interoperabilidad Clinical")
        st.caption("Máster en Ingeniería Biomédica | Universidad Pública de Navarra")
    with col_logo:
        if os.path.exists("Upna.png"): st.image("Upna.png", width=100)

    st.markdown("---")
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        st.markdown("""
        ### Bienvenido al Conversor HL7 ➔ FHIR Interactivo
        Esta herramienta permite transformar mensajes HL7 v2 complejos (incluyendo señales vectoriales de ECG e instrumentación MDC) en recursos FHIR robustos y estandarizados.
        
        **Instrucciones de uso:**
        1. Prepara tu archivo de monitorización clínica u onda electrocardiográfica (`.hl7`).
        2. Haz clic en el botón de abajo para activar el panel de control.
        3. Arrastra el archivo al cargador lateral.
        4. Revisa las señales reconstruidas dinámicamente y descarga tu Bundle interoperable en JSON.
        """)
        if st.button("Empezar a convertir"):
            st.session_state.empezar = True
            st.rerun()
    with col_w2:
        st.image("https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&q=80&w=400")

else:
    with st.sidebar:
        st.markdown("## ⚙️ Panel de Control")
        st.markdown("---")
        archivo = st.file_uploader("Subir mensaje HL7 v2", type=["hl7"])
        if st.button("🏠 Volver al Inicio"):
            st.session_state.empezar = False
            st.rerun()

    col_titulo, col_logo = st.columns([6, 1])
    with col_titulo:
        st.title("🏥 Conversor Clínico HL7 ➔ FHIR")
        st.caption("Máster en Ingeniería Biomédica | Universidad Pública de Navarra")
    with col_logo:
        if os.path.exists("Upna.png"):
            st.markdown('<div class="upna-logo">', unsafe_allow_html=True)
            st.image("Upna.png", width=100)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    if archivo:
        try:
            content = archivo.getvalue().decode("utf-8")
            resumen, fhir_json = hl7_to_fhir_universal(content)

            if resumen:
                with st.expander("👤 DATOS PERSONALES DEL PACIENTE", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f"""<div class="patient-box"><div class="patient-label">Paciente</div><div class="patient-value">{resumen['paciente']}</div></div>""", unsafe_allow_html=True)
                    with c2: st.markdown(f"""<div class="patient-box"><div class="patient-label">ID Sistema</div><div class="patient-value">{resumen['id']}</div></div>""", unsafe_allow_html=True)
                    with c3: st.markdown(f"""<div class="patient-box"><div class="patient-label">Centro Origen</div><div class="patient-value">{resumen['centro']}</div></div>""", unsafe_allow_html=True)

                if resumen["figura_plotly"] is not None:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("📈 Trazado Electrocardiográfico Continuo (Papel Milimetrado)")
                    st.markdown('<div class="ecg-scroll-container">', unsafe_allow_html=True)
                    st.plotly_chart(resumen["figura_plotly"], use_container_width=False)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("🩺 Parámetros e Instrumentación del Mensaje (OBX)")
                st.dataframe(resumen['datos'], use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("📦 Exportación y Datos FHIR")
                
                st.download_button(
                    label="📥 DESCARGAR BUNDLE FHIR (.JSON)",
                    data=fhir_json,
                    file_name=f"fhir_{resumen['id']}.json",
                    mime="application/json",
                    use_container_width=True
                )

                with st.expander("🔍 Ver código fuente del FHIR Bundle"):
                    st.code(fhir_json, language="json")
            else:
                st.error("Error estructural en el archivo cargado.")
        except Exception as e:
            st.error(f"Error al procesar el archivo clínico: {str(e)}")
    else:
        st.info("👈 Por favor, sube un archivo HL7 en el panel de la izquierda para comenzar.")