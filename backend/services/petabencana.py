import requests
import pandas as pd
from datetime import datetime

def fetch_petabencana_reports(hours=72):
    """
    Mengambil data laporan citizen report dari PetaBencana.id API.
    Memfilter laporan dalam rentang waktu tertentu (default 72 jam - Golden Time).
    """
    # timeperiod dalam detik
    timeperiod = int(hours * 3600)
    url = f"https://data.petabencana.id/reports?timeperiod={timeperiod}"
    
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            print(f"PetaBencana API returned status code {r.status_code}")
            return pd.DataFrame()
            
        data = r.json()
        geometries = data.get('result', {}).get('objects', {}).get('output', {}).get('geometries', [])
        
        records = []
        for g in geometries:
            if g.get('type') == 'Point':
                coords = g.get('coordinates', [])
                props = g.get('properties', {})
                
                # Pastikan ini laporan bencana yang dikonfirmasi
                if props.get('status') != 'confirmed':
                    continue
                    
                if len(coords) == 2:
                    disaster_raw = props.get('disaster_type', 'banjir')
                    
                    # Translasi ke bahasa Indonesia yang sesuai dengan SDSS
                    disaster_map = {
                        'flood': 'Banjir',
                        'earthquake': 'Gempa Bumi',
                        'fire': 'Kebakaran',
                        'haze': 'Kabut Asap',
                        'wind': 'Angin Kencang',
                        'volcano': 'Gunung Meletus'
                    }
                    disaster_type = disaster_map.get(disaster_raw, disaster_raw.capitalize())
                    
                    records.append({
                        'lon': coords[0],
                        'lat': coords[1],
                        'source': 'PetaBencana',
                        'confidence': 0.8,  # Citizen reports divalidasi oleh chatbot PetaBencana
                        'disaster_type': disaster_type,
                        'event_date': props.get('created_at'),
                        'image_url': props.get('image_url'),
                        'text': props.get('text')
                    })
                    
        df = pd.DataFrame(records)
        if not df.empty:
            # Hapus timezone offset agar konsisten dengan backend SDSS
            df['event_date'] = pd.to_datetime(df['event_date']).dt.tz_localize(None)
            
        return df
    except Exception as e:
        print(f"Error fetching PetaBencana: {e}")
        return pd.DataFrame()
