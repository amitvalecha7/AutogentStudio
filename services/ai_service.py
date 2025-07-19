import os
import json
import requests
from typing import Dict, List, Any, Optional, Generator
import openai
import anthropic
from anthropic import Anthropic
import google.generativeai as genai
import cohere

# <important_code_snippet_instructions>
# The newest OpenAI model is "gpt-4o", not older versions
# The newest Anthropic model is "claude-sonnet-4-20250514", not older models
# When copying code from this service, ensure you use the latest models
# </important_code_snippet_instructions>

class AIService:
    def __init__(self):
        # Initialize AI service clients
        self.openai_client = None
        self.anthropic_client = None
        self.google_client = None
        self.cohere_client = None
        
        # Initialize OpenAI
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)
        
        # Initialize Anthropic - newest model is "claude-sonnet-4-20250514"
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        if anthropic_key:
            self.anthropic_client = Anthropic(api_key=anthropic_key)
        
        # Initialize Google AI
        google_key = os.environ.get('GOOGLE_API_KEY')
        if google_key:
            genai.configure(api_key=google_key)
            self.google_client = genai.GenerativeModel('gemini-pro')
        
        # Initialize Cohere
        cohere_key = os.environ.get('COHERE_API_KEY')
        if cohere_key:
            self.cohere_client = cohere.Client(cohere_key)
    
    def chat_completion(self, messages: List[Dict], provider: str = 'openai', 
                       model: str = None, settings: Dict = None) -> Dict:
        """Generate chat completion using specified AI provider"""
        
        if not settings:
            settings = {}
        
        try:
            if provider == 'openai':
                return self._openai_chat_completion(messages, model or 'gpt-4o', settings)
            elif provider == 'anthropic':
                return self._anthropic_chat_completion(messages, model or 'claude-sonnet-4-20250514', settings)
            elif provider == 'google':
                return self._google_chat_completion(messages, model or 'gemini-pro', settings)
            elif provider == 'cohere':
                return self._cohere_chat_completion(messages, model or 'command', settings)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        
        except Exception as e:
            raise Exception(f"AI service error ({provider}): {str(e)}")
    
    def _openai_chat_completion(self, messages: List[Dict], model: str, settings: Dict) -> Dict:
        """OpenAI chat completion - newest model is "gpt-4o" """
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=settings.get('temperature', 0.7),
            max_tokens=settings.get('max_tokens', 2048),
            top_p=settings.get('top_p', 1.0),
            frequency_penalty=settings.get('frequency_penalty', 0.0),
            presence_penalty=settings.get('presence_penalty', 0.0)
        )
        
        return {
            'content': response.choices[0].message.content,
            'model': model,
            'tokens_used': response.usage.total_tokens,
            'cost': self._calculate_openai_cost(model, response.usage)
        }
    
    def _anthropic_chat_completion(self, messages: List[Dict], model: str, settings: Dict) -> Dict:
        """Anthropic chat completion - newest model is "claude-sonnet-4-20250514" """
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")
        
        # Convert messages format
        system_message = ""
        conversation_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                conversation_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=settings.get('max_tokens', 2048),
            temperature=settings.get('temperature', 0.7),
            system=system_message if system_message else None,
            messages=conversation_messages
        )
        
        return {
            'content': response.content[0].text,
            'model': model,
            'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
            'cost': self._calculate_anthropic_cost(model, response.usage)
        }
    
    def _google_chat_completion(self, messages: List[Dict], model: str, settings: Dict) -> Dict:
        """Google AI chat completion"""
        if not self.google_client:
            raise Exception("Google AI client not initialized")
        
        # Convert messages to Google format
        prompt = ""
        for msg in messages:
            if msg['role'] == 'system':
                prompt += f"System: {msg['content']}\n"
            elif msg['role'] == 'user':
                prompt += f"Human: {msg['content']}\n"
            elif msg['role'] == 'assistant':
                prompt += f"Assistant: {msg['content']}\n"
        
        prompt += "Assistant:"
        
        response = self.google_client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=settings.get('temperature', 0.7),
                max_output_tokens=settings.get('max_tokens', 2048),
                top_p=settings.get('top_p', 1.0)
            )
        )
        
        return {
            'content': response.text,
            'model': model,
            'tokens_used': response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
            'cost': 0.0  # Google AI pricing varies
        }
    
    def _cohere_chat_completion(self, messages: List[Dict], model: str, settings: Dict) -> Dict:
        """Cohere chat completion"""
        if not self.cohere_client:
            raise Exception("Cohere client not initialized")
        
        # Convert messages to Cohere chat format
        chat_history = []
        current_message = ""
        
        for msg in messages[:-1]:  # All but last message
            if msg['role'] == 'user':
                chat_history.append({"role": "USER", "message": msg['content']})
            elif msg['role'] == 'assistant':
                chat_history.append({"role": "CHATBOT", "message": msg['content']})
        
        # Last message should be the current user message
        if messages and messages[-1]['role'] == 'user':
            current_message = messages[-1]['content']
        
        response = self.cohere_client.chat(
            model=model,
            message=current_message,
            chat_history=chat_history,
            temperature=settings.get('temperature', 0.7),
            max_tokens=settings.get('max_tokens', 2048)
        )
        
        return {
            'content': response.text,
            'model': model,
            'tokens_used': response.meta.billed_units.input_tokens + response.meta.billed_units.output_tokens if hasattr(response, 'meta') else 0,
            'cost': 0.0  # Would need Cohere pricing calculation
        }
    
    def stream_chat_completion(self, messages: List[Dict], provider: str = 'openai', 
                              model: str = None, settings: Dict = None) -> Generator[Dict, None, None]:
        """Stream chat completion for real-time responses"""
        
        if not settings:
            settings = {}
        
        try:
            if provider == 'openai':
                yield from self._openai_stream_completion(messages, model or 'gpt-4o', settings)
            elif provider == 'anthropic':
                yield from self._anthropic_stream_completion(messages, model or 'claude-sonnet-4-20250514', settings)
            else:
                # For non-streaming providers, yield the complete response
                response = self.chat_completion(messages, provider, model, settings)
                yield {'content': response['content'], 'done': True}
        
        except Exception as e:
            yield {'error': f"Streaming error ({provider}): {str(e)}"}
    
    def _openai_stream_completion(self, messages: List[Dict], model: str, settings: Dict) -> Generator[Dict, None, None]:
        """OpenAI streaming completion"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        stream = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=settings.get('temperature', 0.7),
            max_tokens=settings.get('max_tokens', 2048),
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield {
                    'content': chunk.choices[0].delta.content,
                    'done': False
                }
        
        yield {'done': True}
    
    def _anthropic_stream_completion(self, messages: List[Dict], model: str, settings: Dict) -> Generator[Dict, None, None]:
        """Anthropic streaming completion"""
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")
        
        # Convert messages format
        system_message = ""
        conversation_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                conversation_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=settings.get('max_tokens', 2048),
            temperature=settings.get('temperature', 0.7),
            system=system_message if system_message else None,
            messages=conversation_messages
        ) as stream:
            for text in stream.text_stream:
                yield {
                    'content': text,
                    'done': False
                }
        
        yield {'done': True}
    
    def generate_image_openai(self, prompt: str, size: str = "1024x1024", 
                             quality: str = "standard", n: int = 1) -> Dict:
        """Generate image using OpenAI DALL-E"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        response = self.openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=min(n, 1)  # DALL-E 3 only supports n=1
        )
        
        return {
            'images': [{'url': image.url} for image in response.data],
            'model': 'dall-e-3',
            'prompt': prompt
        }
    
    def generate_image_midjourney(self, prompt: str, aspect_ratio: str = "1:1", style: str = "natural") -> Dict:
        """Generate image using Midjourney API (placeholder - would need actual API)"""
        # This would integrate with actual Midjourney API
        return {
            'images': [{'url': f'https://via.placeholder.com/1024x1024.png?text=Midjourney+Image'}],
            'model': 'midjourney',
            'prompt': prompt,
            'note': 'Midjourney integration placeholder - requires actual API setup'
        }
    
    def generate_image_pollinations(self, prompt: str, width: int = 1024, height: int = 1024) -> Dict:
        """Generate image using Pollinations AI (free service)"""
        try:
            # Pollinations.ai free image generation
            encoded_prompt = requests.utils.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}"
            
            return {
                'images': [{'url': image_url}],
                'model': 'pollinations',
                'prompt': prompt
            }
        except Exception as e:
            raise Exception(f"Pollinations image generation error: {str(e)}")
    
    def analyze_image(self, base64_image: str, prompt: str = None) -> str:
        """Analyze image using vision-capable models"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        if not prompt:
            prompt = "Analyze this image in detail and describe its key elements, context, and any notable aspects."
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",  # Vision-capable model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def upscale_image(self, image_data: str) -> Dict:
        """Upscale image using AI (placeholder for actual upscaling service)"""
        return {
            'image_url': 'https://via.placeholder.com/2048x2048.png?text=Upscaled+Image',
            'note': 'Image upscaling placeholder - requires actual upscaling service'
        }
    
    def denoise_image(self, image_data: str) -> Dict:
        """Denoise image (placeholder)"""
        return {
            'image_url': 'https://via.placeholder.com/1024x1024.png?text=Denoised+Image',
            'note': 'Image denoising placeholder'
        }
    
    def colorize_image(self, image_data: str) -> Dict:
        """Colorize black and white image (placeholder)"""
        return {
            'image_url': 'https://via.placeholder.com/1024x1024.png?text=Colorized+Image',
            'note': 'Image colorization placeholder'
        }
    
    def detect_objects(self, image_data: str) -> Dict:
        """Detect objects in image"""
        analysis = self.analyze_image(image_data, "Identify and list all objects visible in this image.")
        return {
            'objects': analysis,
            'note': 'Object detection using vision model analysis'
        }
    
    def extract_text_from_image(self, image_data: str) -> Dict:
        """Extract text from image (OCR)"""
        analysis = self.analyze_image(image_data, "Extract and transcribe all text visible in this image.")
        return {
            'text': analysis,
            'note': 'Text extraction using vision model'
        }
    
    def create_image_variations(self, image_data: str, n: int = 3, strength: float = 0.7) -> Dict:
        """Create variations of an image"""
        # This would use actual image variation APIs
        return {
            'images': [
                {'url': f'https://via.placeholder.com/1024x1024.png?text=Variation+{i+1}'}
                for i in range(n)
            ],
            'note': 'Image variations placeholder'
        }
    
    def edit_image(self, image_data: str, mask_data: str = None, prompt: str = "") -> Dict:
        """Edit image with AI (inpainting/outpainting)"""
        return {
            'image_url': 'https://via.placeholder.com/1024x1024.png?text=Edited+Image',
            'prompt': prompt,
            'note': 'Image editing placeholder'
        }
    
    def _calculate_openai_cost(self, model: str, usage) -> float:
        """Calculate OpenAI API costs"""
        # Pricing as of 2024 (would need to be updated with current pricing)
        pricing = {
            'gpt-4o': {'input': 0.005, 'output': 0.015},  # per 1K tokens
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015}
        }
        
        if model not in pricing:
            return 0.0
        
        input_cost = (usage.prompt_tokens / 1000) * pricing[model]['input']
        output_cost = (usage.completion_tokens / 1000) * pricing[model]['output']
        
        return input_cost + output_cost
    
    def _calculate_anthropic_cost(self, model: str, usage) -> float:
        """Calculate Anthropic API costs"""
        # Anthropic pricing (would need current pricing)
        pricing = {
            'claude-sonnet-4-20250514': {'input': 0.003, 'output': 0.015},
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015}
        }
        
        if model not in pricing:
            return 0.0
        
        input_cost = (usage.input_tokens / 1000) * pricing[model]['input']
        output_cost = (usage.output_tokens / 1000) * pricing[model]['output']
        
        return input_cost + output_cost
    
    def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Get text embeddings for vector operations"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        response = self.openai_client.embeddings.create(
            model=model,
            input=text
        )
        
        return response.data[0].embedding
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio using Whisper"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        with open(audio_file_path, "rb") as audio_file:
            response = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        return response.text
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """Convert text to speech"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        response = self.openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        return response.content
