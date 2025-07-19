import os
import logging
from openai import OpenAI

class OpenAIService:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = "gpt-4o"
    
    def generate_response(self, messages, model=None, temperature=0.7, max_tokens=2048):
        """Generate a response using OpenAI's chat completion API"""
        if model is None:
            model = self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"OpenAI API error: {str(e)}")
            raise e
    
    def generate_image(self, prompt, size="1024x1024", quality="standard"):
        """Generate an image using DALL-E"""
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size=size,
                quality=quality
            )
            
            return response.data[0].url
            
        except Exception as e:
            logging.error(f"DALL-E API error: {str(e)}")
            raise e
    
    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using Whisper"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return response.text
            
        except Exception as e:
            logging.error(f"Whisper API error: {str(e)}")
            raise e
    
    def create_embedding(self, text, model="text-embedding-3-small"):
        """Create embeddings for text"""
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logging.error(f"Embedding API error: {str(e)}")
            raise e
    
    def fine_tune_model(self, training_file_id, model="gpt-3.5-turbo"):
        """Create a fine-tuning job"""
        try:
            response = self.client.fine_tuning.jobs.create(
                training_file=training_file_id,
                model=model
            )
            
            return response.id
            
        except Exception as e:
            logging.error(f"Fine-tuning API error: {str(e)}")
            raise e
    
    def get_available_models(self):
        """Get list of available models"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
            
        except Exception as e:
            logging.error(f"Models API error: {str(e)}")
            raise e
