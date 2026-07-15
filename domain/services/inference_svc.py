import asyncio
from concurrent.futures import ThreadPoolExecutor
from domain.ml.drw_model import infer_parameters
from domain.ml.classifier import classifier
from infrastructure.database.memory_store import memory_store
from infrastructure.database.postgres import db_manager
from api.websockets.router import broadcast_json

executor = ThreadPoolExecutor(max_workers=4)

def drw_inference_task(t, y, yerr):
    return infer_parameters(t, y, yerr, epochs=40)

async def process_lightcurve_message(oid, mjd, mag, magerr, class_name, fid):
    await memory_store.add_point(oid, mjd, mag, magerr, class_name)
    
    point_data = {
        "oid": str(oid),
        "mjd": mjd,
        "mag": mag,
        "fid": fid
    }
    await broadcast_json({"type": "point", "data": point_data})
            
    obj_data = await memory_store.get_data(oid)
    if obj_data:
        n_points = len(obj_data['t'])
        if n_points >= 15 and n_points % 15 == 0:
            loop = asyncio.get_running_loop()
            tau, sigma = await loop.run_in_executor(
                executor, 
                drw_inference_task, 
                obj_data['t'], obj_data['y'], obj_data['yerr']
            )
            
            real_class_name = obj_data.get('class_name')
            if real_class_name:
                true_label = 1 if real_class_name == "AGN" else 0
            else:
                true_label = 1 if tau > 5.0 else 0
            
            pred, prob, metrics = await classifier.predict_and_score(tau, sigma, n_points, true_label)
            await classifier.partial_fit(tau, sigma, n_points, true_label)
            
            classification = "AGN" if pred == 1 else "Star"
            
            pred_data = {
                "oid": oid,
                "tau": round(tau, 3),
                "sigma": round(sigma, 4),
                "classification": classification,
                "probability": round(prob, 3),
                "n_points": n_points,
                "metrics": metrics
            }
            
            await broadcast_json({"type": "prediction", "data": pred_data})
            
            await loop.run_in_executor(
                executor,
                db_manager.save_inference,
                oid, tau, sigma, n_points, classification
            )
