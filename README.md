# AGN Predictive Sub-Broker: Real-Time ZTF Data Streaming

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch)
![Kafka](https://img.shields.io/badge/Kafka-231F20?style=flat&logo=apachekafka)

Un sub-broker astronómico diseñado para la ingesta, agregación en tiempo real y clasificación estocástica de **Núcleos Galácticos Activos (AGNs) vs. Estrellas Variables**. El sistema procesa alertas del *Zwicky Transient Facility* (ZTF) distribuidas por el broker ALeRCE.

## 🔭 ¿Qué problema resuelve?
Los brokers principales procesan millones de alertas genéricas. Este **Sub-Broker** actúa como un filtro especializado que:
1. **Ingiere Fotones en Vivo:** Intercepta datos astronómicos asincrónicos.
2. **Stateful Aggregation:** Agrupa fotones por su OID y filtro óptico (Bandas *g* y *r*) en memoria RAM.
3. **Inferencia Termodinámica:** Aplica un modelo de caminata aleatoria amortiguada (Damped Random Walk - DRW) programado en tensores de PyTorch para extraer las variables físicas del disco de acreción del Agujero Negro ($Tau$ y $Sigma$) en milisegundos.

## 🏗️ Arquitectura de la Solución

- **Message Broker:** Apache Kafka (KRaft mode) desplegado vía Docker.
- **Microservicio & WebSockets:** `FastAPI` actúa como el consumidor de Kafka, mantiene el estado de las curvas de luz y expone un WebSocket de alta velocidad.
- **Machine Learning Engine:** Un modelo generativo (`torch.nn.Module`) que usa el optimizador *Adam* para ajustar las curvas e inferir parámetros astrofísicos asintóticos.
- **Frontend Asíncrono:** Una interfaz gráfica libre de dependencias (Vanilla JS + Chart.js) con mitigación de re-renderizado vía `requestAnimationFrame` y mitigación de cuellos de botella del DOM.

## 📁 Estructura del Proyecto
El código está modularizado para ser comprensible por equipos multidisciplinarios (Data Engineers y Astrofísicos):

* `1_fetch_alerce_data.py`: Script para minar datos históricos de la API de ALeRCE y preparar datasets locales (`data/`).
* `2_kafka_stream_simulator.py`: Inyecta el dataset local a Kafka a alta velocidad para pruebas de estrés y simulación.
* `4_pytorch_drw_model.py`: La matemática pura. Modelo termodinámico de tensores en PyTorch.
* `5_fastapi_websockets.py`: El corazón del backend. Une Kafka, PyTorch y los WebSockets web.
* `6_live_alerce_streamer.py`: Intercepta los últimos eventos captados por el observatorio (Polling REST) y los inyecta al pipeline.
* `7_production_firehose_bridge.py`: Plantilla de arquitectura para conectarse directamente al streaming binario oficial (Apache Avro) de ALeRCE.
* `docker-compose.yml`: Infraestructura (Kafka + Postgres).
* `frontend/`: Interfaz de usuario (HTML/CSS/JS).

## 🚀 Instalación y Despliegue

### Requisitos Previos
* Docker y Docker Compose
* Python 3.10+

### Paso 1: Levantar la Infraestructura
```bash
docker-compose up -d
```

### Paso 2: Entorno Virtual y Dependencias
```bash
python -m venv venv
# Activar entorno (Windows)
.\venv\Scripts\activate
# Activar entorno (Linux/Mac)
source venv/bin/activate

pip install -r requirements.txt
```

### Paso 3: Inicializar el Backend (PyTorch + WebSockets)
```bash
uvicorn 5_fastapi_websockets:app --reload --host 0.0.0.0 --port 8000
```
> 👉 **Abre tu navegador en:** [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

### Paso 4: Inyectar la Luz Estelar
En otra consola, ejecuta cualquiera de los siguientes motores:
- **Simulación Masiva:** `python 2_kafka_stream_simulator.py`
- **Telescopio en Vivo (Reciente):** `python 6_live_alerce_streamer.py`

## 🧠 Glosario Astrofísico
- **MJD (Modified Julian Date):** Reloj absoluto que cuenta los días continuos, esencial para matemáticas orbitales precisas.
- **Magnitud (magpsf):** Escala logarítmica invertida de brillo (números menores implican mayor flujo lumínico).
- **Tau [días]:** Tiempo de relajación térmica. Memoria a largo plazo de las erupciones del agujero negro. Un $Tau$ muy alto delata un Agujero Negro Supermasivo.
- **Sigma [mag / √día]:** Razón de la variabilidad estocástica a largo plazo del disco de acreción.
- **Bandas ZTF:** Los colores de captura. `g-band` (Verde) y `r-band` (Roja).

## 📄 Licencia
Este proyecto se distribuye bajo la licencia **MIT**, permitiendo a cualquier institución científica su libre modificación y uso comercial o académico.
