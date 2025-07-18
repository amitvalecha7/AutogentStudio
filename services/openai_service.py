import os
import logging
from openai import OpenAI

class OpenAIService:
    def __init__(self):
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logging.warning("OpenAI API key not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
    
    def chat_completion(self, message, model='gpt-4o', temperature=0.7, max_tokens=2000):
        """
        Get chat completion from OpenAI
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        """
        if not self.client:
            raise Exception("OpenAI client not initialized - API key missing")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                'content': response.choices[0].message.content,
                'model': model,
                'usage': response.usage.dict() if response.usage else None
            }
        except Exception as e:
            logging.error(f"OpenAI chat completion error: {str(e)}")
            raise
    
    def generate_image(self, prompt, model='dall-e-3', size='1024x1024'):
        """Generate image using DALL-E"""
        if not self.client:
            raise Exception("OpenAI client not initialized - API key missing")
        
        try:
            response = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            return {
                'url': response.data[0].url,
                'revised_prompt': response.data[0].revised_prompt
            }
        except Exception as e:
            logging.error(f"OpenAI image generation error: {str(e)}")
            raise
    
    def create_embedding(self, text, model='text-embedding-3-small'):
        """Create embedding for text"""
        if not self.client:
            raise Exception("OpenAI client not initialized - API key missing")
        
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return {
                'embedding': response.data[0].embedding,
                'model': model,
                'usage': response.usage.dict() if response.usage else None
            }
        except Exception as e:
            logging.error(f"OpenAI embedding error: {str(e)}")
            raise
    
    def transcribe_audio(self, audio_file_path, model='whisper-1'):
        """Transcribe audio file"""
        if not self.client:
            raise Exception("OpenAI client not initialized - API key missing")
        
        try:
            with open(audio_file_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=model,
                    file=audio_file
                )
            
            return {
                'text': response.text,
                'model': model
            }
        except Exception as e:
            logging.error(f"OpenAI transcription error: {str(e)}")
            raise
    
    def create_fine_tuning_job(self, training_file_id, model='gpt-3.5-turbo'):
        """Create fine-tuning job"""
        if not self.client:
            raise Exception("OpenAI client not initialized - API key missing")
        
        try:
            response = self.client.fine_tuning.jobs.create(
                training_file=training_file_id,
                model=model
            )
            
            return {
                'job_id': response.id,
                'status': response.status,
                'model': model
            }
        except Exception as e:
            logging.error(f"OpenAI fine-tuning error: {str(e)}")
            raise
