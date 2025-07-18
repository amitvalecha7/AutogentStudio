from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import User
from blueprints.auth import login_required, get_current_user
from services.openai_service import OpenAIService
import logging
import uuid
import os

image_bp = Blueprint('image', __name__)

@image_bp.route('/')
@login_required
def image_index():
    user = get_current_user()
    return render_template('image/image.html', user=user)

@image_bp.route('/generate', methods=['POST'])
@login_required
def generate_image():
    user = get_current_user()
    data = request.get_json()
    
    prompt = data.get('prompt')
    style = data.get('style', 'vivid')
    size = data.get('size', '1024x1024')
    quality = data.get('quality', 'standard')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        # Use OpenAI DALL-E for image generation
        openai_service = OpenAIService()
        image_result = openai_service.generate_image(
            prompt=prompt,
            size=size,
            quality=quality,
            style=style
        )
        
        if image_result and 'url' in image_result:
            logging.info(f"Image generated for user {user.id}")
            return jsonify({
                'success': True,
                'image_url': image_result['url'],
                'prompt': prompt,
                'style': style,
                'size': size,
                'quality': quality
            })
        else:
            return jsonify({'error': 'Failed to generate image'}), 500
    
    except Exception as e:
        logging.error(f"Error generating image: {str(e)}")
        return jsonify({'error': 'Image generation failed'}), 500

@image_bp.route('/variations', methods=['POST'])
@login_required
def generate_variations():
    user = get_current_user()
    data = request.get_json()
    
    image_url = data.get('image_url')
    n = data.get('n', 2)
    size = data.get('size', '1024x1024')
    
    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400
    
    try:
        # Note: This would require implementing image variations
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'variations': [],
            'message': 'Image variations feature coming soon'
        })
    
    except Exception as e:
        logging.error(f"Error generating variations: {str(e)}")
        return jsonify({'error': 'Variation generation failed'}), 500

@image_bp.route('/edit', methods=['POST'])
@login_required
def edit_image():
    user = get_current_user()
    data = request.get_json()
    
    image_url = data.get('image_url')
    mask_url = data.get('mask_url')
    prompt = data.get('prompt')
    size = data.get('size', '1024x1024')
    
    if not all([image_url, prompt]):
        return jsonify({'error': 'Image URL and prompt are required'}), 400
    
    try:
        # Note: This would require implementing image editing
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'edited_image_url': '',
            'message': 'Image editing feature coming soon'
        })
    
    except Exception as e:
        logging.error(f"Error editing image: {str(e)}")
        return jsonify({'error': 'Image editing failed'}), 500

@image_bp.route('/gallery')
@login_required
def image_gallery():
    user = get_current_user()
    # In a real application, you would fetch user's generated images from database
    return render_template('image/gallery.html', user=user, images=[])

@image_bp.route('/styles')
@login_required
def get_styles():
    """Get available image generation styles"""
    styles = [
        {'id': 'vivid', 'name': 'Vivid', 'description': 'Hyper-real and dramatic images'},
        {'id': 'natural', 'name': 'Natural', 'description': 'Natural and realistic images'},
        {'id': 'artistic', 'name': 'Artistic', 'description': 'Artistic and stylized images'},
        {'id': 'abstract', 'name': 'Abstract', 'description': 'Abstract and conceptual images'},
        {'id': 'photorealistic', 'name': 'Photorealistic', 'description': 'Photography-like images'},
        {'id': 'cartoon', 'name': 'Cartoon', 'description': 'Cartoon and illustration style'},
        {'id': 'anime', 'name': 'Anime', 'description': 'Anime and manga style'},
        {'id': 'cyberpunk', 'name': 'Cyberpunk', 'description': 'Futuristic cyberpunk aesthetic'},
        {'id': 'steampunk', 'name': 'Steampunk', 'description': 'Victorian steampunk style'},
        {'id': 'minimalist', 'name': 'Minimalist', 'description': 'Clean and minimal design'}
    ]
    
    return jsonify({'styles': styles})

@image_bp.route('/sizes')
@login_required
def get_sizes():
    """Get available image sizes"""
    sizes = [
        {'id': '256x256', 'name': 'Small (256x256)', 'description': 'Small square image'},
        {'id': '512x512', 'name': 'Medium (512x512)', 'description': 'Medium square image'},
        {'id': '1024x1024', 'name': 'Large (1024x1024)', 'description': 'Large square image'},
        {'id': '1792x1024', 'name': 'Wide (1792x1024)', 'description': 'Wide landscape image'},
        {'id': '1024x1792', 'name': 'Tall (1024x1792)', 'description': 'Tall portrait image'}
    ]
    
    return jsonify({'sizes': sizes})
