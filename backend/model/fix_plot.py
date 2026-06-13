import json

NOTEBOOK_PATH = r"c:\Users\Jase.LAPTOP-UM736EL9\Documents\Binus\Thesis S2\SDSS_Post-Disaster_Food_Logistics\backend\model\train_model.ipynb"

with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for c in nb.get('cells', []):
    src = ''.join(c.get('source', []))
    if 'Sampel Dataset: Citra Post-Disaster & Mask Kerusakan' in src:
        new_src = src.replace('fig, axs = plt.subplots(2, 5, figsize=(20, 8))', 
"""for imgs, masks in train_ds.take(1):
    n_samples = min(5, imgs.shape[0])
    fig, axs = plt.subplots(2, n_samples, figsize=(4*n_samples, 8))
""")
        new_src = new_src.replace('for imgs, masks in train_ds.take(1):', '')
        new_src = new_src.replace('for i in range(min(5, imgs.shape[0])):', 'for i in range(n_samples):')
        
        # Split back to lines
        lines = new_src.splitlines(True)
        c['source'] = lines
        print("Berhasil mengubah cell plot!")
        break

with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
