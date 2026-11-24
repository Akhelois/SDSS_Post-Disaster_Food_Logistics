import sys, os
sys.path.insert(0, os.path.abspath('backend'))
os.chdir('backend')
from main import get_dashboard_data

res = get_dashboard_data()
if 'map_data' in res:
    rz = res['map_data']['red_zones']
    print(f'Total Red zones: {len(rz)}')
    for z in rz:
        pct = round(z['priority_score'] * 100, 1)
        print(f"{z['desa']} | Score: {z['priority_score']} ({pct}%) | Label: {z['priority_label']} | Count: {z['count']} | Pop: {z['population']} | Elapsed: {z.get('elapsed_hours')}h | Pillars: {z.get('priority_pillars')}")
else:
    print('No map_data:', res.keys())
