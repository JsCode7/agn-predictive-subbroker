import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sys
import os

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.websockets.router import router as websocket_router
from infrastructure.database.postgres import db_manager
from infrastructure.database.memory_store import memory_store
from infrastructure.messaging.kafka_client import consume_kafka, worker_loop
from domain.services.inference_svc import executor

app = FastAPI(title="AGN Sub-Broker MVP - Clean Architecture")

app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.include_router(websocket_router)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, db_manager.init_db)
    
    asyncio.create_task(memory_store.cleanup_loop())
    asyncio.create_task(consume_kafka())
    
    for _ in range(4):
        asyncio.create_task(worker_loop())
