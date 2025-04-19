from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import io
import json
import os
from google.cloud import storage
import re

app = Flask(__name__)

# Function to fetch CSV data from GCP Storage
def fetch_csv_data(gcs_url):
    # Set the path to your service account JSON file
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "json-file-path"

    # Parse the GCS URL, expected format:
    # "https://storage.googleapis.com/<bucket>/<path-to-blob>"
    match = re.match(r"https://storage.googleapis.com/([^/]+)/(.+)", gcs_url)
    if not match:
        raise ValueError("Invalid GCP Storage URL format")
    
    bucket_name = match.group(1)
    blob_path = match.group(2)

    # Initialize storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Download the blob as string and load as DataFrame
    csv_content = blob.download_as_string()
    df = pd.read_csv(io.StringIO(csv_content.decode('utf-8')))
    return df

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# API route to get CSV data
@app.route('/api/data')
def get_data():
    try:
        url = "https://storage.googleapis.com/your-processed-csvs/processed/sonarqube_report.csv"

        df = fetch_csv_data(url)
        
        # Convert DataFrame to JSON
        data = df.fillna('').to_dict(orient='records')
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API route for chatbot interaction
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({"response": "Please provide a message."})
        
        # Get data for context
        url = "https://storage.cloud.google.com/your-processed-csvs/processed/sonarqube_report.csv"
        df = fetch_csv_data(url)
        
        # Process the user message and generate a response based on CSV data
        response = process_chat_request(user_message, df)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

def process_chat_request(message, df):
    """
    Process the user's chat message using the SonarQube data.
    This is a simple implementation - in production you would integrate with Gemini API.
    """
    message = message.lower()
    
    # Count issues by severity
    if "count" in message and ("severity" in message or "issues" in message):
        severity_counts = df['severity'].value_counts().to_dict()
        return f"Issue counts by severity: {severity_counts}"
    
    # List rules that appear most frequently
    elif "frequent" in message and "rules" in message:
        rule_counts = df['rule'].value_counts().head(5).to_dict()
        response = "Most frequent rules:\n"
        for rule, count in rule_counts.items():
            response += f"- {rule}: {count} occurrences\n"
        return response
        
    # Get info about specific severity
    elif any(sev in message for sev in ["blocker", "critical", "major", "minor", "info"]):
        for sev in ["blocker", "critical", "major", "minor", "info"]:
            if sev in message:
                count = len(df[df['severity'].str.lower() == sev])
                return f"There are {count} issues with {sev} severity."
    
    # Default response if no specific intent is detected
    else:
        total_issues = len(df)
        severity_breakdown = df['severity'].value_counts().to_dict()
        return f"I can provide information about the {total_issues} SonarQube issues. The severity breakdown is: {severity_breakdown}. What specific information would you like to know?"

if __name__ == '__main__':
    app.run(debug=True)