from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

app = Flask(__name__)
CORS(app) # Allow all origins
@app.route("/helper_api", methods=["POST", "OPTIONS"])
def get_relevant_keyword():
    """Returns the most relevant noun keyword in a given string"""
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        response.headers.update(headers)
        return response
    data = request.get_json()
    text = data.get("text", "")
    
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    #all_keywords = [chunk.text for chunk in doc.noun_chunks]
    noun_chunks = []

    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip().lower()

        # Skip noun chunks starting with stop words
        if chunk[0].text.lower() in STOP_WORDS:
            continue

        # Give weight to noun chunks with multiple NOUN or PROPN tokens
        score = sum(1 for tok in chunk if tok.pos_ in ['NOUN', 'PROPN'])

        if score > 0:
            noun_chunks.append((chunk_text, score))

    # Returns the highest scoring noun chunk
    if noun_chunks:
        return jsonify({"keyword": max(noun_chunks, key=lambda x: x[1])[0]})
    return jsonify({"keyword": None})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)