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
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "durable-height-454113-n9-34ea69735ea6.json"

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
        url = "https://storage.googleapis.com/your-processed-csvs/processed/sonarqube_report.csv"
        df = fetch_csv_data(url)
        
        # Process the user message and generate a response based on CSV data
        response = process_chat_request(user_message, df)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

def process_chat_request(message, df):
    """
    A smarter chatbot that handles various queries about SonarQube report data.
    """
    message = message.lower()
    df.columns = [col.lower() for col in df.columns]

    response_parts = []

    # Show help
    if "help" in message or "what can you do" in message:
        return (
            "I can help you understand your SonarQube analysis report.\n"
            "Try asking things like:\n"
            "- How many bugs are there?\n"
            "- Count issues by severity\n"
            "- What are the most frequent rules?\n"
            "- Show vulnerabilities\n"
            "- Blocker issues count\n"
        )

    # Count issues by severity
    if "count" in message and ("severity" in message or "issues" in message):
        severity_counts = df['severity'].str.upper().value_counts().to_dict()
        response_parts.append(f"Issue counts by severity: {severity_counts}")

    # Frequent rules
    if "frequent" in message or "top rules" in message:
        if 'rule' in df.columns:
            rule_counts = df['rule'].value_counts().head(5).to_dict()
            response_parts.append("Most frequent rules:")
            for rule, count in rule_counts.items():
                response_parts.append(f"- {rule}: {count} times")
        else:
            response_parts.append("The CSV does not contain a 'rule' column.")

    # Specific severity
    for sev in ["blocker", "critical", "major", "minor", "info"]:
        if sev in message:
            count = len(df[df['severity'].str.lower() == sev])
            response_parts.append(f"There are {count} {sev.upper()} severity issues.")

    # Specific types (bugs, vulnerabilities, smells)
    if "bug" in message:
        count = len(df[df['type'].str.lower() == "bug"])
        response_parts.append(f"There are {count} bug(s) reported.")
    
    if "vulnerab" in message:
        count = len(df[df['type'].str.lower() == "vulnerability"])
        response_parts.append(f"There are {count} vulnerability issue(s).")

    if "smell" in message:
        count = len(df[df['type'].str.lower() == "code_smell"])
        response_parts.append(f"There are {count} code smell(s).")

    # If no specific pattern matched
    if not response_parts:
        total_issues = len(df)
        severity_breakdown = df['severity'].str.upper().value_counts().to_dict()
        response_parts.append(f"I can provide information about {total_issues} SonarQube issues.")
        response_parts.append(f"Severity breakdown: {severity_breakdown}")
        response_parts.append("Try asking about bugs, vulnerabilities, rules, or issue severity.")

    return "\n".join(response_parts)

if __name__ == '__main__':
    app.run(debug=True)