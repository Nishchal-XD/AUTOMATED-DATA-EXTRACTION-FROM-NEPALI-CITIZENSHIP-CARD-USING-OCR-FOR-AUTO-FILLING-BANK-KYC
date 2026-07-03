from main import extract_nagrikta_number


def make_field(text, cid=4):
    # simulate YOLO output item with class_id and OCR text
    return {"class_id": cid, "text": text}


def test_extract_english_digits():
    fld = make_field("Citizen no: 123456789")
    assert extract_nagrikta_number([fld]) == "123456789"


def test_extract_nepali_digits():
    # nepali digits for 98765 -> ९८७६५
    fld = make_field("नागरिकता नं ९८७६५")
    assert extract_nagrikta_number([fld]) == "98765"


def test_ignore_short_numbers():
    fld = make_field("xyz 12 abc")
    assert extract_nagrikta_number([fld]) == ""


def test_multiple_fields():
    fields = [make_field("some text"), make_field("नं. १२३४५६")]
    assert extract_nagrikta_number(fields) == "123456"


def test_ordering():
    # first valid number should be returned
    fields = [make_field("नं. १२३"), make_field("नं. ४५६७")]
    assert extract_nagrikta_number(fields) == "4567"  # first one too short, skip


def make_image_bytes(color=(255,255,255)):
    """Return a PNG image bytes for a tiny square."""
    from io import BytesIO
    from PIL import Image
    buf = BytesIO()
    img = Image.new("RGB", (10, 10), color)
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_upload_route_mismatch(monkeypatch):
    from main import app, extract_nagrikta_number
    client = app.test_client()

    # patch extract_nagrikta_number so front/back return different codes
    counter = {"n": 0}
    def fake(fields):
        counter["n"] += 1
        return "11111" if counter["n"] == 1 else "22222"
    monkeypatch.setattr('main.extract_nagrikta_number', fake)

    data = {
        'front': (make_image_bytes(), 'front.png'),
        'back': (make_image_bytes(), 'back.png'),
    }
    resp = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert 'Nagrikta numbers do not match' in resp.get_data(as_text=True)


def test_upload_route_matching(monkeypatch):
    from main import app
    client = app.test_client()

    # always return same number
    monkeypatch.setattr('main.extract_nagrikta_number', lambda f: '99999')
    data = {
        'front': (make_image_bytes(), 'front.png'),
        'back': (make_image_bytes(), 'back.png'),
    }
    resp = client.post('/api/upload', data=data, content_type='multipart/form-data')
    # since we only patch the number extraction, upload may still fail later
    # but we at least confirm the nagrikta check passes by checking status != 400
    assert resp.status_code != 400


def test_back_docnum_fallback(monkeypatch):
    """Ensure a nagrikta number is recovered even if detector returns unrelated boxes."""
    from main import app
    import numpy as np

    client = app.test_client()

    # fake model that always returns one dummy box with a non–doc class
    class FakeResult:
        def __init__(self):
            self.boxes = type('X', (), {'data': np.array([[0,0,10,10,0.9,0]])})
    class FakeModel:
        def predict(self, source, conf):
            # mimic list of Results (one per image)
            if isinstance(source, list):
                return [FakeResult() for _ in source]
            return [FakeResult()]
    monkeypatch.setattr('main', 'get_model', lambda: FakeModel())

    # no preprocessing required for this test
    monkeypatch.setattr('main', 'preprocess_image', lambda img, lang: img)
    # OCR always returns a string containing a number
    monkeypatch.setattr('main', 'ocr_text', lambda img, lang, is_full_page=False: "Citizenship No: 5555")

    data = {
        'front': (make_image_bytes(), 'front.png'),
        'back': (make_image_bytes(), 'back.png'),
    }
    resp = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code != 400

    # verify that the session data contains the synthetic number on the back
    with client.session_transaction() as sess:
        kyc = sess.get('kyc_data', {})
    back_fields = kyc.get('back', [])
    nums = [item['text'] for item in back_fields if item.get('class_id') == 4]
    assert any('5555' in n for n in nums), f"did not find docnum in back: {nums}"


def test_date_dob_fallback(monkeypatch):
    """If YOLO misses both issued date and DOB boxes, the combined
    OCR text should still yield those values and they should appear in the
    back side data after upload.
    """
    from main import app
    import numpy as np

    client = app.test_client()

    # fake model returns a single irrelevant box (class 0)
    class FakeResult:
        def __init__(self):
            self.boxes = type('X', (), {'data': np.array([[0,0,10,10,0.9,0]])})
    class FakeModel:
        def predict(self, source, conf):
            if isinstance(source, list):
                return [FakeResult() for _ in source]
            return [FakeResult()]
    monkeypatch.setattr('main', 'get_model', lambda: FakeModel())

    # bypass preprocessing so OCR text is predictable
    monkeypatch.setattr('main', 'preprocess_image', lambda img, lang: img)

    # OCR returns both an issued date and a DOB in a single string
    combined_txt = "Issued Date: 2076-05-20 DOB: 2076-05-20"
    def fake_ocr(img, lang, is_full_page=False):
        return combined_txt
    monkeypatch.setattr('main', 'ocr_text', fake_ocr)

    data = {
        'front': (make_image_bytes(), 'front.png'),
        'back': (make_image_bytes(), 'back.png'),
    }
    resp = client.post('/api/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code != 400

    with client.session_transaction() as sess:
        kyc = sess.get('kyc_data', {})
    back = kyc.get('back', [])

    # check that fallback added issued date and dob parts
    issued = [item for item in back if item.get('class_id') == 13]
    assert issued and issued[0].get('text') == '2076-05-20', f"issued date missing: {issued}"
    years = [item for item in back if item.get('class_id') == 7]
    months = [item for item in back if item.get('class_id') == 8]
    days = [item for item in back if item.get('class_id') == 9]
    assert years and years[0].get('text') == '2076'
    assert months and months[0].get('text') == '05'
    assert days and days[0].get('text') == '20'

