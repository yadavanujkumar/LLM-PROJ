# app.py
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import os
import PyPDF2
import json
import requests
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from env variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

# Set OpenAI key
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_default_secret_key')  # Use a secure key for production

# ---------------------
# Helper Functions
# ---------------------

def extract_text_from_file(file):
    """Extract text from a PDF or TXT file."""
    document_text = ""
    if file.filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                document_text += text
    elif file.filename.endswith('.txt'):
        document_text = file.read().decode('utf-8')
    else:
        document_text = None
    return document_text

def compute_similarity(response):
    """A dummy function to compute similarity score (replace with your logic)."""
    # For demonstration, returns a score between 0 and 1 based on response length.
    return round((len(response) % 100) / 100, 2)

# ---------------------
# LLM API Integration
# ---------------------

def get_openai_response(document_text, query, model_name='gpt-3.5-turbo'):
    try:
        prompt = f"Document:\n{document_text}\n\nQuestion: {query}\nAnswer:"
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("OpenAI API error:", e)
        return f"Error from {model_name}"

def get_hf_response(document_text, query, model_id="gpt2"):
    try:
        payload = {
            "inputs": f"Document: {document_text}\nQuestion: {query}\nAnswer:",
            "parameters": {"max_new_tokens": 100}
        }
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            # Depending on the model response structure, adjust the parsing.
            if isinstance(result, list) and 'generated_text' in result[0]:
                return result[0]['generated_text'].strip()
            else:
                return str(result)
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        print("Hugging Face API error:", e)
        return "Error from Hugging Face model"

# ---------------------
# Flask Routes
# ---------------------

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('document')
        if not file:
            return render_template('upload.html', error="No file uploaded!")
        
        document_text = extract_text_from_file(file)
        if document_text is None:
            return render_template('upload.html', error="Unsupported file type. Please upload PDF or TXT.")
        
        session['document_text'] = document_text
        return redirect(url_for('query'))
    return render_template('upload.html')

@app.route('/query', methods=['GET', 'POST'])
def query():
    if 'document_text' not in session:
        return redirect(url_for('upload_file'))
    
    if request.method == 'POST':
        query_text = request.form.get('query')
        if not query_text:
            return render_template('query.html', error="Please enter a query!")
        
        document_text = session.get('document_text')
        # Define our models and corresponding functions.
        models = {
            'OpenAI GPT-3.5': lambda: get_openai_response(document_text, query_text, model_name='gpt-3.5-turbo'),
            'OpenAI GPT-4': lambda: get_openai_response(document_text, query_text, model_name='gpt-4'),
            'Hugging Face GPT-2': lambda: get_hf_response(document_text, query_text, model_id="gpt2")
        }
        responses = {}
        scores = {}
        for model_name, func in models.items():
            response = func()
            responses[model_name] = response
            scores[model_name] = compute_similarity(response)
        
        session['query'] = query_text
        session['responses'] = responses
        session['scores'] = scores
        return redirect(url_for('results'))
    return render_template('query.html')

@app.route('/results', methods=['GET'])
def results():
    if 'responses' not in session or 'scores' not in session:
        return redirect(url_for('upload_file'))
    
    responses = session.get('responses')
    scores = json.dumps(session.get('scores'))
    query_text = session.get('query')
    return render_template('results.html', responses=responses, scores=scores, query=query_text)

# Optional API endpoint for dynamic JS (if needed)
@app.route('/api/scores')
def api_scores():
    if 'scores' not in session:
        return jsonify({})
    return jsonify(session.get('scores'))

if __name__ == '__main__':
    app.run(debug=True)
