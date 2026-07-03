import os, glob, shutil

try:
    with open(r'c:\nagarikta\logs\kyc_app.log', 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        with open('debug_logs.txt', 'w', encoding='utf-8') as out:
            for line in lines[-50:]:
                out.write(line)
except Exception as e:
    print("Log read error:", e)

try:
    files = glob.glob(r'c:\nagarikta\cache\*.json')
    if files:
        latest = max(files, key=os.path.getctime)
        shutil.copy(latest, r'c:\nagarikta\debug_cache.json')
except Exception as e:
    print("Cache read error:", e)
