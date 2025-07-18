import os
import openai
import anthropic
from typing import List, Dict, Any
from models import Chat, Message, APIKey
from utils.encryption import decrypt_api_key

class AIService:
    def __init__(self):
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.default_openai_model = "gpt-4o"
        
        # The newest Anthropic model is "claude-sonnet-4-20250514", not "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022" nor "claude-3-sonnet-20240229". 
        # If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514" as it is the latest model.
        self.default_anthropic_model = "claude-sonnet-4-20250514"
    
    def get_openai_client(self, user_id: str):
        """Get OpenAI client with user's API key"""
        api_key_record = APIKey.query.filter_by(user_id=user_id, provider='openai', is_active=True).first()
        
        if not api_key_record:
            # Fallback to environment variable
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not configured")
        else:
            api_key = decrypt_api_key(api_key_record.encrypted_key)
        
        return openai.OpenAI(api_key=api_key)
    
    def get_anthropic_client(self, user_id: str):
        """Get Anthropic client with user's API key"""
        api_key_record = APIKey.query.filter_by(user_id=user_id, provider='anthropic', is_active=True).first()
        
        if not api_key_record:
            # Fallback to environment variable
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("Anthropic API key not configured")
        else:
            api_key = decrypt_api_key(api_key_record.encrypted_key)
        
        return anthropic.Anthropic(api_key=api_key)
    
    def get_chat_response(self, chat: Chat, message: str) -> str:
        """Get AI response for chat message"""
        try:
            # Get conversation history
            messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at.asc()).all()
            
            # Build conversation context
            conversation = []
            
            # Add system prompt if exists
            if chat.system_prompt:
                conversation.append({"role": "system", "content": chat.system_prompt})
            
            # Add message history
            for msg in messages:
                conversation.append({"role": msg.role, "content": msg.content})
            
            # Add current message
            conversation.append({"role": "user", "content": message})
            
            # Determine provider based on model
            if chat.model.startswith('gpt-') or chat.model.startswith('o1-'):
                return self._get_openai_response(chat, conversation)
            elif chat.model.startswith('claude-'):
                return self._get_anthropic_response(chat, conversation)
            else:
                # Default to OpenAI
                return self._get_openai_response(chat, conversation)
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_openai_response(self, chat: Chat, conversation: List[Dict[str, str]]) -> str:
        """Get response from OpenAI"""
        client = self.get_openai_client(chat.user_id)
        
        response = client.chat.completions.create(
            model=chat.model or self.default_openai_model,
            messages=conversation,
            temperature=chat.temperature or 0.7,
            max_tokens=chat.max_tokens or 2048
        )
        
        return response.choices[0].message.content
    
    def _get_anthropic_response(self, chat: Chat, conversation: List[Dict[str, str]]) -> str:
        """Get response from Anthropic"""
        client = self.get_anthropic_client(chat.user_id)
        
        # Convert conversation format for Anthropic
        anthropic_messages = []
        system_prompt = None
        
        for msg in conversation:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        kwargs = {
            "model": chat.model or self.default_anthropic_model,
            "messages": anthropic_messages,
            "max_tokens": chat.max_tokens or 2048,
            "temperature": chat.temperature or 0.7
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = client.messages.create(**kwargs)
        
        return response.content[0].text
    
    def generate_image(self, user_id: str, prompt: str, model: str = "dall-e-3") -> Dict[str, Any]:
        """Generate image using DALL-E"""
        try:
            client = self.get_openai_client(user_id)
            
            response = client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard"
            )
            
            return {
                "url": response.data[0].url,
                "revised_prompt": getattr(response.data[0], 'revised_prompt', prompt)
            }
            
        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")
    
    def transcribe_audio(self, user_id: str, audio_file_path: str) -> str:
        """Transcribe audio using Whisper"""
        try:
            client = self.get_openai_client(user_id)
            
            with open(audio_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Audio transcription failed: {str(e)}")
    
    def text_to_speech(self, user_id: str, text: str, voice: str = "alloy") -> str:
        """Convert text to speech"""
        try:
            client = self.get_openai_client(user_id)
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                response.stream_to_file(tmp_file.name)
                return tmp_file.name
            
        except Exception as e:
            raise Exception(f"Text to speech failed: {str(e)}")
    
    def analyze_sentiment(self, user_id: str, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        try:
            client = self.get_openai_client(user_id)
            
            response = client.chat.completions.create(
                model=self.default_openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Analyze the sentiment of the text and provide a rating from 1 to 5 stars and a confidence score between 0 and 1. Respond with JSON in this format: {'rating': number, 'confidence': number, 'sentiment': 'positive/negative/neutral'}"
                    },
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return {
                "rating": max(1, min(5, round(result["rating"]))),
                "confidence": max(0, min(1, result["confidence"])),
                "sentiment": result.get("sentiment", "neutral")
            }
            
        except Exception as e:
            raise Exception(f"Sentiment analysis failed: {str(e)}")
    
    def summarize_text(self, user_id: str, text: str, max_length: int = 150) -> str:
        """Summarize text"""
        try:
            client = self.get_openai_client(user_id)
            
            response = client.chat.completions.create(
                model=self.default_openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Summarize the following text in approximately {max_length} words while maintaining key points:"
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Text summarization failed: {str(e)}")
    
    def get_available_models(self, user_id: str) -> Dict[str, List[str]]:
        """Get available models for user"""
        models = {
            "openai": [],
            "anthropic": [],
            "google": [],
            "local": []
        }
        
        # Check if user has API keys configured
        openai_key = APIKey.query.filter_by(user_id=user_id, provider='openai', is_active=True).first()
        if openai_key or os.environ.get('OPENAI_API_KEY'):
            models["openai"] = [
                "gpt-4o",
                "gpt-4",
                "gpt-3.5-turbo",
                "o1-preview",
                "o1-mini"
            ]
        
        anthropic_key = APIKey.query.filter_by(user_id=user_id, provider='anthropic', is_active=True).first()
        if anthropic_key or os.environ.get('ANTHROPIC_API_KEY'):
            models["anthropic"] = [
                "claude-sonnet-4-20250514",
                "claude-3-7-sonnet-20250219",
                "claude-3-5-sonnet-20241022",
                "claude-3-haiku-20240307"
            ]
        
        return models
