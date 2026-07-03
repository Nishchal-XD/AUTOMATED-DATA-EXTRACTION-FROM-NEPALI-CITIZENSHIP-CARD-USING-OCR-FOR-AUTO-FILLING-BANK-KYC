"""
Standalone test for fix_nepali_name and cross_correct_nepali_name.
Imports ONLY those functions by patching heavy dependencies first.
"""
import sys
import re
import logging

# --------------- minimal stubs so main.py loads without Flask/YOLO ---------------
from unittest.mock import MagicMock, patch

for mod in [
    'ultralytics', 'flask', 'flask_swagger_ui', 'flask_limiter',
    'flask_limiter.util', 'database', 'PIL', 'pytesseract', 'cv2',
    'numpy', 'torch', 'transformers', 'werkzeug', 'werkzeug.utils',
    'dotenv',
]:
    sys.modules.setdefault(mod, MagicMock())

# Patch os.getenv to avoid loading config.env
import os
os.environ.setdefault('MODEL_PATH', 'nonexistent')
os.environ.setdefault('SECRET_KEY', 'test')

# Patch create_table so it doesn't try to connect to DB
with patch.dict('sys.modules', {}):
    pass

# Now import the functions we actually want to test
# We do this by exec-ing only the relevant parts of main.py
import importlib
import importlib.util
import types

def load_functions():
    """Load only the correction functions from main.py without running Flask."""
    src_path = r'c:\nagarikta\main.py'
    with open(src_path, encoding='utf-8') as f:
        source = f.read()

    # Build a minimal namespace with the dependencies our functions need
    namespace = {
        '__name__': '__test__',
        're': re,
        'logging': logging,
        'os': os,
        'logger': logging.getLogger('test'),
    }
    # Only execute the parts we need (up to the route definitions)
    # Find the last line before Flask routes
    cut = source.find('\n@app.route(')
    if cut == -1:
        cut = len(source)
    trimmed = source[:cut]

    # Suppress Flask/YOLO init side-effects by neutralising them
    trimmed = trimmed.replace('load_dotenv(', '#load_dotenv(')
    trimmed = trimmed.replace('create_table()', '#create_table()')
    trimmed = trimmed.replace('app = Flask(', 'app = MagicMock(); _ = (')
    trimmed = trimmed.replace("get_swaggerui_blueprint(", "MagicMock()(")

    exec(compile(trimmed, src_path, 'exec'), namespace)
    return namespace

ns = load_functions()
fix_nepali_name = ns['fix_nepali_name']
cross_correct_nepali_name = ns['cross_correct_nepali_name']

# --------------- tests ---------------------------------------------------------------

def check(label, got, expected):
    ok = got == expected
    sym = '✓ PASS' if ok else '✗ FAIL'
    print(f"  {sym} | {label!r}")
    if not ok:
        print(f"         got:      {got!r}")
        print(f"         expected: {expected!r}")
    return ok


all_ok = True
print("\n=== fix_nepali_name tests ===")

tests = [
    # ── User-reported ─────────────────────────────────────────────────
    ("जुसित चन्द",       "शुसिल चन्द"),
    ("जमृता चन्द",       "अमृता चन्द"),
    ("कर्णबहादुर कन्द",  "कर्ण बहादुर चन्द"),
    # ── Surname चन्द variants ─────────────────────────────────────────
    ("राम कन्द",         "राम चन्द"),
    ("सीता चंद",         "सीता चन्द"),
    ("घन्द",             "चन्द"),
    # ── Compound spacing ──────────────────────────────────────────────
    ("नरबहादुर",         "नर बहादुर"),
    ("कर्णबहादुर",       "कर्ण बहादुर"),
    ("लालबहादुर",        "लाल बहादुर"),
    # ── Surname truncations ───────────────────────────────────────────
    ("राम कार्क",        "राम कार्की"),
    ("रमेश पाण्ड",       "रमेश पाण्डे"),
    ("सुरेश तिवार",      "सुरेश तिवारी"),
    # ── ब→व ──────────────────────────────────────────────────────────
    ("बिमला",            "विमला"),
    ("बिनोद",            "विनोद"),
    # ── Regressions ──────────────────────────────────────────────────
    ("भरत बहादुर शाह",  "भरत बहादुर शाह"),
    ("लक्ष्मी कुमारी",  "लक्ष्मी कुमारी"),
    ("प्रकाश थापा",     "प्रकाश थापा"),
    ("सुशील श्रेष्ठ",   "सुशील श्रेष्ठ"),
]

for inp, exp in tests:
    got = fix_nepali_name(inp)
    all_ok &= check(inp, got, exp)

print("\n=== cross_correct_nepali_name tests ===")

cross_tests = [
    ("जुसित चन्द",  "SHUSIL CHAND",  "शुसिल चन्द"),
    ("जमृता चन्द",  "AMRITA CHAND",  "अमृता चन्द"),
    ("शुसिल चन्द",  "SHUSIL CHAND",  "शुसिल चन्द"),   # no-op
    ("अज्ञात नाम",  "UNKNOWN NAME",  "अज्ञात नाम"),    # no-op
]

for nep, eng, exp in cross_tests:
    nep_fixed = fix_nepali_name(nep)
    got = cross_correct_nepali_name(nep_fixed, eng)
    all_ok &= check(f"{nep}+{eng}", got, exp)

print()
print("✓ ALL PASSED" if all_ok else "✗ SOME TESTS FAILED")
sys.exit(0 if all_ok else 1)
