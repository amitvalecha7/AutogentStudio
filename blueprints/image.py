from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from services.ai_service import AIService
from models import ChatMessage, db
import uuid
import base64
import requests
from io import BytesIO

image_bp = Blueprint('image', __name__, url_prefix='/image')

@image_bp.route('/')
@login_required
def index():
    # Get user's generated images
    generated_images = ChatMessage.query.filter(
        ChatMessage.role == 'assistant',
        ChatMessage.metadata.op('->>')('type') == 'image_generation'
    ).join(ChatMessage.session).filter_by(user_id=current_user.id).order_by(
        ChatMessage.created_at.desc()
    ).limit(50).all()
    
    return render_template('image/index.html', generated_images=generated_images)

@image_bp.route('/generate', methods=['POST'])
@login_required
def generate_image():
    data = request.get_json()
    
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    provider = data.get('provider', 'openai')  # openai, midjourney, pollinations
    size = data.get('size', '1024x1024')
    style = data.get('style', 'natural')
    quality = data.get('quality', 'standard')
    n_images = data.get('n_images', 1)
    
    try:
        ai_service = AIService()
        
        # Generate image based on provider
        if provider == 'openai':
            result = ai_service.generate_image_openai(
                prompt=prompt,
                size=size,
                quality=quality,
                n=min(n_images, 4)  # OpenAI max is 4
            )
        elif provider == 'midjourney':
            result = ai_service.generate_image_midjourney(
                prompt=prompt,
                aspect_ratio=size,
                style=style
            )
        elif provider == 'pollinations':
            result = ai_service.generate_image_pollinations(
                prompt=prompt,
                width=int(size.split('x')[0]),
                height=int(size.split('x')[1])
            )
        else:
            return jsonify({'error': 'Invalid provider'}), 400
        
        # Save generation record
        message_id = str(uuid.uuid4())
        generation_record = ChatMessage(
            id=message_id,
            session_id=None,  # Not part of a chat session
            role='assistant',
            content=f"Generated image with prompt: {prompt}",
            metadata={
                'type': 'image_generation',
                'provider': provider,
                'prompt': prompt,
                'settings': {
                    'size': size,
                    'style': style,
                    'quality': quality,
                    'n_images': n_images
                },
                'images': result.get('images', [])
            }
        )
        
        db.session.add(generation_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'images': result.get('images', []),
            'prompt': prompt,
            'provider': provider
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_bp.route('/enhance', methods=['POST'])
@login_required
def enhance_image():
    data = request.get_json()
    
    image_url = data.get('image_url')
    enhancement_type = data.get('enhancement_type', 'upscale')  # upscale, denoise, colorize
    
    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400
    
    try:
        ai_service = AIService()
        
        # Download original image
        response = requests.get(image_url)
        image_data = base64.b64encode(response.content).decode('utf-8')
        
        # Enhance image
        if enhancement_type == 'upscale':
            result = ai_service.upscale_image(image_data)
        elif enhancement_type == 'denoise':
            result = ai_service.denoise_image(image_data)
        elif enhancement_type == 'colorize':
            result = ai_service.colorize_image(image_data)
        else:
            return jsonify({'error': 'Invalid enhancement type'}), 400
        
        return jsonify({
            'success': True,
            'enhanced_image': result['image_url'],
            'original_image': image_url,
            'enhancement_type': enhancement_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_image():
    data = request.get_json()
    
    image_url = data.get('image_url')
    analysis_type = data.get('analysis_type', 'describe')  # describe, detect_objects, extract_text
    
    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400
    
    try:
        ai_service = AIService()
        
        # Download image
        response = requests.get(image_url)
        image_data = base64.b64encode(response.content).decode('utf-8')
        
        # Analyze image
        if analysis_type == 'describe':
            result = ai_service.analyze_image(image_data)
        elif analysis_type == 'detect_objects':
            result = ai_service.detect_objects(image_data)
        elif analysis_type == 'extract_text':
            result = ai_service.extract_text_from_image(image_data)
        else:
            return jsonify({'error': 'Invalid analysis type'}), 400
        
        return jsonify({
            'success': True,
            'analysis': result,
            'analysis_type': analysis_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_bp.route('/variations', methods=['POST'])
@login_required
def create_variations():
    data = request.get_json()
    
    image_url = data.get('image_url')
    n_variations = data.get('n_variations', 3)
    variation_strength = data.get('variation_strength', 0.7)
    
    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400
    
    try:
        ai_service = AIService()
        
        # Download original image
        response = requests.get(image_url)
        image_data = base64.b64encode(response.content).decode('utf-8')
        
        # Create variations
        result = ai_service.create_image_variations(
            image_data=image_data,
            n=min(n_variations, 4),
            strength=variation_strength
        )
        
        return jsonify({
            'success': True,
            'variations': result.get('images', []),
            'original_image': image_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_bp.route('/edit', methods=['POST'])
@login_required
def edit_image():
    data = request.get_json()
    
    image_url = data.get('image_url')
    mask_url = data.get('mask_url')  # Optional mask for inpainting
    prompt = data.get('prompt', '').strip()
    
    if not image_url:
        return jsonify({'error': 'Image URL is required'}), 400
    
    if not prompt:
        return jsonify({'error': 'Edit prompt is required'}), 400
    
    try:
        ai_service = AIService()
        
        # Download images
        image_response = requests.get(image_url)
        image_data = base64.b64encode(image_response.content).decode('utf-8')
        
        mask_data = None
        if mask_url:
            mask_response = requests.get(mask_url)
            mask_data = base64.b64encode(mask_response.content).decode('utf-8')
        
        # Edit image
        result = ai_service.edit_image(
            image_data=image_data,
            mask_data=mask_data,
            prompt=prompt
        )
        
        return jsonify({
            'success': True,
            'edited_image': result['image_url'],
            'original_image': image_url,
            'prompt': prompt
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_bp.route('/gallery')
@login_required
def gallery():
    # Get user's image generation history
    generated_images = ChatMessage.query.filter(
        ChatMessage.role == 'assistant',
        ChatMessage.metadata.op('->>')('type') == 'image_generation'
    ).join(ChatMessage.session).filter_by(user_id=current_user.id).order_by(
        ChatMessage.created_at.desc()
    ).all()
    
    return render_template('image/gallery.html', generated_images=generated_images)

@image_bp.route('/styles')
@login_required
def image_styles():
    # Return available image styles and presets
    styles = {
        'natural': 'Natural and realistic',
        'artistic': 'Artistic and creative',
        'anime': 'Anime and manga style',
        'photographic': 'Photographic quality',
        'digital_art': 'Digital art style',
        'oil_painting': 'Oil painting style',
        'watercolor': 'Watercolor painting',
        'sketch': 'Pencil sketch style',
        'cyberpunk': 'Cyberpunk aesthetic',
        'steampunk': 'Steampunk style',
        'fantasy': 'Fantasy art style',
        'sci_fi': 'Science fiction style'
    }
    
    return jsonify({
        'success': True,
        'styles': styles
    })

@image_bp.route('/templates')
@login_required
def image_templates():
    # Return prompt templates for different use cases
    templates = {
        'portrait': 'A professional portrait of [subject], high quality, detailed face, studio lighting',
        'landscape': 'A beautiful landscape of [location], stunning scenery, golden hour lighting, highly detailed',
        'product': 'Product photography of [product], clean background, professional lighting, commercial quality',
        'logo': 'A modern logo design for [company], clean, minimalist, professional, vector style',
        'illustration': 'An illustration of [subject] in [style] style, colorful, detailed, artistic',
        'character': 'A character design of [description], full body, detailed, concept art style'
    }
    
    return jsonify({
        'success': True,
        'templates': templates
    })
