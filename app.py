from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import google.auth
from google.cloud import storage
import google.generativeai as genai
from dotenv import load_dotenv
import json
import tempfile
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension

load_dotenv()

app = Flask(__name__)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
]

def download_csv_from_gcp(bucket_name, source_blob_name):
    try:
        storage_client = storage.Client()
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_filename = temp_file.name
        
        blob.download_to_filename(temp_filename)
        
        return temp_filename
    
    except Exception as e:
        print(f"Error downloading file from GCP: {str(e)}")
        return None

def parse_gcp_url(url):
    parts = url.replace('https://storage.cloud.google.com/', '').split('/', 1)
    bucket_name = parts[0]
    blob_name = parts[1]
    return bucket_name, blob_name

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_csv_data', methods=['GET'])
def get_csv_data():
    try:
        gcp_url = "https://storage.cloud.google.com/your-processed-csvs/processed/sonarqube_report.csv"
        bucket_name, blob_name = parse_gcp_url(gcp_url)
        
        csv_path = download_csv_from_gcp(bucket_name, blob_name)
        
        if csv_path:
            # Read CSV with appropriate settings to handle all fields
            df = pd.read_csv(csv_path)
            
            # Convert any NaN values to None (which becomes null in JSON)
            df = df.where(pd.notnull(df), None)
            
            # Convert dataframe to JSON records format
            json_data = df.to_json(orient='records')
            
            # Clean up the temporary file
            os.unlink(csv_path)
            
            return json_data
        else:
            return jsonify({"error": "Failed to download CSV file from GCP"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        csv_data = request.json.get('csvData', [])
        
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        csv_summary = json.dumps(csv_data[:5]) if len(csv_data) > 5 else json.dumps(csv_data)
        
        context = f"""
        You are a helpful assistant analyzing Sonarqube reports. 
        Here's sample data from the report: {csv_summary}
        
        The user is asking about this Sonarqube report. Provide helpful insights, explanations, and solutions.
        
        Please format your response with:
        - Clear sections with headers (## for main sections, ### for subsections)
        - Bullet points for lists
        - Bold text (**bold**) for important terms
        - Code blocks for code examples
        - Tables for comparative data when appropriate
        - Horizontal rules between major sections
        
        Keep the response professional but approachable. Focus on:
        1. Identifying the issue clearly
        2. Explaining why it's problematic
        3. Providing actionable solutions
        4. Offering best practices to prevent similar issues
        """
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            context + "\n\nUser: " + user_message,
            safety_settings=safety_settings
        )
        
        html_response = markdown.markdown(
            response.text,
            extensions=[
                FencedCodeExtension(),
                TableExtension(),
                'fenced_code',
                'tables'
            ]
        )
        
        return jsonify({
            "response": html_response,
            "original_markdown": response.text
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to generate response"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)