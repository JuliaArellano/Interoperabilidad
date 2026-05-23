<table>
  <tr>
    <td>
      <h1>
        Plataforma de Interoperabilidad de mensajes ORU HL7 v2 → FHIR R5 con Procesamiento ECG
      </h1>
    </td>
    <td align="right">
      <img src="Logo_UPNA-1.png" width="140">
    </td>
  </tr>
</table>

## Descripción General

Este proyecto implementa una plataforma de interoperabilidad clínica capaz de transformar mensajes HL7 v2.6 en recursos estructurados FHIR R5, incorporando además la reconstrucción y visualización de señales electrocardiográficas (ECG) contenidas dentro de los segmentos de observación del mensaje HL7.

El sistema combina:

* Procesamiento y parsing de mensajes HL7 v2
* Generación automática de recursos FHIR en formato JSON
* Decodificación de señales ECG
* Reconstrucción biomédica de señales fisiológicas
* Visualización interactiva de electrocardiogramas

La aplicación ha sido desarrollada en Python y desplegada mediante Streamlit.

---

# Transformación HL7 v2 → FHIR

El sistema implementa una correspondencia semántica entre los segmentos HL7 v2 y los recursos equivalentes definidos en FHIR R5.

| Segmento HL7 v2 | Recurso FHIR                 |
| --------------- | ---------------------------- |
| MSH             | Bundle                       |
| PID             | Patient                      |
| OBR             | Observation Panel            |
| OBX (NM)        | Observation.valueQuantity    |
| OBX (TX/ST)     | Observation.valueString      |
| OBX ECG         | Observation.valueSampledData |

Todos los recursos generados son agrupados dentro de un único recurso FHIR Bundle.


# Instalación

## Clonar repositorio

```bash
git clone (https://github.com/JuliaArellano/Interoperabilidad.git)
cd Interoperabilidad/app.py
```

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar aplicación Streamlit

```bash
streamlit run app.py
```

---
## Aplicación Web

La plataforma puede probarse directamente desde Streamlit Cloud:

👉 **https://conversionfhir.streamlit.app/**


# Observaciones

La implementación se centra en la interoperabilidad clínica y la reconstrucción de señales ECG contenidas en mensajes HL7 v2.6. No pretende implementar completamente el estándar ISO/IEEE 11073, sino utilizar atributos compatibles con dicha nomenclatura para representar información biomédica y metadatos clínicos.

---

# Autor

Julia Arellano Atienza y Lorena Calvo Peréz

Máster Ingeniería Biomédica (UPNA)
