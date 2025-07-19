import os
import logging
from anthropic import Anthropic

class AnthropicService:
    def __init__(self):
        # The newest Anthropic model is "claude-sonnet-4-20250514", not "claude-3-7-sonnet-20250219", 
        # "claude-3-5-sonnet-20241022" nor "claude-3-sonnet-20240229". 
        # If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514" as it is the latest model.
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")
        
        self.client = Anthropic(api_key=self.api_key)
        self.default_model = "claude-sonnet-4-20250514"
    
    def generate_response(self, messages, model=None, temperature=0.7, max_tokens=2048):
        """Generate a response using Anthropic's Claude API"""
        if model is None:
            model = self.default_model
        
        try:
            # Convert messages format if needed
            formatted_messages = []
            system_message = None
            
            for message in messages:
                if message['role'] == 'system':
                    system_message = message['content']
                else:
                    formatted_messages.append({
                        'role': message['role'],
                        'content': message['content']
                    })
            
            response = self.client.messages.create(
                model=model,
                messages=formatted_messages,
                system=system_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.content[0].text
            
        except Exception as e:
            logging.error(f"Anthropic API error: {str(e)}")
            raise e
    
    def constitutional_ai_check(self, response, principles=None):
        """Perform constitutional AI checking on a response"""
        if principles is None:
            principles = [
                "Be helpful and harmless",
                "Avoid bias and discrimination",
                "Respect privacy and confidentiality",
                "Be truthful and accurate"
            ]
        
        try:
            critique_prompt = f"""
Please critique the following AI response according to these constitutional principles:
{chr(10).join(f'- {p}' for p in principles)}

Response to critique: {response}

Provide a critique and suggest improvements if needed.
"""
            
            critique_response = self.client.messages.create(
                model=self.default_model,
                messages=[{
                    'role': 'user',
                    'content': critique_prompt
                }],
                max_tokens=1000
            )
            
            return {
                'original_response': response,
                'critique': critique_response.content[0].text,
                'passes_check': 'problematic' not in critique_response.content[0].text.lower()
            }
            
        except Exception as e:
            logging.error(f"Constitutional AI check error: {str(e)}")
            raise e
    
    def analyze_text_safety(self, text):
        """Analyze text for safety concerns"""
        try:
            safety_prompt = f"""
Please analyze the following text for potential safety concerns including:
- Harmful content
- Bias or discrimination
- Misinformation
- Privacy violations
- Inappropriate content

Text to analyze: {text}

Provide a safety assessment with a score from 1-10 (10 being completely safe).
"""
            
            response = self.client.messages.create(
                model=self.default_model,
                messages=[{
                    'role': 'user',
                    'content': safety_prompt
                }],
                max_tokens=500
            )
            
            return {
                'text': text,
                'safety_analysis': response.content[0].text,
                'timestamp': logging.time()
            }
            
        except Exception as e:
            logging.error(f"Safety analysis error: {str(e)}")
            raise e
    
    def get_available_models(self):
        """Get list of available Claude models"""
        return [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307"
        ]
