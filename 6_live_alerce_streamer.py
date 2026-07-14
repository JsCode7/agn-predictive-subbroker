from alerce.core import Alerce
import pandas as pd
import json
import time
from confluent_kafka import Producer

def live_stream():
    client = Alerce()
    producer = Producer({'bootstrap.servers': 'localhost:9092'})
    topic = 'lightcurves'
    
    print("Conectando con la API de ALeRCE (ZTF)...")
    print("Buscando los objetos más recientes observados en el universo...")
    
    # Query AGNs and Stars separately to prevent API timeouts (502 Error)
    try:
        agn_objects = client.query_objects(
            classifier="lc_classifier",
            class_name="AGN",
            page_size=10,
            order_by="lastmjd",
            order_dir="DESC"
        )
        
        star_objects = client.query_objects(
            classifier="lc_classifier",
            class_name="Star",
            page_size=3,
            order_by="lastmjd",
            order_dir="DESC"
        )
        
        # Combine the lists safely
        objects_list = []
        if agn_objects is not None and not agn_objects.empty:
            objects_list.append(agn_objects)
        if star_objects is not None and not star_objects.empty:
            objects_list.append(star_objects)
            
        if not objects_list:
            print("No live objects found.")
            return
            
        objects = pd.concat(objects_list, ignore_index=True)
        
    except Exception as e:
        print(f"ALeRCE API Error: {e}")
        return
        
    oids = objects['oid'].tolist()
    print(f"Encontrados {len(oids)} objetos frescos. Descargando su historial de curvas de luz...")
    
    all_detections = []
    for oid in oids:
        try:
            lc = client.query_lightcurve(oid)
            df = pd.DataFrame(lc['detections'])
            if not df.empty:
                df['oid'] = oid
                all_detections.append(df)
        except Exception as e:
            print(f"Error fetching {oid}: {e}")
            
    if not all_detections:
        return
        
    combined_df = pd.concat(all_detections, ignore_index=True)
    if 'mjd' in combined_df.columns:
        # Sort chronologically to stream them naturally
        combined_df = combined_df.sort_values(by='mjd')
        
    print(f"Iniciando el LIVE STREAMING de {len(combined_df)} fotones/puntos a Kafka...")
    for index, row in combined_df.iterrows():
        record = row.to_dict()
        key = str(record['oid'])
        value = json.dumps(record)
        
        producer.produce(topic, key=key.encode('utf-8'), value=value.encode('utf-8'))
        producer.poll(0)
        
        # Micro-delay to simulate live data arriving point by point
        time.sleep(0.02)
        
    producer.flush()
    print("Live streaming completado. Estos son datos reales y frescos.")

if __name__ == "__main__":
    live_stream()
