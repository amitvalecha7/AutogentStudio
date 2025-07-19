from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app import db
from models import User
from services.openai_service import OpenAIService
import logging
import uuid
import os
import requests
from datetime import datetime

image_bp = Blueprint('image', __name__)

@image_bp.route('/image')
def image():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    
    user = User.query.get(session['user_id'])
    return render_template('image/image.html', user=user)

@image_bp.route('/api/image/generate', methods=['POST'])
def generate_image():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Image generation parameters
        model = data.get('model', 'dall-e-3')
        size = data.get('size', '1024x1024')
        quality = data.get('quality', 'standard')
        style = data.get('style', 'vivid')
        
        user = User.query.get(session['user_id'])
        
        # Generate image using OpenAI DALL-E
        openai_service = OpenAIService()
        
        try:
            image_result = openai_service.generate_image(
                prompt=prompt,
                model=model,
                size=size,
                quality=quality,
                style=style
            )
            
            if image_result and 'url' in image_result:
                # Download and save image locally
                image_url = image_result['url']
                
                # Create images directory if it doesn't exist
                images_dir = os.path.join('static', 'generated_images')
                os.makedirs(images_dir, exist_ok=True)
                
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"image_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                local_path = os.path.join(images_dir, filename)
                
                # Download image
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Return both original URL and local path
                    return jsonify({
                        'success': True,
                        'image_url': image_url,
                        'local_path': f'/static/generated_images/{filename}',
                        'prompt': prompt,
                        'model': model,
                        'size': size,
                        'quality': quality,
                        'style': style
                    })
                else:
                    return jsonify({
                        'success': True,
                        'image_url': image_url,
                        'prompt': prompt,
                        'model': model,
                        'size': size,
                        'quality': quality,
                        'style': style
                    })
            else:
                return jsonify({'error': 'Failed to generate image'}), 500
                
        except Exception as e:
            logging.error(f"Error generating image: {str(e)}")
            return jsonify({'error': f'Image generation failed: {str(e)}'}), 500
            
    except Exception as e:
        logging.error(f"Error processing image generation request: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@image_bp.route('/api/image/variations', methods=['POST'])
def create_variations():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        image_url = data.get('image_url', '').strip()
        
        if not image_url:
            return jsonify({'error': 'Image URL is required'}), 400
        
        # Parameters for variations
        n = data.get('n', 1)  # Number of variations
        size = data.get('size', '1024x1024')
        
        user = User.query.get(session['user_id'])
        openai_service = OpenAIService()
        
        try:
            # For DALL-E 3, we'll use the edit/variation functionality
            # Note: This is a simplified implementation
            return jsonify({
                'success': True,
                'message': 'Variations feature coming soon for DALL-E 3',
                'original_url': image_url
            })
            
        except Exception as e:
            logging.error(f"Error creating variations: {str(e)}")
            return jsonify({'error': f'Variation creation failed: {str(e)}'}), 500
            
    except Exception as e:
        logging.error(f"Error processing variation request: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@image_bp.route('/api/image/edit', methods=['POST'])
def edit_image():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        image_url = data.get('image_url', '').strip()
        prompt = data.get('prompt', '').strip()
        
        if not image_url or not prompt:
            return jsonify({'error': 'Image URL and prompt are required'}), 400
        
        # Parameters for editing
        size = data.get('size', '1024x1024')
        
        user = User.query.get(session['user_id'])
        
        # For now, return a placeholder response
        # In a real implementation, you would use image editing APIs
        return jsonify({
            'success': True,
            'message': 'Image editing feature coming soon',
            'original_url': image_url,
            'edit_prompt': prompt
        })
        
    except Exception as e:
        logging.error(f"Error processing image edit request: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

@image_bp.route('/api/image/history')
def image_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        
        # Get generated images from static folder
        images_dir = os.path.join('static', 'generated_images')
        history = []
        
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(images_dir, filename)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        history.append({
                            'filename': filename,
                            'url': f'/static/generated_images/{filename}',
                            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'size': stat.st_size
                        })
        
        # Sort by creation time (newest first)
        history.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'images': history
        })
        
    except Exception as e:
        logging.error(f"Error getting image history: {str(e)}")
        return jsonify({'error': 'Failed to get image history'}), 500

@image_bp.route('/api/image/models')
def get_image_models():
    """Get available image generation models"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    models = [
        {
            'id': 'dall-e-3',
            'name': 'DALL-E 3',
            'description': 'Latest DALL-E model with improved quality and prompt following',
            'sizes': ['1024x1024', '1792x1024', '1024x1792'],
            'qualities': ['standard', 'hd'],
            'styles': ['vivid', 'natural']
        },
        {
            'id': 'dall-e-2',
            'name': 'DALL-E 2',
            'description': 'Previous generation DALL-E model',
            'sizes': ['256x256', '512x512', '1024x1024'],
            'qualities': ['standard'],
            'styles': ['natural']
        }
    ]
    
    return jsonify({
        'success': True,
        'models': models
    })
