import os
import pandas as pd
from alerce.core import Alerce
from tqdm import tqdm

def fetch_lightcurves(client, class_name, num_objects=5000):
    print(f"Fetching {num_objects} objects for class: {class_name}")
    # We may need to paginate to get 5000 objects
    page_size = min(500, num_objects)
    total_pages = max(1, num_objects // page_size)
    
    oids = []
    for i in tqdm(range(1, total_pages + 1), desc="Fetching OIDs"):
        objects = client.query_objects(
            classifier="lc_classifier", 
            class_name=class_name, 
            page_size=page_size, 
            page=i
        )
        if objects is not None and not objects.empty and 'oid' in objects.columns:
            oids.extend(objects['oid'].tolist())
        else:
            print(f"No objects or missing 'oid' for class {class_name} on page {i}")
        
    print(f"Fetched {len(oids)} OIDs. Now fetching lightcurves...")
    
    lcs = []
    for oid in tqdm(oids, desc=f"Fetching lightcurves for {class_name}"):
        try:
            lc = client.query_lightcurve(oid)
            detections = pd.DataFrame(lc['detections'])
            if not detections.empty:
                detections['oid'] = oid
                detections['class_name'] = class_name
                lcs.append(detections)
        except Exception as e:
            # Handle potential API errors gracefully
            print(f"Error fetching {oid}: {e}")
            
    if lcs:
        return pd.concat(lcs, ignore_index=True)
    return pd.DataFrame()

if __name__ == "__main__":
    client = Alerce()
    
    # Fetch data
    agn_df = fetch_lightcurves(client, "AGN", 10)
    star_df = fetch_lightcurves(client, "Star", 10)
    
    # Combine and save
    combined_df = pd.concat([agn_df, star_df], ignore_index=True)
    
    # Sort by time (mjd) to simulate realistic streaming later
    if 'mjd' in combined_df.columns:
        combined_df = combined_df.sort_values(by='mjd')
        
    os.makedirs('data', exist_ok=True)
    output_path = 'data/lightcurves.csv'
    combined_df.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}")
