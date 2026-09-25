from transformers import pipeline

asr = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-small"
)

result = asr(
    r"C:\Users\kalpa\Downloads\WhatsApp Video 2026-09-04 at 7.08.57 PM.mp4",
    return_timestamps=True,
    language="en"
)

print("Transcription:", result["text"])