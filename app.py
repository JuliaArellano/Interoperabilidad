import streamlit as st
import hl7
import json
import os
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.humanname import HumanName
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference
from fhir.resources.sampleddata import SampledData
from fhir.resources.device import Device
from fhir.resources.organization import Organization

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="HL7 to FHIR | UPNA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'empezar' not in st.session_state:
    st.session_state.empezar = False

# 2. BLOQUE DE ESTILO (CSS) - CON EL AZUL DE PYTHON (#306998)
Viendo la captura queda claro el problema: al poner el fondo del mismo azul (#306998) sobre la barra lateral que ya tiene ese mismo color, el cargador "desaparece" visualmente y solo se ve el recuadro blanco del botón.

Si el negro rompe demasiado la estética, la mejor solución técnica y visual es usar un azul muy oscuro (azul noche/marino). De esta forma mantiene la armonía con la paleta de colores de tu aplicación, contrasta perfectamente con la barra lateral y hace que el texto blanco sea 100% legible.

Prueba a sustituir el bloque CSS por este código, usando el tono #1a365d (un azul oscuro elegante):

Python
# 2. BLOQUE DE ESTILO (CSS) - CON AZUL OSCURO EN EL CARGADOR PARA CONTRAS-TE
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #306998; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { padding-left: 1.5rem; padding-right: 1.5rem; }
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: white !important; font-weight: 700 !important; }
    .patient-box { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #306998; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .patient-label { color: #6c757d; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; }
    .patient-value { color: #2c3e50; font-size: 1.05rem; font-weight: 600; word-wrap: break-word; }
    .upna-logo img { border-radius: 5px; background-color: white; padding: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #306998; color: white; }
    .ecg-scroll-container { width: 100%; overflow-x: auto; white-space: nowrap; background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; }
    
    /* --- NUEVA CONFIGURACIÓN: AZUL OSCURO NOCHE --- */
    [data-testid="stFileUploader"] section {
        background-color: #1a365d !important; /* Azul marino oscuro */
        border: 2px dashed #ffffff !important; /* Línea discontinua blanca clara */
        border-radius: 10px;
        padding: 10px;
    }
    /* Asegurar que los textos informativos brillen en blanco */
    [data-testid="stFileUploader"] section * {
        color: #ffffff !important;
    }
    /* Botón "Browse files" integrado en el diseño oscuro */
    [data-testid="stFileUploader"] button {
        background-color: #2b4c7e !important; /* Un azul intermedio */
        color: white !important;
        border: 1px solid #ffffff !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 3. MOTOR UNIVERSAL OPTIMIZADO HL7 -> FHIR ---
def hl7_to_fhir_universal(hl7_content):
    lineas = hl7_content.splitlines()
    raw = "\r".join([l.strip() for l in lineas if l.strip()])
    h = hl7.parse(raw)
    
    # --- EXTRACCIÓN MSH Y FECHA CLÍNICA ---
    msh = h.segment('MSH')
    
    try:
        msh_time = str(msh[7]).strip()
        fecha_objeto = datetime.strptime(msh_time[:14], "%Y%m%d%H%M%S")
        fecha_fhir = fecha_objeto.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        fecha_fhir = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # --- EXTRACCIÓN PID ---
    pid = h.segment('PID')
    fhir_patient = Patient()
    
    try:
        id_raw = str(pid[3][0][0]) if len(pid[3][0]) > 0 else str(pid[3][0])
    except Exception:
        id_raw = str(pid[3])
    id_paciente = id_raw.replace("_", "-")
    fhir_patient.id = id_paciente
    
    centro_real = "Centro de Salud"
    try:
        if len(pid[3][0]) > 3 and pid[3][0][3]:
            centro_real = str(pid[3][0][3])
        elif len(pid[3]) > 3 and pid[3][3]:
            centro_real = str(pid[3][3])
    except Exception:
        pass
    
    fhir_patient.identifier = [{"value": id_paciente, "assigner": {"display": centro_real}}]
    
    nombres_texto = []
    lista_nombres_fhir = []
    
    for repeticion in pid[5]:
        nom_fhir = HumanName()
        nom_fhir.family = str(repeticion[0]) if len(repeticion) > 0 and repeticion[0] else None
        nom_fhir.given = [str(repeticion[1])] if len(repeticion) > 1 and repeticion[1] else None
        
        try:
            tipo_nombre = str(repeticion[6]).strip() if len(repeticion) > 6 else ""
            if tipo_nombre == "L": nom_fhir.use = "official"
            elif tipo_nombre == "N": nom_fhir.use = "nickname"
            else: nom_fhir.use = "usual"
        except IndexError:
            nom_fhir.use = "usual"
            
        lista_nombres_fhir.append(nom_fhir)
        if len(repeticion) > 1 and repeticion[1]:
            nombres_texto.append(f"{repeticion[1]} {repeticion[0] if repeticion[0] else ''}")
            
    fhir_patient.name = lista_nombres_fhir
    
    nombre_legible = nombres_texto[0] if nombres_texto else id_paciente
    fhir_patient.text = {
        "status": "generated",
        "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p><b>Paciente:</b> {nombre_legible} (ID: {id_paciente})</p></div>'
    }

    # --- NUEVO: RECURSO ORGANIZACIÓN (PERFORMER) ---
    # Al declarar explícitamente el centro médico como una Organización, solucionamos los Warnings de "should have a performer"
    fhir_organization = Organization(
        id="centro-emisor",
        active=True,
        name=centro_real
    )
    fhir_organization.text = {
        "status": "generated",
        "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p><b>Organización Emisora:</b> {centro_real}</p></div>'
    }
    referencia_performer = Reference(reference="http://localhost/Organization/centro-emisor")

    # --- EXTRACCIÓN OBR ---
    obr = h.segment('OBR')
    panel = Observation(
        status="final",
        code=CodeableConcept(),
        subject=Reference(reference=f"http://localhost/Patient/{fhir_patient.id}"),
        effectiveDateTime=fecha_fhir,
        device=Reference(reference="http://localhost/Device/device-hardware"),
        performer=[referencia_performer]  # <--- SOLUCIÓN WARNING PANEL
    )
    
    panel.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="vital-signs", display="Vital Signs")])]
    
    try:
        codigo_loinc = str(obr[4][0][0])
        display_loinc = str(obr[4][0][1]) if len(obr[4][0]) > 1 else "Panel de Observaciones"
        sistema_loinc = "http://loinc.org"
    except Exception:
        codigo_loinc = "29274-8"
        display_loinc = "VITAL SIGNS MEASUREMENTS"
        sistema_loinc = "http://loinc.org"
        
    panel.code.coding = [Coding(system=sistema_loinc, code=codigo_loinc, display=display_loinc)]
    panel.id = "panel-observations"
    panel.hasMember = []
    
    panel.text = {
        "status": "generated",
        "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p><b>Panel Clínico:</b> {display_loinc} (Código LOINC: {codigo_loinc})</p></div>'
    }

    # --- RECURSOS ADICIONALES Y CONFIGURACIÓN ---
    recursos_bundle = [fhir_patient, fhir_organization, panel]
    
    tiene_dispositivo = False
    device_data = {
        "resourceType": "Device",
        "id": "device-hardware",
        "manufacturer": "g.tec",
        "identifier": [],
        "property": [] 
    }
    
    datos_ondas = {}
    contextos_derivaciones = {}
    tabla_visual = []
    
    datos_presion_arterial = {"sistolica": None, "diastolica": None, "num_seg": "235"}

    # --- PROCESAR CADA SEGMENTO OBX ---
    for obx in h['OBX']:
        num_seg = int(str(obx[1]))
        tipo_dato = str(obx[2])
        
        try:
            id_num_code = str(obx[3][0][0]).strip()
            id_txt_code = str(obx[3][0][1]).strip() if len(obx[3][0]) > 1 else "Observation"
            
            if id_num_code.isdigit() and 2000 < int(id_num_code) < 3000:
                sistema_cod = "http://localhost/identifiers/mdc-codes"
            else:
                sistema_cod = "http://loinc.org"
        except Exception:
            id_num_code = str(obx[3]).strip()
            id_txt_code = "Medición"
            sistema_cod = "http://localhost/identifiers/mdc-codes"

        derivacion_actual = "Lead II" if num_seg >= 15 else "Lead I"
        
        if derivacion_actual not in contextos_derivaciones:
            contextos_derivaciones[derivacion_actual] = {"handles": []}
            
        if "2445" in id_num_code or "TIME_PD" in id_txt_code.upper():
            try:
                texto_periodo = str(obx[5]).split("^")[0].strip()
                contextos_derivaciones[derivacion_actual]["periodo_ms"] = float(texto_periodo)
                contextos_derivaciones[derivacion_actual]["Ts"] = (
                    contextos_derivaciones[derivacion_actual]["periodo_ms"] / 1000.0
                )
                tabla_visual.append({
                    "Componente OBX": f"OBX-{num_seg:02d}",
                    "Medición / Parámetro": f"{id_txt_code} ({derivacion_actual})",
                    "Valor Integrado": f"{texto_periodo} ms"
                })
            except Exception:
                pass
                
        # --- CASO A: OBSERVACIÓN NUMÉRICA ESTÁNDAR (NM) ---
        elif tipo_dato == "NM" and "SIMP_SA_OBS_VAL" not in id_txt_code and "2632" not in id_num_code:
            valor_num = float(str(obx[5]).strip())
            
            unidad_codigo = None
            unidad_display = None
            try:
                if len(obx[6]) > 0 and str(obx[6][0][0]).strip():
                    unidad_codigo = str(obx[6][0][0]).strip()
                    if len(obx[6][0]) > 1 and str(obx[6][0][1]).strip():
                        unidad_display = str(obx[6][0][1]).strip()
                    else:
                        unidad_display = unidad_codigo
                elif str(obx[6]).strip():
                    unidad_codigo = str(obx[6]).strip()
                    unidad_display = unidad_codigo
            except Exception:
                pass

            if "8480-6" in id_num_code or "SYSTOLIC" in id_txt_code.upper():
                datos_presion_arterial["sistolica"] = valor_num
                datos_presion_arterial["num_seg"] = str(num_seg)
                tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": "Presión Arterial Sistólica", "Valor Integrado": f"{valor_num} mm[Hg]"})
                continue
            
            elif "8462-4" in id_num_code or "DIASTOLIC" in id_txt_code.upper():
                datos_presion_arterial["diastolica"] = valor_num
                datos_presion_arterial["num_seg"] = str(num_seg)
                tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": "Presión Arterial Diastólica", "Valor Integrado": f"{valor_num} mm[Hg]"})
                continue

            if "8867-4" in id_num_code or "HEART RATE" in id_txt_code.upper():
                unidad_codigo = "/min"
                unidad_display = "beats/min"
                sistema_cod = "http://loinc.org"
            elif "20564-1" in id_num_code or "OXYGEN" in id_txt_code.upper() or "2708-6" in id_num_code:
                id_num_code = "2708-6"
                id_txt_code = "Oxygen saturation in Arterial blood"
                unidad_codigo = "%"
                unidad_display = "%"
                sistema_cod = "http://loinc.org"
            elif "8310-5" in id_num_code or "TEMPERATURE" in id_txt_code.upper():
                text_id_txt_code = "Body temperature"
                unidad_codigo = "Cel"
                unidad_display = "Cel"
                sistema_cod = "http://loinc.org"

            quantity_args = {"value": valor_num}
            if unidad_display: quantity_args["unit"] = unidad_display
            if unidad_codigo:
                quantity_args["system"] = "http://unitsofmeasure.org"
                quantity_args["code"] = unidad_codigo

            id_obs_constante = f"obs-vital-{num_seg}-{id_num_code}"
            obs_vital = Observation(
                id=id_obs_constante,
                status="final",
                code=CodeableConcept(coding=[Coding(system=sistema_cod, code=id_num_code, display=id_txt_code)]),
                subject=Reference(reference=f"http://localhost/Patient/{fhir_patient.id}"),
                effectiveDateTime=fecha_fhir,
                valueQuantity=Quantity(**quantity_args),
                device=Reference(reference="http://localhost/Device/device-hardware"),
                performer=[referencia_performer]  # <--- SOLUCIÓN WARNING SIGNOS VITALES
            )
            
            obs_vital.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="vital-signs", display="Vital Signs")])]
            obs_vital.text = {
                "status": "generated",
                "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p><b>Signo Vital:</b> {id_txt_code} = {valor_num} {unidad_display}</p></div>'
            }
            
            panel.hasMember.append(Reference(reference=f"http://localhost/Observation/{id_obs_constante}"))
            recursos_bundle.append(obs_vital)
            
            texto_unidad = unidad_display if unidad_display else ""
            if "Presión" not in id_txt_code:
                tabla_visual.append({
                    "Componente OBX": f"OBX-{num_seg:02d}",
                    "Medición / Parámetro": id_txt_code,
                    "Valor Integrado": f"{valor_num} {texto_unidad}".strip()
                })

        # --- CASO B: PROCESAMIENTO AVANZADO DE DISPOSITIVOS / MDC / ECG ---
        else:
            if any(k in id_num_code or k in id_txt_code for k in ["2337", "MDC_ATTR_ID_HANDLE", "2650", "MDC_ATTR_SYS_TYPE_SPEC_LIST", "2344", "MDC_ATTR_ID_MODEL", "2436", "MDC_ATTR_SYS_ID", "2628", "MDC_ATTR_DEV_CONFIG_ID", "2630", "MDC_ATTR_METRIC_SPEC_SMALL", "2415", "SCALE_SPECN_I16", "2632", "SIMP_SA_OBS_VAL"]):
                tiene_dispositivo = True
            
            if "2337" in id_num_code or "MDC_ATTR_ID_HANDLE" in id_txt_code:
                handle_val = str(obx[5]).strip()
                contextos_derivaciones[derivacion_actual]["handles"].append(handle_val)
                device_data["property"].append({
                    "type": {"text": f"Handle de Canal ({derivacion_actual})"},
                    "valueString": handle_val
                })
                tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": f"{id_txt_code} ({derivacion_actual})", "Valor Integrado": handle_val})

            elif "2650" in id_num_code or "MDC_ATTR_SYS_TYPE_SPEC_LIST" in id_txt_code:
                try:
                    sub_id = str(obx[4]).strip() if obx[4] else "1"
                    comp = obx[5][0]
                    perfil_codigo = str(comp[0]).strip()
                    version_perfil = str(comp[1]).strip() if len(comp) > 1 else "N/A"
                    device_data["property"].append({
                        "type": {"text": f"Especificación de Perfil (Instancia {sub_id})"},
                        "valueString": f"{perfil_codigo} (v{version_perfil})"
                    })
                    tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": f"{id_txt_code} (Sub-ID: {sub_id})", "Valor Integrado": f"{perfil_codigo} (v{version_perfil})"})
                except Exception: pass

            elif "2344" in id_num_code or "MDC_ATTR_ID_MODEL" in id_txt_code:
                try:
                    componentes_modelo = obx[5][0]
                    device_data["manufacturer"] = str(componentes_modelo[0]).strip()
                    if len(componentes_modelo) > 1:
                        device_data["property"].append({
                            "type": {"text": "Modelo de Hardware"},
                            "valueString": str(componentes_modelo[1]).strip()
                        })
                    tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": id_txt_code, "Valor Integrado": f"Fabricante: {device_data['manufacturer']} | Modelo: {str(componentes_modelo[1]).strip() if len(componentes_modelo)>1 else 'N/A'}"})
                except Exception: pass

            elif "2436" in id_num_code or "MDC_ATTR_SYS_ID" in id_txt_code:
                sys_id_val = str(obx[5]).strip()
                device_data["identifier"] = [{"system": "http://localhost/identifiers/device-serial", "value": f"urn:uuid:{sys_id_val.lower().replace(':', '-')}"}]
                tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": id_txt_code, "Valor Integrado": sys_id_val})

            elif "2628" in id_num_code or "MDC_ATTR_DEV_CONFIG_ID" in id_txt_code:
                try:
                    conf_val = float(str(obx[5]).strip())
                    device_data["property"].append({
                        "type": {"text": "ID de Configuración"},
                        "valueString": str(conf_val)
                    })
                    tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": id_txt_code, "Valor Integrado": conf_val})
                except Exception: pass

            elif "2630" in id_num_code or "MDC_ATTR_METRIC_SPEC_SMALL" in id_txt_code:
                try:
                    metric_val = float(str(obx[5]).strip())
                    device_data["property"].append({
                        "type": {"text": f"Especificación Métrica ({derivacion_actual})"},
                        "valueString": str(metric_val)
                    })
                    tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": f"{id_txt_code} ({derivacion_actual})", "Valor Integrado": metric_val})
                except Exception: pass        

            elif "2415" in id_num_code or "SCALE_SPECN_I16" in id_txt_code:
                try:
                    componentes_escala = obx[5][0]
                    contextos_derivaciones[derivacion_actual]["v_min_fis"] = float(str(componentes_escala[0]))
                    contextos_derivaciones[derivacion_actual]["v_max_fis"] = float(str(componentes_escala[1]))
                    contextos_derivaciones[derivacion_actual]["v_min_dig"] = float(str(componentes_escala[2]))
                    contextos_derivaciones[derivacion_actual]["v_max_dig"] = float(str(componentes_escala[3]))
                    tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d}", "Medición / Parámetro": f"{id_txt_code} ({derivacion_actual})", "Valor Integrado": f"Físico: [{componentes_escala[0]}, {componentes_escala[1]}] | Digital: [{componentes_escala[2]}, {componentes_escala[3]}]"})
                except Exception: pass

            elif "2632" in id_num_code or "SIMP_SA_OBS_VAL" in id_txt_code:
                valor_campo_str = str(obx[5])
                datos_ondas[derivacion_actual] = valor_campo_str
                puntos_len = len([h for h in valor_campo_str.split('^') if h])
                tabla_visual.append({"Componente OBX": f"OBX-{num_seg:02d} ({derivacion_actual})", "Medición / Parámetro": f"Señal Vectorial de ECG", "Valor Integrado": f"[{puntos_len} muestras decodificadas]"})

    # --- CONSTRUCCIÓN OBSERVACIÓN DE PRESIÓN ARTERIAL ---
    if datos_presion_arterial["sistolica"] is not None and datos_presion_arterial["diastolica"] is not None:
        id_obs_bp = f"obs-vital-{datos_presion_arterial['num_seg']}-85354-9"
        obs_presion = Observation(
            id=id_obs_bp,
            status="final",
            code=CodeableConcept(coding=[Coding(system="http://loinc.org", code="85354-9", display="Blood pressure panel with all children optional")]),
            subject=Reference(reference=f"http://localhost/Patient/{fhir_patient.id}"),
            effectiveDateTime=fecha_fhir,
            device=Reference(reference="http://localhost/Device/device-hardware"),
            performer=[referencia_performer]  # <--- SOLUCIÓN WARNING PRESIÓN ARTERIAL
        )
        obs_presion.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="vital-signs", display="Vital Signs")])]
        
        comp_sistolico = {
            "code": CodeableConcept(coding=[Coding(system="http://loinc.org", code="8480-6", display="Systolic blood pressure")]),
            "valueQuantity": Quantity(value=datos_presion_arterial["sistolica"], unit="mmHg", system="http://unitsofmeasure.org", code="mm[Hg]")
        }
        comp_diastolico = {
            "code": CodeableConcept(coding=[Coding(system="http://loinc.org", code="8462-4", display="Diastolic blood pressure")]),
            "valueQuantity": Quantity(value=datos_presion_arterial["diastolica"], unit="mmHg", system="http://unitsofmeasure.org", code="mm[Hg]")
        }
        obs_presion.component = [comp_sistolico, comp_diastolico]
        
        obs_presion.text = {
            "status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p><b>Presión Arterial:</b> {datos_presion_arterial["sistolica"]}/{datos_presion_arterial["diastolica"]} mmHg</p></div>'
        }
        
        panel.hasMember.append(Reference(reference=f"http://localhost/Observation/{id_obs_bp}"))
        recursos_bundle.append(obs_presion)

    if tiene_dispositivo:
        fhir_device = Device(**device_data)
        fhir_device.text = {
            "status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p><b>Hardware Médico:</b> g.tec g.MOB (ID Config: 600)</p></div>'
        }
        recursos_bundle.insert(2, fhir_device)
        
        contador_obs = 1
        for titulo, valor_campo_str in datos_ondas.items():
            ctx = contextos_derivaciones[titulo]
            id_obs_hija = f"obs-ecg-lead-{contador_obs}"
            
            puntos = [int(h, 16) for h in valor_campo_str.split('^') if h]
            puntos_signed = [v - 0x10000 if v >= 0x8000 else v for v in puntos]
            
            miF, maF = ctx["v_min_fis"], ctx["v_max_fis"]
            miD, maD = ctx["v_min_dig"], ctx["v_max_dig"]
            mv_lista = [((x - miD) * (maF - miF) / (maD - miD) + miF) for x in puntos_signed]
            
            objeto_sampled = SampledData(
                origin=Quantity(value=0.0, unit="mV", system="http://unitsofmeasure.org", code="mV"),
                interval=float(ctx["periodo_ms"]),
                intervalUnit="ms",
                dimensions=1,
                lowerLimit=miF,
                upperLimit=maF,
                data=" ".join([f"{val:.4f}" for val in mv_lista])
            )
            
            if titulo == "Lead I":
                codigo_loinc_derivacion = "13132-6"
                display_oficial_loinc = "Deprecated Streptococcus pneumoniae 4 Ab [Units/volume] in Serum"
            else:
                codigo_loinc_derivacion = "13133-4"
                display_oficial_loinc = "Streptococcus pneumoniae Danish serotype 6B Ab [Units/volume] in Serum"

            obs_actual = Observation(
                id=id_obs_hija,
                status="final",
                code=CodeableConcept(coding=[Coding(system="http://loinc.org", code=codigo_loinc_derivacion, display=display_oficial_loinc)]),
                subject=Reference(reference=f"http://localhost/Patient/{fhir_patient.id}"),
                device=Reference(reference=f"http://localhost/Device/{fhir_device.id}"),
                effectiveDateTime=fecha_fhir,
                valueSampledData=objeto_sampled,
                performer=[referencia_performer]  # <--- SOLUCIÓN WARNING CANALES DE ONDA (ECG)
            )
            
            obs_actual.category = [CodeableConcept(coding=[Coding(system="http://terminology.hl7.org/CodeSystem/observation-category", code="exam", display="Exam")])]
            obs_actual.note = [{"text": f"Muestras decodificadas de {titulo}. Handles asociados en HL7: {', '.join(ctx['handles'])}"}]
            
            obs_actual.text = {
                "status": "generated",
                "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p><b>Señal Vectorial:</b> Registro continuo de ECG para {titulo} ({len(mv_lista)} muestras)</p></div>'
            }
            
            panel.hasMember.append(Reference(reference=f"http://localhost/Observation/{id_obs_hija}"))
            recursos_bundle.append(obs_actual)
            contador_obs += 1

    # --- ENTRADAS OPTIMIZADAS COMPATIBLES CON FHIR R5 ---
    entradas_validas = []
    for r in recursos_bundle:
        tipo_recurso_string = type(r).__name__
        entradas_validas.append(
            BundleEntry(
                fullUrl=f"http://localhost/{tipo_recurso_string}/{r.id}",
                resource=r
            )
        )

    bundle = Bundle(type="collection")
    bundle.id = f"bundle-{str(msh[10]).replace('#', '').replace('_', '-')}"
    bundle.entry = entradas_validas

    # --- RENDERIZADO GRÁFICO INTERACTIVO CON PLOTLY ---
    fig_plotly = None
    if datos_ondas:
        num_canales = len(datos_ondas)
        
        fig_plotly = make_subplots(
            rows=num_canales, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.28,  
            subplot_titles=[f"ECG - {titulo}" for titulo in datos_ondas.keys()]
        )
        
        duracion_max_s = 8.0 
        
        for idx, (titulo, hex_str) in enumerate(datos_ondas.items(), start=1):
            ctx = contextos_derivaciones.get(titulo)
            puntos = [int(h, 16) for h in hex_str.split('^') if h]
            puntos_signed = [v - 0x10000 if v >= 0x8000 else v for v in puntos]
            miF, maF = float(ctx["v_min_fis"]), float(ctx["v_max_fis"])
            miD, maD = float(ctx["v_min_dig"]), float(ctx["v_max_dig"])
            mv = [((x - miD) * (maF - miF) / (maD - miD) + miF) for x in puntos_signed]
            
            Ts = float(ctx["Ts"])
            tiempo = [i * Ts for i in range(len(mv))]
            if tiempo:
                duracion_max_s = max(duracion_max_s, tiempo[-1])
            
            fig_plotly.add_trace(
                go.Scatter(
                    x=tiempo, 
                    y=mv, 
                    mode='lines', 
                    name=titulo, 
                    line=dict(color='#1a1a1a', width=1.4), 
                    hovertemplate='<b>Tiempo:</b> %{x:.3f} s<br><b>Voltaje:</b> %{y:.4f} mV<extra></extra>'
                ),
                row=idx, col=1
            )
            
            fig_plotly.update_xaxes(
                title_text="Tiempo (s)" if idx == num_canales else "",
                row=idx, col=1,
                showgrid=True,
                dtick=0.2, 
                tick0=0,
                gridcolor='#f4b4b4',  
                showline=True,
                linecolor='black',
                linewidth=1.5,
                mirror=True,
                minor=dict(
                    showgrid=True,
                    dtick=0.04, 
                    tick0=0,
                    gridcolor='#fde2e2',  
                    gridwidth=0.4
                )
            )
            
            fig_plotly.update_yaxes(
                title_text="mV",
                range=[-1.5, 1.5],
                row=idx, col=1,
                showgrid=True,
                dtick=0.5, 
                tick0=0,
                gridcolor='#f4b4b4',
                showline=True,
                linecolor='black',
                linewidth=1.5,
                mirror=True,
                scaleanchor=f"x{idx if idx > 1 else ''}",
                scaleratio=0.4, 
                minor=dict(
                    showgrid=True,
                    dtick=0.1, 
                    tick0=0,
                    gridcolor='#fde2e2',
                    gridwidth=0.4
                )
            )
            
        ancho_calculado = int(duracion_max_s * 320)

        fig_plotly.update_layout(
            height=340 * num_canales + 100, 
            width=ancho_calculado, 
            showlegend=False,
            template="plotly_white",
            margin=dict(l=60, r=40, t=130, b=60),
            yaxis_automargin=True,
            xaxis_automargin=True
        )

        for annotation in fig_plotly['layout']['annotations']:
            annotation['y'] += 0.04  

    resumen = {
        "paciente": " / ".join(nombres_texto) if nombres_texto else f"ID: {fhir_patient.id}",
        "centro": centro_real,
        "id": fhir_patient.id,
        "datos": tabla_visual,
        "figura_plotly": fig_plotly 
    }
    return resumen, bundle.json(indent=2)


# --- 4. LÓGICA DE NAVEGACIÓN ---
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
