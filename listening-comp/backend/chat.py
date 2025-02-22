# Create BedrockChat
# bedrock_chat.py
import boto3
import streamlit as st
from typing import Optional, Dict, Any
from google import genai
from dotenv import load_dotenv
import os
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# Model ID
MODEL_ID = "amazon.nova-micro-v1:0"


class BedrockChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock chat client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        if inference_config is None:
            inference_config = {"temperature": 0.7}

        messages = [{
            "role": "user",
            "content": [{"text": message}]
        }]

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return None


class GeminiChat:
    def __init__(self):
        """Initialize Gemini chat client"""
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def generate_response(self, message: str) -> Optional[str]:
        """Generate a response using Google Gemini"""
        self.system_instructions = """You are a Japanese tutor. The user will ask your help with translating english to japanese, but do NOT provide them with the direct answer. Only provide hints!!!"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite-preview-02-05",
                contents=message,
                config=types.GenerateContentConfig(
                    # system_instruction=self.system_instructions,
                )
            )
            return response.text#['content']  # Adjust based on the actual response structure
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None


if __name__ == "__main__":
    # chat = BedrockChat()
    chat = GeminiChat()
    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            break
        response = chat.generate_response(user_input)
        print("Bot:", response)
