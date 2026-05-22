# Plataforma de Interoperabilidad de mensajes de observación HL7 v2 → FHIR R5 con Procesamiento ECG <img src='Logo_UPNA-1.png' align="right" />

## Descripción General

Este proyecto implementa una plataforma de interoperabilidad clínica capaz de transformar mensajes HL7 v2 en recursos estructurados FHIR R4, incorporando además la reconstrucción y visualización de señales electrocardiográficas (ECG) contenidas dentro de los segmentos de observación del mensaje HL7.

El sistema combina:

* Procesamiento y parsing de mensajes HL7 v2
* Generación automática de recursos FHIR en formato JSON
* Decodificación de señales ECG
* Reconstrucción biomédica de señales fisiológicas
* Visualización interactiva de electrocardiogramas

La aplicación ha sido desarrollada en Python y desplegada mediante Streamlit.

---

# Funcionalidades Principales

## Procesamiento de Mensajes HL7 v2

La plataforma analiza automáticamente mensajes clínicos HL7 v2 y separa sus segmentos principales:

* MSH
* PID
* OBR
* OBX

A partir de estos segmentos, el sistema extrae información clínica estructurada que posteriormente es transformada al modelo FHIR.

---

# Transformación HL7 v2 → FHIR

El sistema implementa una correspondencia semántica entre los segmentos HL7 v2 y los recursos equivalentes definidos en FHIR R4.

| Segmento HL7 v2 | Recurso FHIR                 |
| --------------- | ---------------------------- |
| MSH             | Bundle                       |
| PID             | Patient                      |
| OBR             | Observation Panel            |
| OBX (NM)        | Observation.valueQuantity    |
| OBX (TX/ST)     | Observation.valueString      |
| OBX ECG         | Observation.valueSampledData |

Todos los recursos generados son agrupados dentro de un único recurso FHIR Bundle.

---

# Tecnologías Utilizadas

| Tecnología     | Función                  |
| -------------- | ------------------------ |
| Python         | Implementación principal |
| Streamlit      | Aplicación web           |
| HL7 Parser     | Procesamiento HL7 v2     |
| FHIR Resources | Modelado FHIR            |
| Plotly         | Visualización ECG        |
| ISO/IEEE 11073 | Nomenclatura biomédica   |

---

# Instalación

## Clonar repositorio

```bash
git clone <(https://github.com/JuliaArellano/Interoperabilidad.git)>
cd <nombre_repositorio>
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

# Aplicaciones del Proyecto

Este proyecto está orientado a:

* Investigación en interoperabilidad clínica
* Procesamiento de señales biomédicas
* Estudios HL7/FHIR
* Estandarización de datos ECG
* Desarrollo de prototipos sanitarios
* Entornos educativos y académicos

---

# Observaciones

La implementación se centra en la interoperabilidad clínica y la reconstrucción de señales ECG contenidas en mensajes HL7 v2. No pretende implementar completamente el estándar ISO/IEEE 11073, sino utilizar atributos compatibles con dicha nomenclatura para representar información biomédica y metadatos clínicos.

---

# Autor

Julia Arellano Atienza y Lorena Calvo Peréz

Máster Ingeniería Biomédica (UPNA)
