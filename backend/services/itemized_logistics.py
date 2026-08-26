import os
import numpy as np
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'model')
H5_MODEL_PATH = os.path.join(MODEL_DIR, 'itemized_logistics_dl_model.h5')

_dl_model_cache = None

def _load_model():
    global _dl_model_cache
    if _dl_model_cache is None and os.path.exists(H5_MODEL_PATH):
        try:
            from tensorflow import keras
            _dl_model_cache = keras.models.load_model(H5_MODEL_PATH, compile=False)
        except Exception:
            pass
    return _dl_model_cache

def predict_itemized_logistics(damage_count, affected_kk, total_population, disaster_type="Banjir", severity_level=3, emergency_duration=10, vulnerability_idx=0.5):
    model = _load_model()
    
    disaster_map = {
        'banjir': 0,
        'gempa bumi': 1,
        'gempa': 1,
        'tanah longsor': 2,
        'longsor': 2,
        'angin kencang': 3,
        'tsunami': 4,
        'kebakaran': 5,
        'kebakaran hutan': 5
    }
    dt_clean = str(disaster_type).lower().strip()
    disaster_type_enc = disaster_map.get(dt_clean, 0)
    
    if affected_kk is None or affected_kk <= 0:
        affected_kk = max(1, damage_count)
        
    if total_population is None or total_population <= 0:
        total_population = affected_kk * 4
        
    input_array = np.array([[
        float(damage_count),
        float(affected_kk),
        float(total_population),
        float(disaster_type_enc),
        float(severity_level),
        float(emergency_duration),
        float(vulnerability_idx)
    ]], dtype=np.float32)
    
    if model is not None:
        try:
            raw_preds = model.predict(input_array)
            preds = raw_preds[0] if len(raw_preds.shape) > 1 else raw_preds
            
            target_cols = [
                'beras_kg', 'minyak_liter', 'gula_kg', 'indomie_pcs',
                'roma_sari_gandum_pack', 'roma_malkist_abon_pack', 'roma_kelapa_pack',
                'roma_marie_susu_pack', 'sarden_pcs', 'kornet_pcs',
                'susu_full_cream_pcs', 'susu_dancow_box', 'matras_pcs',
                'kasur_lipat_pcs', 'kompor_set', 'karpet_plastik_pcs', 'kipas_angin_pcs'
            ]
            
            result = {}
            for col, val in zip(target_cols, preds):
                result[col] = max(0.0, float(round(float(val), 2) if 'kg' in col or 'liter' in col else round(float(val))))
            return result
        except Exception:
            pass

    duration_factor = emergency_duration / 10.0
    return {
        'beras_kg': round(affected_kk * 5.0 * duration_factor, 2),
        'minyak_liter': round(affected_kk * 1.0 * duration_factor, 2),
        'gula_kg': round(affected_kk * 1.0 * duration_factor, 2),
        'indomie_pcs': int(affected_kk * 5 * duration_factor),
        'roma_sari_gandum_pack': int(affected_kk * 1 * duration_factor),
        'roma_malkist_abon_pack': int(affected_kk * 1 * duration_factor),
        'roma_kelapa_pack': int(affected_kk * 1 * duration_factor),
        'roma_marie_susu_pack': int(affected_kk * 1 * duration_factor),
        'sarden_pcs': int(affected_kk * 1 * duration_factor),
        'kornet_pcs': int(affected_kk * 1 * duration_factor),
        'susu_full_cream_pcs': int(affected_kk * 1 * duration_factor),
        'susu_dancow_box': int(affected_kk * 1 * duration_factor),
        'matras_pcs': affected_kk,
        'kasur_lipat_pcs': affected_kk,
        'kompor_set': affected_kk,
        'karpet_plastik_pcs': affected_kk,
        'kipas_angin_pcs': affected_kk
    }
