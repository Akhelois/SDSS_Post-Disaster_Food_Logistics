from main import get_dashboard_data
try:
    print(get_dashboard_data())
except Exception as e:
    import traceback
    traceback.print_exc()
