import os
import shutil
import ctypes

src = r"C:\Users\Jase.LAPTOP-UM736EL9\AppData\Local\Programs\Python\Python310\Lib\site-packages\shapely\lib.cp310-win_amd64.pyd"
dst = r"C:\Windows\Temp\lib.cp310-win_amd64.pyd"

try:
    shutil.copy(src, dst)
    print("Copied successfully.")
    
    # Try loading from C:\Windows\Temp
    ctypes.CDLL(dst)
    print("Loaded from C:\\Windows\\Temp successfully!")
except Exception as e:
    print("Failed:", e)
finally:
    if os.path.exists(dst):
        try:
            os.remove(dst)
        except:
            pass
