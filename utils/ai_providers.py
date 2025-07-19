import os
import openai
import anthropic
from openai import OpenAI
from anthropic import Anthropic

# <important_code_snippet_instructions>
# The newest OpenAI model is "gpt-4o", not "gpt-4".
# The newest Anthropic model is "claude-sonnet-4-20250514", not older 3.x models.
# Always prefer using these latest models unless explicitly requested otherwise.
# </important_code_snippet_instructions>

class AIProviders:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI provider clients"""
        # OpenAI Client
        openai_key = os.environ.get('OPENAI_API_KEY', 'default_openai_key')
        if openai_key and openai_key != 'default_openai_key':
            self.openai_client = OpenAI(api_key=openai_key)
        
        # Anthropic Client
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY', 'default_anthropic_key')
        if anthropic_key and anthropic_key != 'default_anthropic_key':
            self.anthropic_client = Anthropic(api_key=anthropic_key)
    
    def chat_with_openai(self, messages, model='gpt-4o', **kwargs):
        """Chat with OpenAI models"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Please check API key.")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def chat_with_anthropic(self, messages, model='claude-sonnet-4-20250514', **kwargs):
        """Chat with Anthropic models"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized. Please check API key.")
        
        try:
            # Convert messages format for Anthropic
            system_message = ""
            anthropic_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    anthropic_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            response = self.anthropic_client.messages.create(
                model=model,
                messages=anthropic_messages,
                system=system_message if system_message else anthropic.NOT_GIVEN,
                max_tokens=kwargs.get('max_tokens', 4000),
                **{k: v for k, v in kwargs.items() if k != 'max_tokens'}
            )
            return response
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def generate_image(self, prompt, model='dall-e-3', **kwargs):
        """Generate images with DALL-E"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Please check API key.")
        
        try:
            response = self.openai_client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=kwargs.get('size', '1024x1024'),
                **{k: v for k, v in kwargs.items() if k != 'size'}
            )
            return response
        except Exception as e:
            raise Exception(f"Image generation error: {str(e)}")
    
    def get_available_models(self, provider='openai'):
        """Get available models for a provider"""
        models = {
            'openai': [
                'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo',
                'dall-e-3', 'dall-e-2', 'whisper-1', 'tts-1'
            ],
            'anthropic': [
                'claude-sonnet-4-20250514', 'claude-3-7-sonnet-20250219',
                'claude-3-5-sonnet-20241022', 'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307'
            ]
        }
        return models.get(provider, [])

# Global instance
ai_providers = AIProviders()
