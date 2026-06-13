import json
nb = json.load(open(r'c:\Users\Jase.LAPTOP-UM736EL9\Documents\Binus\Thesis S2\SDSS_Post-Disaster_Food_Logistics\backend\model\train_model.ipynb','r',encoding='utf-8'))
for i, c in enumerate(nb.get('cells',[])):
    src = ''.join(c.get('source',[]))
    if 'train_test_split' in src or 'oversampling' in src.lower() or 'damage_ratios' in src:
        print(f'--- CELL {i} ---')
        print(src[:500])
