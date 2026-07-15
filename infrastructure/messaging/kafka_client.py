import asyncio
import json
from confluent_kafka import Consumer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_GROUP, KAFKA_TOPIC
from domain.services.inference_svc import process_lightcurve_message, executor

msg_queue = asyncio.Queue(maxsize=1000)

async def consume_kafka():
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })
    consumer.subscribe([KAFKA_TOPIC])
    loop = asyncio.get_running_loop()
    
    while True:
        msg = await loop.run_in_executor(executor, consumer.poll, 0.1)
        
        if msg is None:
            await asyncio.sleep(0.01)
            continue
            
        if msg.error():
            print(f"Kafka error: {msg.error()}")
            continue
            
        await msg_queue.put((msg.value(), msg.offset()))
        
        def _commit():
            consumer.commit(message=msg, asynchronous=False)
        await loop.run_in_executor(executor, _commit)

async def worker_loop():
    while True:
        msg_value, msg_offset = await msg_queue.get()
        try:
            data = json.loads(msg_value.decode('utf-8'))
            oid = data['oid']
            mjd = float(data.get('mjd', 0) or 0)
            mag = float(data.get('magpsf', 0) or 0)
            magerr = float(data.get('sigmapsf', 0) or 0)
            class_name = data.get('class_name')
            fid = int(data.get('fid', 1) or 1)
            
            await process_lightcurve_message(oid, mjd, mag, magerr, class_name, fid)
        except Exception as e:
            print(f"Error processing message offset {msg_offset}: {e}")
        finally:
            msg_queue.task_done()
