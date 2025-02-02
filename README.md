1. This project is a Flask-based web application that lets users upload a document (PDF or TXT).  
2. Users then submit a query related to the content of the document.  
3. The app extracts text from the document using libraries like PyPDF2.  
4. It sends the document text and query to multiple LLM APIs (OpenAI and Hugging Face).  
5. Responses are fetched from models such as GPT-3.5, GPT-4, and GPT-2.  
6. A dummy function computes similarity scores for each model’s response.  
7. A dynamic Chart.js bar chart visualizes the similarity scores.  
8. The frontend uses Bootstrap for a responsive and modern UI.  
9. API keys and sensitive configurations are managed via a secure .env file.  
10. Future enhancements include advanced document parsing, semantic similarity evaluation, and user feedback features.
