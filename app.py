import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from main import run_pipeline_for_api

app = Flask(__name__)
CORS(app)


@app.route("/run-pipeline", methods=["POST"])
def run_pipeline_endpoint():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    suffix = os.path.splitext(file.filename)[1] or ".jpg"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        temp_path = tmp.name

    try:
        result = run_pipeline_for_api(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(temp_path)


if __name__ == "__main__":
    app.run(port=5000, debug=True)