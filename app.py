from flask import Flask, render_template, request, send_from_directory
import os
from test import predict

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    debug = None
    image_url = None

    if request.method == "POST":
        file = request.files.get("image")
        if file and file.filename:
            save_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(save_path)

            label, conf, debug = predict(save_path)
            result = {"label": label, "confidence": round(conf, 3)}

            image_url = f"/uploads/{file.filename}"  # 👈 CORRECT URL

    return render_template(
        "index.html",
        result=result,
        debug=debug,
        image_url=image_url
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True, use_reloader=False)
