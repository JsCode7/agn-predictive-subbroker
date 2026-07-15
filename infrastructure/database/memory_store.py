import asyncio
import time
from typing import Dict, Any

class MemoryStore:
    def __init__(self, ttl_seconds=3600, max_points=5000):
        self.store: Dict[str, Any] = {}
        self.ttl = ttl_seconds
        self.max_points = max_points
        self.lock = asyncio.Lock()

    async def add_point(self, oid, mjd, mag, magerr, class_name=None):
        async with self.lock:
            if oid not in self.store:
                self.store[oid] = {'t': [], 'y': [], 'yerr': [], 'class_name': class_name, 'last_updated': time.time()}
            
            self.store[oid]['t'].append(mjd)
            self.store[oid]['y'].append(mag)
            self.store[oid]['yerr'].append(magerr)
            self.store[oid]['last_updated'] = time.time()
            if class_name:
                self.store[oid]['class_name'] = class_name
            
            if len(self.store[oid]['t']) > self.max_points:
                self.store[oid]['t'].pop(0)
                self.store[oid]['y'].pop(0)
                self.store[oid]['yerr'].pop(0)

    async def get_data(self, oid):
        async with self.lock:
            if oid in self.store:
                return dict(self.store[oid])
            return None

    async def cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            async with self.lock:
                now = time.time()
                expired = [oid for oid, data in self.store.items() if now - data['last_updated'] > self.ttl]
                for oid in expired:
                    del self.store[oid]
                if expired:
                    print(f"MemoryStore: Evicted {len(expired)} idle objects.")

memory_store = MemoryStore()
