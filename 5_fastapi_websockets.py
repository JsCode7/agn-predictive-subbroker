import asyncio
import json
import importlib.util
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from confluent_kafka import Consumer

# Load PyTorch DRW Model module dynamically due to numeric filename
spec = importlib.util.spec_from_file_location("drw_model", "4_pytorch_drw_model.py")
drw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drw)

app = FastAPI(title="AGN Sub-Broker MVP")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

async def consume_kafka():
    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'fastapi-backend-group-demo',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['lightcurves'])
    
    memory_store = {}
    
    while True:
        # Avoid blocking the event loop
        msg = consumer.poll(0.01)
        if msg is None:
            await asyncio.sleep(0.05)
            continue
        if msg.error():
            continue
            
        data = json.loads(msg.value().decode('utf-8'))
        oid = data['oid']
        
        if oid not in memory_store:
            memory_store[oid] = {'t': [], 'y': [], 'yerr': []}
            
        memory_store[oid]['t'].append(data['mjd'])
        memory_store[oid]['y'].append(data['magpsf'])
        memory_store[oid]['yerr'].append(data['sigmapsf'])
        
        # Clean payload to prevent NaN/Infinity JSON parsing errors in JS
        point_data = {
            "oid": str(oid),
            "mjd": float(data.get('mjd', 0) or 0),
            "mag": float(data.get('magpsf', 0) or 0),
            "fid": int(data.get('fid', 1) or 1)
        }
        
        for client in clients:
            try:
                await client.send_json({"type": "point", "data": point_data})
            except:
                pass
            
        # Rate limit to simulate streaming and prevent browser freeze
        await asyncio.sleep(0.02)
        
        n_points = len(memory_store[oid]['t'])
        if n_points >= 15 and n_points % 15 == 0:
            t = memory_store[oid]['t']
            y = memory_store[oid]['y']
            yerr = memory_store[oid]['yerr']
            
            try:
                tau, sigma = drw.infer_parameters(t, y, yerr, epochs=40)
                is_agn = tau > 5.0
                
                pred_data = {
                    "oid": oid,
                    "tau": round(tau, 3),
                    "sigma": round(sigma, 4),
                    "classification": "AGN" if is_agn else "Star",
                    "n_points": n_points
                }
                for client in clients:
                    await client.send_json({"type": "prediction", "data": pred_data})
            except Exception as e:
                print("Error in DRW inference:", e)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_kafka())
