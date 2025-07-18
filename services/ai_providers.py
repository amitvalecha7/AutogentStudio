import os
import openai
import anthropic
from anthropic import Anthropic
import requests
import json
from utils.encryption import decrypt_api_key
from models import APIKey
from flask_login import current_user

class AIProviders:
    def __init__(self):
        self.providers = {
            'openai': self._get_openai_client,
            'anthropic': self._get_anthropic_client,
            'google': self._get_google_client,
            'cohere': self._get_cohere_client,
            'ollama': self._get_ollama_client
        }
    
    def _get_api_key(self, provider):
        """Get decrypted API key for provider"""
        if current_user.is_authenticated:
            api_key_record = APIKey.query.filter_by(
                user_id=current_user.id, 
                provider=provider,
                is_active=True
            ).first()
            
            if api_key_record:
                return decrypt_api_key(api_key_record.encrypted_key)
        
        # Fallback to environment variables
        return os.getenv(f'{provider.upper()}_API_KEY')
    
    def _get_openai_client(self):
        """Get OpenAI client"""
        api_key = self._get_api_key('openai')
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        return openai.OpenAI(api_key=api_key)
    
    def _get_anthropic_client(self):
        """Get Anthropic client"""
        api_key = self._get_api_key('anthropic')
        if not api_key:
            raise ValueError("Anthropic API key not found")
        
        return Anthropic(api_key=api_key)
    
    def _get_google_client(self):
        """Get Google AI client"""
        api_key = self._get_api_key('google')
        if not api_key:
            raise ValueError("Google AI API key not found")
        
        return {"api_key": api_key}
    
    def _get_cohere_client(self):
        """Get Cohere client"""
        api_key = self._get_api_key('cohere')
        if not api_key:
            raise ValueError("Cohere API key not found")
        
        return {"api_key": api_key}
    
    def _get_ollama_client(self):
        """Get Ollama client"""
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        return {"base_url": base_url}
    
    def get_chat_response(self, message, model='gpt-4o', temperature=0.7, max_tokens=2000):
        """Get chat response from AI provider"""
        try:
            if model.startswith('gpt-'):
                # OpenAI models
                client = self._get_openai_client()
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": message}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
            elif model.startswith('claude-'):
                # Anthropic models
                client = self._get_anthropic_client()
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text
            
            elif model.startswith('gemini-'):
                # Google models
                client = self._get_google_client()
                headers = {
                    'Content-Type': 'application/json',
                    'x-goog-api-key': client['api_key']
                }
                
                data = {
                    "contents": [{"parts": [{"text": message}]}],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens
                    }
                }
                
                response = requests.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    raise Exception(f"Google AI API error: {response.text}")
            
            elif model in ['llama3', 'mistral', 'codellama']:
                # Ollama models
                client = self._get_ollama_client()
                response = requests.post(
                    f"{client['base_url']}/api/generate",
                    json={
                        "model": model,
                        "prompt": message,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    return response.json()['response']
                else:
                    raise Exception(f"Ollama API error: {response.text}")
            
            else:
                raise ValueError(f"Unsupported model: {model}")
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_image(self, prompt, model='dall-e-3', size='1024x1024', quality='standard'):
        """Generate image using AI provider"""
        try:
            if model.startswith('dall-e'):
                # OpenAI DALL-E
                client = self._get_openai_client()
                response = client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    n=1
                )
                return response.data[0].url
            
            elif model == 'midjourney':
                # Midjourney API (requires separate service)
                # This would integrate with Midjourney API
                return "https://example.com/midjourney-image.png"
            
            elif model == 'stable-diffusion':
                # Stable Diffusion API
                # This would integrate with Stability AI API
                return "https://example.com/stable-diffusion-image.png"
            
            else:
                raise ValueError(f"Unsupported image model: {model}")
        
        except Exception as e:
            raise Exception(f"Image generation error: {str(e)}")
    
    def get_embeddings(self, text, model='text-embedding-3-small'):
        """Get text embeddings"""
        try:
            if model.startswith('text-embedding'):
                # OpenAI embeddings
                client = self._get_openai_client()
                response = client.embeddings.create(
                    model=model,
                    input=text
                )
                return response.data[0].embedding
            
            elif model.startswith('embed-'):
                # Cohere embeddings
                client = self._get_cohere_client()
                headers = {
                    'Authorization': f'Bearer {client["api_key"]}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    "texts": [text],
                    "model": model
                }
                
                response = requests.post(
                    'https://api.cohere.ai/v1/embed',
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    return response.json()['embeddings'][0]
                else:
                    raise Exception(f"Cohere API error: {response.text}")
            
            else:
                raise ValueError(f"Unsupported embedding model: {model}")
        
        except Exception as e:
            raise Exception(f"Embedding error: {str(e)}")
    
    def get_available_models(self):
        """Get list of available models"""
        return {
            'chat': {
                'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
                'anthropic': ['claude-sonnet-4-20250514', 'claude-3-7-sonnet-20250219', 'claude-3-haiku-20240307'],
                'google': ['gemini-pro', 'gemini-pro-vision'],
                'ollama': ['llama3', 'mistral', 'codellama']
            },
            'image': {
                'openai': ['dall-e-3', 'dall-e-2'],
                'midjourney': ['midjourney'],
                'stability': ['stable-diffusion-xl', 'stable-diffusion-2']
            },
            'embedding': {
                'openai': ['text-embedding-3-small', 'text-embedding-3-large'],
                'cohere': ['embed-english-v3.0', 'embed-multilingual-v3.0']
            }
        }
