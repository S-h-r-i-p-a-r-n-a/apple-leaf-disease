# from gtts import gTTS
# import os

# # Hardcoded FAQ (can be extended or replaced with a model later)
# FAQ = {
#     "what is rust": "Rust is a fungal disease that affects apple leaves. Use fungicides like myclobutanil.",
#     "how to cure scab": "Scab can be treated using captan or mancozeb sprays. Prune infected parts.",
#     "how to use the app": "Upload a leaf image. The app detects the disease and suggests treatments.",
#     "can i prevent disease": "Yes. Maintain cleanliness and apply preventive fungicides regularly."
# }

# # Simple matching function
# def get_answer(query: str):
#     query = query.lower()
#     for key in FAQ:
#         if key in query:
#             return FAQ[key]
#     return "Sorry, I don't have an answer to that yet."

# # Convert answer to Hindi audio
# def text_to_voice(text: str, lang="hi", save_path="downloads/response.mp3"):
#     os.makedirs("downloads", exist_ok=True)
#     tts = gTTS(text, lang=lang)
#     tts.save(save_path)
#     return save_path
