# Upload & KYC Form Debug Guide

## Issues Fixed

### 1. **Missing EasyOCR Library** ❌ → ✅
- **Problem**: The app imports `easyocr` but it wasn't installed
- **Symptom**: Upload processing would fail silently
- **Fix**: `pip install easyocr`
- **Status**: FIXED

### 2. **Missing Flask-Swagger-UI** ❌ → ✅
- **Problem**: Swagger UI couldn't be imported
- **Symptom**: Flask app wouldn't start
- **Fix**: `pip install flask-swagger-ui`
- **Status**: FIXED

---

## How to Test the System

### Step 1: Start the Flask App
```bash
cd c:\nagarikta
python chatgpt.py
```

**Expected output:**
```
[DEBUG] Loading YOLO model from: weights/best.pt
[DEBUG] Model loaded successfully
WARNING in app.run_simple (line XXX): This is a development server...
Running on http://0.0.0.0:5001
```

### Step 2: Test Health Check (Optional)
Open in browser or run in terminal:
```
http://localhost:5001/api/health
```

Should return:
```json
{
  "status": "ok",
  "model_loaded": true,
  "config": {
    "upload_folder_exists": true
  }
}
```

### Step 3: Test Upload
1. Open http://localhost:5001 in your browser
2. Upload front & back citizenship card images
3. Click "Upload"
4. Check server console for detailed logs

---

## Understanding the Debug Logs

When you upload, you'll see logs in 3 categories:

### ✓ SUCCESS Logs
```
[DEBUG] Upload request received
[DEBUG] Images loaded - Front: (1920, 1200), Back: (1920, 1200)
[DEBUG] Running YOLO prediction...
[DEBUG] Found 14 boxes in front image
[DEBUG] Box 0 (class 1): "राज कुमार शर्म"
[DEBUG] Session updated successfully
[DEBUG] Redirecting to KYC form
```

### ⚠️ WARNING Logs
```
[WARN] EasyOCR failed: ...
[WARN] Tesseract failed: ...
[WARN] Nagrikta number check failed: ...
```
→ These are usually OK - the system tries multiple OCR methods

### ❌ ERROR Logs (Need Action)
```
[ERROR] Failed to save files: ...
[ERROR] YOLO prediction failed: ...
[ERROR] Failed to load images: ...
[ERROR] OCR failed for box 0: ...
```
→ These indicate actual problems

---

## Common Issues & Solutions

### Issue: "Nothing happens after upload"
**Possible causes:**
1. ❌ Missing dependencies → RUN: `pip install -r requirements.txt`
2. ❌ YOLO model not found → Check `weights/best.pt` exists
3. ❌ Tesseract not installed → Install from: https://github.com/UB-Mannheim/tesseract/wiki
4. ❌ Port 5001 already in use → Change port in chatgpt.py line 1079

**Debug steps:**
- Check server console for [ERROR] messages
- Open browser console (F12) → Console tab → check for errors
- Run diagnostics: `python test_upload_debug.py`

### Issue: Browser shows "Upload failed" message
**Check:**
1. Server console for [ERROR] logs
2. Browser console (F12) for JavaScript errors
3. The error message shown to user (should be detailed now)

### Issue: Model loading hangs
**This is normal** - the first time takes 1-2 minutes if using GPU
- Be patient or check GPU memory usage

### Issue: OCR not extracting text correctly
**This is a different issue** - upload IS working but text cleaning needs tuning
- Check individual OCR boxes in server logs
- Modify text cleaning functions in chatgpt.py (lines 380-700)

---

## File Structure Check

Make sure these exist:
```
c:\nagarikta\
├── chatgpt.py           ← Main Flask app
├── weights\
│   └── best.pt          ← YOLO model (6 MB)
├── uploads\             ← Gets created automatically
├── templates\
│   ├── index.html
│   └── kycform.html
├── static\
│   ├── script.js
│   ├── style.css
│   └── index.html
└── requirements.txt     ← Updated with easyocr
```

---

## Updated Dependencies

These were just installed:
- ✓ **easyocr** - Optical character recognition
- ✓ **flask-swagger-ui** - API documentation UI

All dependencies should now be satisfied. Verify with:
```bash
pip install -r requirements.txt
```

---

## Next Steps

1. **Start the app**: `python chatgpt.py`
2. **Test upload**: Go to http://localhost:5001
3. **Monitor logs**: Watch server console for [DEBUG] messages
4. **Check results**: Browser should redirect to KYC form
5. **If stuck**: Check logs for [ERROR] messages

---

## Still Having Issues?

Run the diagnostic:
```bash
python test_upload_debug.py
```

This will check:
- ✓ YOLO model file
- ✓ Upload folder
- ✓ All dependencies
- ✓ Tesseract installation
- ✓ Model can be loaded

Output will show exactly what's missing or broken.
