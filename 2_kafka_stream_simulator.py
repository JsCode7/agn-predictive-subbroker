import pandas as pd
import json
import time
from confluent_kafka import Producer

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    # else:
    #     print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def simulate_stream():
    conf = {'bootstrap.servers': 'localhost:9092'}
    producer = Producer(conf)
    topic = 'lightcurves'

    print("Loading data...")
    try:
        df = pd.read_csv('data/lightcurves.csv')
    except FileNotFoundError:
        print("Data not found. Please run 1_fetch_alerce_data.py first.")
        return
        
    print("Simulating stream...")
    for index, row in df.iterrows():
        record = row.to_dict()
        
        # Use OID as the key to ensure the same object goes to the same partition
        key = str(record['oid'])
        value = json.dumps(record)
        
        producer.produce(topic, key=key.encode('utf-8'), value=value.encode('utf-8'), callback=delivery_report)
        producer.poll(0)
        
        # Simulate real-time delay
        time.sleep(0.001)

    producer.flush()
    print("Simulation complete.")

if __name__ == "__main__":
    simulate_stream()
