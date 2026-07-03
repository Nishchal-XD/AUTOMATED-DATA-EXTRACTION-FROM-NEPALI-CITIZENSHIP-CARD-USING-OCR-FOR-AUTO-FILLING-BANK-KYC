import importlib
try:
    m = importlib.import_module('flask_swagger_ui')
    print('module found', m)
except Exception as e:
    print('import error', e)
