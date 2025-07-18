import os
import logging
from anthropic import Anthropic

class AnthropicService:
    def __init__(self):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            logging.warning("Anthropic API key not found in environment variables")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)
    
    def chat_completion(self, message, model='claude-sonnet-4-20250514', max_tokens=2000):
        """
        Get chat completion from Anthropic Claude
        # The newest Anthropic model is "claude-sonnet-4-20250514", not "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022" nor "claude-3-sonnet-20240229".
        # If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514" as it is the latest model.
        """
        if not self.client:
            raise Exception("Anthropic client not initialized - API key missing")
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            
            return {
                'content': response.content[0].text,
                'model': model,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
        except Exception as e:
            logging.error(f"Anthropic chat completion error: {str(e)}")
            raise
    
    def analyze_image(self, image_data, prompt, model='claude-sonnet-4-20250514'):
        """Analyze image with Claude"""
        if not self.client:
            raise Exception("Anthropic client not initialized - API key missing")
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            return {
                'content': response.content[0].text,
                'model': model
            }
        except Exception as e:
            logging.error(f"Anthropic image analysis error: {str(e)}")
            raise
