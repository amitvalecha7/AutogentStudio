import os
import logging
from typing import Dict, List, Any, Optional
import json

# Import AI provider SDKs
try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None

try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

def get_provider_client(provider: str):
    """Get initialized client for AI provider"""
    if provider == 'openai':
        if not openai:
            raise ImportError("OpenAI SDK not installed")
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return OpenAI(api_key=api_key)
    
    elif provider == 'anthropic':
        if not anthropic:
            raise ImportError("Anthropic SDK not installed")
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return Anthropic(api_key=api_key)
    
    elif provider == 'google':
        if not genai:
            raise ImportError("Google Generative AI SDK not installed")
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        return genai
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def generate_response(provider: str, model: str, messages: List[Dict], 
                     temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """Generate AI response using specified provider and model"""
    try:
        if provider == 'openai':
            client = get_provider_client('openai')
            
            # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # Do not change this unless explicitly requested by the user
            if model == 'gpt-4':
                model = 'gpt-4o'  # Use latest model
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        elif provider == 'anthropic':
            client = get_provider_client('anthropic')
            
            # The newest Anthropic model is "claude-sonnet-4-20250514", not older 3.x models
            # If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514"
            if model in ['claude-3-5-sonnet', 'claude-3-sonnet']:
                model = 'claude-sonnet-4-20250514'
            
            # Convert messages format for Anthropic
            system_message = None
            conversation_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    conversation_messages.append(msg)
            
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=conversation_messages
            )
            return response.content[0].text
        
        elif provider == 'google':
            genai_client = get_provider_client('google')
            
            # Convert messages to Google format
            prompt_parts = []
            for msg in messages:
                if msg['role'] == 'system':
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg['role'] == 'user':
                    prompt_parts.append(f"Human: {msg['content']}")
                elif msg['role'] == 'assistant':
                    prompt_parts.append(f"Assistant: {msg['content']}")
            
            prompt = "\n".join(prompt_parts) + "\nAssistant:"
            
            model_instance = genai_client.GenerativeModel(model)
            response = model_instance.generate_content(
                prompt,
                generation_config=genai_client.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            return response.text
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
    except Exception as e:
        logging.error(f"Error generating response with {provider}/{model}: {e}")
        raise

def generate_image(prompt: str, provider: str = 'openai', model: str = 'dall-e-3',
                  style: str = 'realistic', size: str = '1024x1024') -> Dict[str, Any]:
    """Generate image using AI provider"""
    try:
        if provider == 'openai':
            client = get_provider_client('openai')
            
            # Enhance prompt based on style
            enhanced_prompt = enhance_image_prompt(prompt, style)
            
            response = client.images.generate(
                model=model,
                prompt=enhanced_prompt,
                size=size,
                quality="hd" if model == 'dall-e-3' else "standard",
                n=1
            )
            
            return {
                'url': response.data[0].url,
                'revised_prompt': getattr(response.data[0], 'revised_prompt', prompt)
            }
        
        elif provider == 'midjourney':
            # Placeholder for Midjourney integration
            # In a real implementation, you would integrate with Midjourney API
            raise NotImplementedError("Midjourney integration not implemented")
        
        elif provider == 'stable_diffusion':
            # Placeholder for Stable Diffusion integration
            raise NotImplementedError("Stable Diffusion integration not implemented")
        
        else:
            raise ValueError(f"Unsupported image provider: {provider}")
            
    except Exception as e:
        logging.error(f"Error generating image with {provider}/{model}: {e}")
        raise

def enhance_image_prompt(prompt: str, style: str) -> str:
    """Enhance image prompt based on style"""
    style_enhancements = {
        'realistic': 'photorealistic, high quality, detailed',
        'artistic': 'artistic style, creative interpretation, beautiful',
        'cartoon': 'cartoon style, animated, colorful',
        'sketch': 'hand-drawn sketch, pencil drawing, artistic',
        'abstract': 'abstract art, modern, creative',
        'digital_art': 'digital art, concept art, highly detailed',
        'oil_painting': 'oil painting style, classical art, masterpiece',
        'watercolor': 'watercolor painting, soft colors, artistic'
    }
    
    enhancement = style_enhancements.get(style, '')
    if enhancement:
        return f"{prompt}, {enhancement}"
    return prompt

def get_available_models() -> Dict[str, List[Dict]]:
    """Get list of available models for each provider"""
    models = {
        'openai': [
            {
                'id': 'gpt-4o',
                'name': 'GPT-4 Omni',
                'description': 'Most capable multimodal model',
                'context_window': 128000,
                'capabilities': ['text', 'vision', 'function_calling']
            },
            {
                'id': 'gpt-4o-mini',
                'name': 'GPT-4 Omni Mini',
                'description': 'Faster and more affordable GPT-4',
                'context_window': 128000,
                'capabilities': ['text', 'vision', 'function_calling']
            },
            {
                'id': 'gpt-3.5-turbo',
                'name': 'GPT-3.5 Turbo',
                'description': 'Fast and capable for most tasks',
                'context_window': 16385,
                'capabilities': ['text', 'function_calling']
            }
        ],
        'anthropic': [
            {
                'id': 'claude-sonnet-4-20250514',
                'name': 'Claude 4 Sonnet',
                'description': 'Most capable Claude model',
                'context_window': 200000,
                'capabilities': ['text', 'vision', 'function_calling']
            },
            {
                'id': 'claude-3-5-sonnet-20241022',
                'name': 'Claude 3.5 Sonnet',
                'description': 'Previous generation Claude',
                'context_window': 200000,
                'capabilities': ['text', 'vision', 'function_calling']
            }
        ],
        'google': [
            {
                'id': 'gemini-1.5-pro',
                'name': 'Gemini 1.5 Pro',
                'description': 'Extremely large context window',
                'context_window': 2000000,
                'capabilities': ['text', 'vision', 'function_calling']
            },
            {
                'id': 'gemini-1.5-flash',
                'name': 'Gemini 1.5 Flash',
                'description': 'Fast and efficient',
                'context_window': 1000000,
                'capabilities': ['text', 'vision', 'function_calling']
            }
        ]
    }
    
    # Filter models based on available API keys
    available_models = {}
    
    if os.environ.get('OPENAI_API_KEY'):
        available_models['openai'] = models['openai']
    
    if os.environ.get('ANTHROPIC_API_KEY'):
        available_models['anthropic'] = models['anthropic']
    
    if os.environ.get('GOOGLE_API_KEY'):
        available_models['google'] = models['google']
    
    return available_models

def validate_model_config(provider: str, model: str) -> bool:
    """Validate if model is available for provider"""
    available_models = get_available_models()
    
    if provider not in available_models:
        return False
    
    provider_models = [m['id'] for m in available_models[provider]]
    return model in provider_models

def estimate_tokens(text: str) -> int:
    """Estimate token count for text (simplified)"""
    # Simple estimation: ~4 characters per token
    return len(text) // 4

def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate API cost based on provider and token usage"""
    # Simplified cost calculation (actual costs may vary)
    cost_per_1k_tokens = {
        'openai': {
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015}
        },
        'anthropic': {
            'claude-sonnet-4-20250514': {'input': 0.003, 'output': 0.015},
            'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015}
        },
        'google': {
            'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
            'gemini-1.5-flash': {'input': 0.000075, 'output': 0.0003}
        }
    }
    
    if provider not in cost_per_1k_tokens or model not in cost_per_1k_tokens[provider]:
        return 0.0
    
    rates = cost_per_1k_tokens[provider][model]
    input_cost = (input_tokens / 1000) * rates['input']
    output_cost = (output_tokens / 1000) * rates['output']
    
    return input_cost + output_cost

def get_embedding(text: str, model: str = 'text-embedding-3-small') -> List[float]:
    """Generate text embedding using OpenAI"""
    try:
        client = get_provider_client('openai')
        
        response = client.embeddings.create(
            model=model,
            input=text
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        raise

def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio using OpenAI Whisper"""
    try:
        client = get_provider_client('openai')
        
        with open(audio_file_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        return response.text
        
    except Exception as e:
        logging.error(f"Error transcribing audio: {e}")
        raise

def text_to_speech(text: str, voice: str = 'alloy') -> bytes:
    """Convert text to speech using OpenAI TTS"""
    try:
        client = get_provider_client('openai')
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        return response.content
        
    except Exception as e:
        logging.error(f"Error generating speech: {e}")
        raise
