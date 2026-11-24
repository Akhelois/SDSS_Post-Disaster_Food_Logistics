import json, os, sys

with open('backend/output/sdss_result.geojson', 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f"Total features: {len(d.get('features', []))}")
sources = {}
for f in d.get('features', []):
    s = f.get('properties', {}).get('source', 'Unknown')
    sources[s] = sources.get(s, 0) + 1
print("Sources in raw geojson:", sources)

# Check SPHERE standard calculation
# 1 KK = 4 Jiwa
# Standar BNPB 10 hari = 400g beras/jiwa/hari = 4kg/jiwa untuk 10 hari = 16kg per KK
# 16.06 Ton = 16,060 kg beras / 16 kg per KK = ~1,003 KK = ~4,015 Jiwa!
print("\n--- SPHERE HARMONIZATION CHECK ---")
beras_ton = 16.06
beras_kg = beras_ton * 1000
kk_supported = beras_kg / 16.0 # 16 kg per KK for 10 days
jiwa_supported = kk_supported * 4
print(f"16.06 Ton Beras supports: {kk_supported:.0f} KK ({jiwa_supported:.0f} Jiwa) according to BNPB 10-day standard!")
