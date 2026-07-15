# AGN Predictive Sub-Broker: Real-Time ZTF Data Streaming

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch)
![Kafka](https://img.shields.io/badge/Kafka-231F20?style=flat&logo=apachekafka)

Un sub-broker astronómico diseñado para la ingesta, agregación temporal estocástica en tiempo real y clasificación de **Núcleos Galácticos Activos (AGNs) vs. Estrellas Variables** empleando algoritmos de Aprendizaje Continuo (Continuous Learning). El sistema procesa flujos de fotometría óptica del *Zwicky Transient Facility* (ZTF) distribuidas por el broker oficial ALeRCE.

## 🔭 Relevancia Científica
Los brokers principales procesan millones de alertas genéricas. Este **Sub-Broker** actúa como un filtro topológico especializado para Astrofísica que:
1. **Ingiere Fotones Asíncronos:** Intercepta datos astronómicos asincrónicos irregulares en múltiples bandas fotométricas.
2. **Inferencia Termodinámica:** Aplica un modelo de **Caminata Aleatoria Amortiguada** (Damped Random Walk - DRW) parametrizado en tensores de PyTorch para inferir asintóticamente las características del disco de acreción: la variabilidad a largo plazo ($\sigma$) y el tiempo de relajación de decaimiento temporal ($\tau$).
3. **Clasificación Estocástica Continua:** Desacoplado de heurísticas estáticas, se entrena progresivamente (Incremental Learning) utilizando Descenso de Gradiente Estocástico (SGD) empleando la entropía cruzada (`log_loss`) sobre las variables extraídas de las curvas de luz asincrónicas, contrastándolas en tiempo real contra catálogos validados de ALeRCE.

## 🏗️ Arquitectura Hexagonal y de Patrones (SOLID)
El código base sigue una estructura de Puertos y Adaptadores, garantizando resiliencia y separación total de responsabilidades.

- **`core/`**: Parámetros globales y esquemas estáticos de configuración.
- **`infrastructure/`**: Comunicación transaccional con la capa externa. Contiene el consumidor asíncrono con **Backpressure** de Apache Kafka, un Gestor de Memoria en RAM por fotones transitorios (Ring Buffer y control de TTL concurrente), y un Connection Pool (`psycopg2`) vinculado a esquemas duales PostgreSQL (Historia y Estado).
- **`domain/`**: Corazón de la inferencia. Integra el modelo PyTorch, la topología incremental del SGDClassifier y la orquestación lógica (`inference_svc.py`).
- **`api/`**: La capa perimetral web (FastAPI) que desacopla el ecosistema WebSocket.
- **`scripts/`**: Utilitarios heredados para recolección de minería de datos y simulaciones *Firehose*.

## 🚀 Despliegue en Entorno de Producción

### Requisitos Previos
* Docker, Docker Compose y Python 3.10+

### Levantando Infraestructura Externa
```bash
docker-compose up -d
```
*(Incluye Apache Kafka en modo KRaft y TimescaleDB/PostgreSQL).*

### Inicializando Servidor de Inferencia (Backend)
Desde la raíz del repositorio y con el entorno virtual activado (`venv`):
```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
> 👉 **Monitor Visual:** Abre tu navegador en [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

### Inyectando Data Astronómica (Firehose)
Para simular un streaming masivo validado contra catálogo:
```bash
python scripts/2_kafka_stream_simulator.py
```

## 🧠 Parámetros Físicos Extractados
- **MJD (Modified Julian Date):** Reloj absoluto continuo.
- **Magnitud (magpsf):** Escala logarítmica invertida de flujo lumínico.
- **Tau [días]:** Tiempo de relajación térmica. La memoria a largo plazo de erupciones transitorias estocásticas del disco.
- **Sigma [mag / √día]:** Razón de variabilidad estocástica a largo plazo (ruido fotométrico intrínseco).
- **ROC-AUC & Entropía Cruzada:** Métricas de fiabilidad probabilística calculadas en el modelo clasificatorio subyacente.

## 📄 Licencia
Este proyecto se distribuye bajo la licencia **MIT**, permitiendo a cualquier institución científica su libre modificación y uso comercial o académico.
