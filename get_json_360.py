import requests
import json
import os
import time
from datetime import datetime

# API and base URL
API_URL = "https://api.polyhaven.com"

# Add a user agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_asset_list():
    """Get list of all HDRIs with their metadata"""
    try:
        # First get the list of all assets
        response = requests.get(f"{API_URL}/assets", headers=HEADERS, params={'t': 'hdris'})
        response.raise_for_status()
        
        # The API returns a dictionary of assets where the key is the asset ID
        all_assets = response.json()
        
        # Filter for HDRI assets only (type 0 is HDRI in the API)
        hdri_assets = {}
        for asset_id, asset_data in all_assets.items():
            if isinstance(asset_data, dict) and asset_data.get('type') == 0:
                hdri_assets[asset_id] = "hdri"
        
        print(f"🔎 Found {len(hdri_assets)} HDRIs")
        
        # Debug: Print first few asset IDs if any found
        if hdri_assets:
            sample_ids = list(hdri_assets.keys())[:3]
            print(f"Sample HDRI IDs: {sample_ids}")
        
        return hdri_assets
    except Exception as e:
        print(f"⚠️ API Error in get_asset_list(): {e}")
        if 'response' in locals() and hasattr(response, 'status_code'):
            print(f"Response status code: {response.status_code}")
            if hasattr(response, 'text'):
                print(f"Response text: {response.text[:200]}...")
        return []

def get_asset_info(asset_id, max_retries=3):
    """Get detailed information about a specific asset with retry logic"""
    for attempt in range(max_retries):
        try:
            # First get the asset info
            info_url = f"{API_URL}/info/{asset_id}"
            response = requests.get(info_url, headers=HEADERS, timeout=10)
            
            # If asset not found, try with _4k suffix
            if response.status_code == 404:
                print(f"ℹ️  Asset not found, trying with _4k suffix: {asset_id}")
                asset_id = f"{asset_id}_4k"
                info_url = f"{API_URL}/info/{asset_id}"
                response = requests.get(info_url, headers=HEADERS, timeout=10)
            
            if response.status_code == 404:
                print(f"❌ Asset not found: {asset_id}")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            # Get the files info
            files_url = f"{API_URL}/files/{asset_id}"
            files_response = requests.get(files_url, headers=HEADERS, timeout=10)
            files_data = files_response.json() if files_response.status_code == 200 else {}
            
            # Extract resolution from files data if available
            max_res = [0, 0]
            if 'hdri' in files_data:
                for res, formats in files_data['hdri'].items():
                    for format_name, file_info in formats.items():
                        if 'resolution' in file_info and file_info['resolution']:
                            w, h = file_info['resolution']
                            if w * h > max_res[0] * max_res[1]:
                                max_res = [w, h]
            
            # Get author information
            authors = {}
            if 'authors' in data:
                for author, role in data['authors'].items():
                    authors[author] = role
            
            # Format the asset information
            asset_info = {
                "name": data.get('name', asset_id.replace('_', ' ').title()),
                "type": 0,  # 0 for HDRI
                "date_published": data.get('date_published', 0),
                "download_count": data.get('download_count', 0),
                "files_hash": data.get('files_hash', ''),
                "authors": authors or {"Unknown": "All"},
                "categories": data.get('categories', []),
                "tags": data.get('tags', []),
                "max_resolution": max_res if max_res != [0, 0] else [8192, 4096],
                "dimensions": [30000, 30000],  # Default dimensions
                "thumbnail_url": data.get('thumbnail_url', f"https://cdn.polyhaven.com/asset_img/thumbs/{asset_id}.png?width=256&height=256")
            }
            
            return asset_info
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"⚠️ Failed to fetch {asset_id} after {max_retries} attempts: {e}")
                return None
            print(f"↩️  Retrying {asset_id} (attempt {attempt + 1}/{max_retries})...")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Unexpected error with {asset_id}: {e}")
            return None

def save_to_json(data, filename='hdri_metadata.json'):
    """Save the collected data to a JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved metadata to {filename}")
        return True
    except Exception as e:
        print(f"⚠️ Error saving to JSON: {e}")
        return False

def main():
    # Get all HDRI metadata
    print("🚀 Starting HDRI metadata collection...")
    hdri_assets = get_asset_list()
    
    if not hdri_assets:
        print("❌ No HDRI assets found")
        return
    
    # Process the assets
    assets_data = {}
    total_assets = len(hdri_assets)
    processed = 0
    
    # Process all assets (remove [:] to process all)
    for idx, (asset_id, _) in enumerate(list(hdri_assets.items())[:843], 1):
        print(f"\n📡 Processing {idx}/{total_assets}: {asset_id}")
        asset_info = get_asset_info(asset_id)
        
        if asset_info:
            assets_data[asset_id] = asset_info
            processed += 1
            print(f"✅ Fetched: {asset_info['name']}")
        else:
            print(f"❌ Failed to fetch: {asset_id}")
        
        # Be nice to the API with a delay
        time.sleep(1)  # Increased delay to 1 second
    
    print(f"\n📊 Successfully processed {processed} out of {total_assets} HDRIs")
    
    # Save to JSON file
    if assets_data:
        output_file = 'hdri_metadata.json'
        if save_to_json(assets_data, output_file):
            print(f"\n✅ Successfully collected metadata for {len(assets_data)} HDRIs")
            print(f"📄 Output file: {os.path.abspath(output_file)}")
            
            # Print a sample of the collected data
            sample_asset = next(iter(assets_data.values()))
            print("\n📝 Sample HDRI data:")
            print(json.dumps(sample_asset, indent=2, ensure_ascii=False))
        else:
            print("❌ Failed to save metadata")
    else:
        print("❌ No data collected")
    
    return assets_data

if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    print(f"\n⏱️  Execution time: {(time.time() - start_time):.2f} seconds")