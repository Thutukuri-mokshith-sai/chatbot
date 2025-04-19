from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import nltk
import spacy
from difflib import get_close_matches

# Download necessary NLTK data
nltk.download('punkt')

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Load disease dataset
with open('disease.json', 'r') as f:
    data = json.load(f)

# Extract all disease names
disease_keys = list(data.keys())

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Greetings
greetings = {"hi", "hello", "hey", "greetings", "good morning", "good evening", "howdy"}

# Global state
current_disease = None

# Utility function to find best match for disease name
def find_best_match(user_input, keys):
    matches = get_close_matches(user_input, keys, n=1, cutoff=0.4)
    return matches[0] if matches else None
def find_disease_by_symptom(user_input):
    user_tokens = set(nltk.word_tokenize(user_input.lower()))
    max_overlap = 0
    best_match = None

    for disease, details in data.items():
        for symptom in details.get("symptoms", []):
            symptom_tokens = set(nltk.word_tokenize(symptom.lower()))
            overlap = len(user_tokens & symptom_tokens)
            if overlap > max_overlap:
                max_overlap = overlap
                best_match = disease

    return best_match if max_overlap > 0 else None


def get_answer(user_input):
    global current_disease
    user_input = user_input.lower()

    # Greeting
    if any(greet in user_input for greet in greetings):
        return "Welcome! How can I assist you with crop diseases?"

    # Build a crop-to-disease map from disease keys
    crop_to_diseases = {}
    for disease_name in disease_keys:
        crop_name = disease_name.split()[0].lower()
        crop_to_diseases.setdefault(crop_name, []).append(disease_name)

    # Check if user asked about diseases of a crop
    if "disease" in user_input or "diseases" in user_input:
        for crop, diseases in crop_to_diseases.items():
            if crop in user_input:
                response = f"Diseases found in {crop.capitalize()}:\n"
                response += "\n".join(diseases)
                response += "\n\nYou can ask about any of these to know more."
                return response

    # Try direct disease match
    identified_disease = find_best_match(user_input, disease_keys)

    # Try symptom-based match if not found
    if not identified_disease:
        identified_disease = find_disease_by_symptom(user_input)

    # Update current disease
    if identified_disease:
        current_disease = identified_disease

    if not current_disease:
        return "Please provide a disease name or describe the symptoms."

    disease_info = data.get(current_disease, {})

    # Info extraction
    if "symptom" in user_input:
        return "\n".join(disease_info.get("symptoms", ["No symptom data available."]))

    elif "treatment" in user_input:
        treatments = disease_info.get("treatments", [])
        if treatments:
            return "\n\n".join([f"Name: {t['name']}\nDosage: {t['dosage']}\nApplication: {t['application']}" for t in treatments])
        return "No treatment data available."

    elif "pathogen" in user_input:
        return f"Pathogen: {disease_info.get('pathogen', 'Unknown')}"

    elif "organic" in user_input:
        organic = disease_info.get("organic_alternatives", [])
        if organic:
            return "\n\n".join([f"Name: {o['name']}\nDosage: {o['dosage']}\nApplication: {o['application']}" for o in organic])
        return "No organic alternatives available."

    elif "prevention" in user_input:
        return "\n".join(disease_info.get("prevention", ["No prevention data available."]))

    elif "safety" in user_input:
        return "\n".join(disease_info.get("safety_tips", ["No safety tips available."]))

    elif any(word in user_input for word in ["details", "info", "information", "about", "describe"]):
        response = f"Information about {current_disease}:\n\n"
        response += "Symptoms:\n" + "\n".join(disease_info.get("symptoms", [])) + "\n\n"
        response += "Prevention:\n" + "\n".join(disease_info.get("prevention", [])) + "\n\n"
        response += "Treatments:\n"
        treatments = disease_info.get("treatments", [])
        if treatments:
            response += "\n\n".join([f"Name: {t['name']}\nDosage: {t['dosage']}\nApplication: {t['application']}" for t in treatments])
        else:
            response += "No treatment info available."
        return response

    else:
        return f"You're referring to {current_disease}. What would you like to know? (e.g., symptoms, treatments, prevention, organic alternatives, pathogen)"
# API endpoint
@app.route('/chat', methods=['POST'])
def chat():
    print("chat")
    user_input = request.json.get('message', '')
    response = get_answer(user_input)
    return jsonify({"response": response})

# Start the server
if __name__ == '__main__':
    app.run(debug=True)
