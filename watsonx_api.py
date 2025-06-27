import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WATSONX_API_KEY")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
MODEL_ID = os.getenv("WATSONX_MODEL_ID")

# Step 1: Get IBM IAM Token
def get_iam_token():
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": API_KEY
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()["access_token"]

# Step 2: Use Token to Call Watsonx
def generate_quiz(topic):
    token = get_iam_token()

    url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "model_id": MODEL_ID,
        "input": f"Generate 5 multiple choice quiz questions on the topic: {topic}. Return them as plain text.",
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 500
        },
        "project_id": PROJECT_ID
    }

    response = requests.post(url, headers=headers, json=data)
    print("RESPONSE JSON:", response.json())  # Debug
    try:
        result = response.json().get("results", [{}])[0].get("generated_text")
        return result if result else "No quiz generated"
    except Exception as e:
        return f"Error in response: {str(e)}"