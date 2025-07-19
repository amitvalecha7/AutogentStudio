"""
Ollama Local API Service for Autogent Studio
Provides local Ollama model inference capabilities
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional, Generator
from flask import current_app

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama service
        
        Args:
            base_url: Base URL for local Ollama server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def check_health(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"Ollama server health check failed: {e}")
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except requests.RequestException as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {"name": model_name}
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                stream=True
            )
            
            response.raise_for_status()
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if data.get("status") == "success":
                        return True
                    elif "error" in data:
                        logger.error(f"Model pull error: {data['error']}")
                        return False
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def generate_text(self, 
                     prompt: str, 
                     model: str = "llama2",
                     stream: bool = False,
                     **kwargs) -> str:
        """
        Generate text using Ollama model
        
        Args:
            prompt: Input text prompt
            model: Model name
            stream: Whether to stream response
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=stream
            )
            
            response.raise_for_status()
            
            if stream:
                return self._handle_stream_response(response)
            else:
                result = response.json()
                return result.get("response", "")
            
        except requests.RequestException as e:
            logger.error(f"Ollama text generation failed: {e}")
            raise Exception(f"Failed to generate text: {str(e)}")
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = "llama2",
                       stream: bool = False,
                       **kwargs) -> Dict[str, Any]:
        """
        Chat completion using Ollama model
        
        Args:
            messages: List of chat messages
            model: Model name
            stream: Whether to stream response
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=stream
            )
            
            response.raise_for_status()
            
            if stream:
                content = self._handle_stream_response(response)
            else:
                result = response.json()
                content = result.get("message", {}).get("content", "")
            
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": sum(len(msg.get("content", "").split()) for msg in messages),
                    "completion_tokens": len(content.split()),
                    "total_tokens": sum(len(msg.get("content", "").split()) for msg in messages) + len(content.split())
                }
            }
            
        except requests.RequestException as e:
            logger.error(f"Ollama chat completion failed: {e}")
            raise
    
    def embed_text(self, text: str, model: str = "llama2") -> List[float]:
        """
        Generate text embeddings
        
        Args:
            text: Input text to embed
            model: Model name
            
        Returns:
            List of embedding values
        """
        try:
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = self.session.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
            
        except requests.RequestException as e:
            logger.error(f"Ollama embedding failed: {e}")
            return []
    
    def create_model(self, 
                    name: str, 
                    modelfile: str,
                    stream: bool = False) -> bool:
        """
        Create a custom model
        
        Args:
            name: Name for the new model
            modelfile: Modelfile content
            stream: Whether to stream response
            
        Returns:
            True if successful
        """
        try:
            payload = {
                "name": name,
                "modelfile": modelfile,
                "stream": stream
            }
            
            response = self.session.post(
                f"{self.base_url}/api/create",
                json=payload,
                stream=stream
            )
            
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get("status") == "success":
                            return True
                        elif "error" in data:
                            logger.error(f"Model creation error: {data['error']}")
                            return False
            else:
                return True
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to create model {name}: {e}")
            return False
    
    def delete_model(self, name: str) -> bool:
        """
        Delete a model
        
        Args:
            name: Name of the model to delete
            
        Returns:
            True if successful
        """
        try:
            payload = {"name": name}
            response = self.session.delete(
                f"{self.base_url}/api/delete",
                json=payload
            )
            
            response.raise_for_status()
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to delete model {name}: {e}")
            return False
    
    def show_model_info(self, name: str) -> Dict[str, Any]:
        """
        Show model information
        
        Args:
            name: Model name
            
        Returns:
            Model information dictionary
        """
        try:
            payload = {"name": name}
            response = self.session.post(
                f"{self.base_url}/api/show",
                json=payload
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to get model info for {name}: {e}")
            return {}
    
    def copy_model(self, source: str, destination: str) -> bool:
        """
        Copy a model
        
        Args:
            source: Source model name
            destination: Destination model name
            
        Returns:
            True if successful
        """
        try:
            payload = {
                "source": source,
                "destination": destination
            }
            
            response = self.session.post(
                f"{self.base_url}/api/copy",
                json=payload
            )
            
            response.raise_for_status()
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to copy model {source} to {destination}: {e}")
            return False
    
    def _handle_stream_response(self, response) -> str:
        """Handle streaming response from Ollama"""
        content_parts = []
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    
                    if "response" in data:
                        content_parts.append(data["response"])
                    elif "message" in data and "content" in data["message"]:
                        content_parts.append(data["message"]["content"])
                    
                    if data.get("done", False):
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        return "".join(content_parts)
    
    def generate_stream(self, 
                       prompt: str, 
                       model: str = "llama2",
                       **kwargs) -> Generator[str, None, None]:
        """
        Generate text with streaming response
        
        Args:
            prompt: Input prompt
            model: Model name
            **kwargs: Additional parameters
            
        Yields:
            Text chunks as they are generated
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except requests.RequestException as e:
            logger.error(f"Ollama streaming generation failed: {e}")
            yield f"Error: {str(e)}"

# Global service instance
ollama_service = OllamaService()