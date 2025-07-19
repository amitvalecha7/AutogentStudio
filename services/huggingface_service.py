"""
Huggingface Local API Service for Autogent Studio
Provides local Huggingface model inference capabilities
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class HuggingfaceService:
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize Huggingface service
        
        Args:
            base_url: Base URL for local Huggingface inference server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def check_health(self) -> bool:
        """Check if Huggingface server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"Huggingface server health check failed: {e}")
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to list Huggingface models: {e}")
            return []
    
    def generate_text(self, 
                     prompt: str, 
                     model: str = "microsoft/DialoGPT-large",
                     max_length: int = 512,
                     temperature: float = 0.7,
                     top_p: float = 0.9,
                     do_sample: bool = True) -> str:
        """
        Generate text using local Huggingface model
        
        Args:
            prompt: Input text prompt
            model: Model name/identifier
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            do_sample: Whether to use sampling
            
        Returns:
            Generated text response
        """
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": do_sample,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": False
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/models/{model}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            
            return result.get("generated_text", "")
            
        except requests.RequestException as e:
            logger.error(f"Huggingface text generation failed: {e}")
            raise Exception(f"Failed to generate text: {str(e)}")
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = "microsoft/DialoGPT-large",
                       max_tokens: int = 512,
                       temperature: float = 0.7) -> Dict[str, Any]:
        """
        Chat completion using Huggingface model
        
        Args:
            messages: List of chat messages
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Chat completion response
        """
        try:
            # Convert messages to prompt format
            prompt = self._format_chat_prompt(messages)
            
            generated_text = self.generate_text(
                prompt=prompt,
                model=model,
                max_length=max_tokens,
                temperature=temperature
            )
            
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(generated_text.split()),
                    "total_tokens": len(prompt.split()) + len(generated_text.split())
                }
            }
            
        except Exception as e:
            logger.error(f"Huggingface chat completion failed: {e}")
            raise
    
    def embed_text(self, 
                  text: str, 
                  model: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[float]:
        """
        Generate text embeddings
        
        Args:
            text: Input text to embed
            model: Embedding model name
            
        Returns:
            List of embedding values
        """
        try:
            payload = {
                "inputs": text,
                "options": {
                    "wait_for_model": True
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/pipeline/feature-extraction",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            embeddings = response.json()
            
            # Handle different response formats
            if isinstance(embeddings, list):
                if len(embeddings) > 0 and isinstance(embeddings[0], list):
                    return embeddings[0]  # First embedding if batch
                return embeddings
            
            return []
            
        except requests.RequestException as e:
            logger.error(f"Huggingface embedding failed: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Input text
            
        Returns:
            Sentiment analysis result
        """
        try:
            payload = {
                "inputs": text
            }
            
            response = self.session.post(
                f"{self.base_url}/pipeline/sentiment-analysis",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Huggingface sentiment analysis failed: {e}")
            return {"label": "UNKNOWN", "score": 0.0}
    
    def classify_text(self, 
                     text: str, 
                     candidate_labels: List[str],
                     model: str = "facebook/bart-large-mnli") -> Dict[str, Any]:
        """
        Zero-shot text classification
        
        Args:
            text: Input text to classify
            candidate_labels: List of possible labels
            model: Classification model
            
        Returns:
            Classification results
        """
        try:
            payload = {
                "inputs": text,
                "parameters": {
                    "candidate_labels": candidate_labels
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/pipeline/zero-shot-classification",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Huggingface text classification failed: {e}")
            return {"labels": [], "scores": []}
    
    def summarize_text(self, 
                      text: str, 
                      max_length: int = 150,
                      min_length: int = 50,
                      model: str = "facebook/bart-large-cnn") -> str:
        """
        Summarize text using Huggingface model
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
            model: Summarization model
            
        Returns:
            Summary text
        """
        try:
            payload = {
                "inputs": text,
                "parameters": {
                    "max_length": max_length,
                    "min_length": min_length,
                    "do_sample": False
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/pipeline/summarization",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("summary_text", "")
            
            return result.get("summary_text", "")
            
        except requests.RequestException as e:
            logger.error(f"Huggingface summarization failed: {e}")
            return ""
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into a prompt"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

# Global service instance
huggingface_service = HuggingfaceService()