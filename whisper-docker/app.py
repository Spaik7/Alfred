from flask import Flask, request, jsonify
import os
import whisper

# Load Whisper model from environment variable (set during Docker build)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "turbo")
print(f"🤖 Loading Whisper model: {WHISPER_MODEL}")
model = whisper.load_model(WHISPER_MODEL)

LANGUAGE_WHITELIST = ["en", "it"]

def limited_language_detection(audio_path):
    """
    Detects language and re-runs transcription if outside the allowed set.
    """
    result = model.transcribe(audio_path)
    lang = result.get("language", "en")

    # Force fallback if not in whitelist
    if lang not in LANGUAGE_WHITELIST:
        print(f"⚠️ Detected '{lang}', forcing fallback to 'en'")
        result = model.transcribe(audio_path, language="it")

    return result


def transcribe_audio(file_path):
    """
    Transcribe audio to text using Whisper model.
    Limits language detection to Italian or English.
    Automatically removes the audio file after transcription.
    """
    try:
        result = limited_language_detection(file_path)
        plain_text = result["text"]
        print(f"🗣 Detected language: {result['language']}")
        return plain_text

    finally:
        # Ensure cleanup
        if os.path.exists(file_path):
            os.remove(file_path)


app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/audio", methods=["POST"])
def audio():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Save uploaded file
        save_path = os.path.join(UPLOAD_FOLDER, "last_command.wav")
        file.save(save_path)
        print(f"✅ File received: {save_path}")

        # Transcribe (English/Italian only)
        plain_text = transcribe_audio(save_path)

        return jsonify({
            "success": True,
            "transcription": plain_text,
        })

    except Exception as e:
        print("❌ Error transcribing file:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9999)
