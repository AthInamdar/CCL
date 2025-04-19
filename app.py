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

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Safety settings for Gemini
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

# Function to download the CSV file from GCP
def download_csv_from_gcp(bucket_name, source_blob_name):
    try:
        # Initialize GCP storage client
        storage_client = storage.Client()
        
        # Get bucket and blob
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_filename = temp_file.name
        
        # Download the blob to the temporary file
        blob.download_to_filename(temp_filename)
        
        return temp_filename
    
    except Exception as e:
        print(f"Error downloading file from GCP: {str(e)}")
        return None

# Parse GCP URL
def parse_gcp_url(url):
    # Expected format: https://storage.cloud.google.com/your-bucket-name/path/to/file.csv
    parts = url.replace('https://storage.cloud.google.com/', '').split('/', 1)
    bucket_name = parts[0]
    blob_name = parts[1]
    return bucket_name, blob_name

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to get CSV data
@app.route('/get_csv_data', methods=['GET'])
def get_csv_data():
    try:
        gcp_url = "https://storage.cloud.google.com/your-processed-csvs/processed/sonarqube_report.csv"
        bucket_name, blob_name = parse_gcp_url(gcp_url)
        
        # Download the CSV file
        csv_path = download_csv_from_gcp(bucket_name, blob_name)
        
        if csv_path:
            # Read the CSV file
            df = pd.read_csv(csv_path)
            
            # Convert DataFrame to JSON
            json_data = df.to_json(orient='records')
            
            # Clean up the temporary file
            os.unlink(csv_path)
            
            return json_data
        else:
            return jsonify({"error": "Failed to download CSV file from GCP"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for Gemini chat
@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        csv_data = request.json.get('csvData', [])
        
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        # Convert CSV data to a readable format for Gemini
        csv_summary = json.dumps(csv_data[:5]) if len(csv_data) > 5 else json.dumps(csv_data)
        
        # Create a context for Gemini with specific formatting instructions
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
        
        # Generate response from Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            context + "\n\nUser: " + user_message,
            safety_settings=safety_settings
        )
        
        # Convert markdown to HTML for better rendering in the frontend
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
            "original_markdown": response.text  # Optional: for debugging
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to generate response"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)