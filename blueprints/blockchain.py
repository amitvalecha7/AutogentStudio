from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import BlockchainWallet, SmartContract, db
from services.blockchain_service import BlockchainService
import uuid

blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/blockchain')

@blockchain_bp.route('/')
@login_required
def index():
    # Get user's wallets and contracts
    wallets = BlockchainWallet.query.filter_by(
        user_id=current_user.id
    ).order_by(BlockchainWallet.created_at.desc()).all()
    
    contracts = SmartContract.query.all()  # Public contracts
    
    return render_template('blockchain/index.html', 
                         wallets=wallets, 
                         contracts=contracts)

@blockchain_bp.route('/wallet')
@login_required
def wallet():
    wallets = BlockchainWallet.query.filter_by(
        user_id=current_user.id
    ).order_by(BlockchainWallet.created_at.desc()).all()
    
    return render_template('blockchain/wallet.html', wallets=wallets)

@blockchain_bp.route('/contracts')
@login_required
def contracts():
    contracts = SmartContract.query.order_by(
        SmartContract.created_at.desc()
    ).all()
    
    return render_template('blockchain/contracts.html', contracts=contracts)

@blockchain_bp.route('/plugins')
@login_required
def plugins():
    return render_template('blockchain/plugins.html')

@blockchain_bp.route('/revenue')
@login_required
def revenue():
    return render_template('blockchain/revenue.html')

@blockchain_bp.route('/nft')
@login_required
def nft():
    return render_template('blockchain/nft.html')

@blockchain_bp.route('/connect-wallet', methods=['POST'])
@login_required
def connect_wallet():
    data = request.get_json()
    
    wallet_address = data.get('wallet_address', '').strip()
    wallet_type = data.get('wallet_type', 'metamask')
    network = data.get('network', 'ethereum')
    
    if not wallet_address:
        return jsonify({'error': 'Wallet address is required'}), 400
    
    try:
        blockchain_service = BlockchainService()
        
        # Verify wallet ownership
        verification_result = blockchain_service.verify_wallet_ownership(
            address=wallet_address,
            wallet_type=wallet_type,
            network=network
        )
        
        if not verification_result.get('verified'):
            return jsonify({'error': 'Wallet verification failed'}), 400
        
        # Check if wallet already exists
        existing_wallet = BlockchainWallet.query.filter_by(
            user_id=current_user.id,
            wallet_address=wallet_address,
            network=network
        ).first()
        
        if existing_wallet:
            existing_wallet.is_active = True
            existing_wallet.wallet_type = wallet_type
            db.session.commit()
            wallet_id = existing_wallet.id
        else:
            wallet_id = str(uuid.uuid4())
            wallet = BlockchainWallet(
                id=wallet_id,
                user_id=current_user.id,
                wallet_address=wallet_address,
                wallet_type=wallet_type,
                network=network,
                is_active=True
            )
            
            db.session.add(wallet)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'wallet_id': wallet_id,
            'verification': verification_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/wallet/<wallet_id>/balance')
@login_required
def wallet_balance(wallet_id):
    wallet = BlockchainWallet.query.filter_by(
        id=wallet_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        blockchain_service = BlockchainService()
        
        # Get wallet balance
        balance_info = blockchain_service.get_wallet_balance(wallet)
        
        return jsonify({
            'success': True,
            'balance': balance_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/deploy-contract', methods=['POST'])
@login_required
def deploy_contract():
    data = request.get_json()
    
    contract_name = data.get('name', '').strip()
    contract_code = data.get('contract_code', '')
    network = data.get('network', 'ethereum')
    wallet_id = data.get('wallet_id')
    
    if not all([contract_name, contract_code, wallet_id]):
        return jsonify({'error': 'All fields are required'}), 400
    
    wallet = BlockchainWallet.query.filter_by(
        id=wallet_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        blockchain_service = BlockchainService()
        
        # Deploy smart contract
        deployment_result = blockchain_service.deploy_smart_contract(
            contract_code=contract_code,
            wallet=wallet,
            network=network
        )
        
        contract_id = str(uuid.uuid4())
        contract = SmartContract(
            id=contract_id,
            name=contract_name,
            contract_address=deployment_result.get('address'),
            network=network,
            abi=deployment_result.get('abi', []),
            purpose=data.get('purpose', ''),
            is_verified=False
        )
        
        db.session.add(contract)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contract_id': contract_id,
            'deployment': deployment_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/contract/<contract_id>')
@login_required
def view_contract(contract_id):
    contract = SmartContract.query.get_or_404(contract_id)
    
    return render_template('blockchain/contract_detail.html', contract=contract)

@blockchain_bp.route('/contract/<contract_id>/interact', methods=['POST'])
@login_required
def interact_contract(contract_id):
    contract = SmartContract.query.get_or_404(contract_id)
    
    data = request.get_json()
    method_name = data.get('method_name')
    parameters = data.get('parameters', [])
    wallet_id = data.get('wallet_id')
    
    if not all([method_name, wallet_id]):
        return jsonify({'error': 'Method name and wallet ID are required'}), 400
    
    wallet = BlockchainWallet.query.filter_by(
        id=wallet_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        blockchain_service = BlockchainService()
        
        # Interact with smart contract
        interaction_result = blockchain_service.interact_with_contract(
            contract=contract,
            method_name=method_name,
            parameters=parameters,
            wallet=wallet
        )
        
        return jsonify({
            'success': True,
            'result': interaction_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/revenue-sharing/setup', methods=['POST'])
@login_required
def setup_revenue_sharing():
    data = request.get_json()
    
    plugin_id = data.get('plugin_id')
    revenue_percentage = data.get('revenue_percentage', 70.0)
    wallet_id = data.get('wallet_id')
    
    if not all([plugin_id, wallet_id]):
        return jsonify({'error': 'Plugin ID and wallet ID are required'}), 400
    
    wallet = BlockchainWallet.query.filter_by(
        id=wallet_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        blockchain_service = BlockchainService()
        
        # Set up revenue sharing contract
        revenue_setup = blockchain_service.setup_revenue_sharing(
            plugin_id=plugin_id,
            revenue_percentage=revenue_percentage,
            wallet=wallet
        )
        
        return jsonify({
            'success': True,
            'setup': revenue_setup
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/nft/mint', methods=['POST'])
@login_required
def mint_nft():
    data = request.get_json()
    
    ai_agent_id = data.get('ai_agent_id')
    metadata_uri = data.get('metadata_uri')
    wallet_id = data.get('wallet_id')
    
    if not all([ai_agent_id, metadata_uri, wallet_id]):
        return jsonify({'error': 'All fields are required'}), 400
    
    wallet = BlockchainWallet.query.filter_by(
        id=wallet_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        blockchain_service = BlockchainService()
        
        # Mint NFT for AI agent
        mint_result = blockchain_service.mint_ai_agent_nft(
            ai_agent_id=ai_agent_id,
            metadata_uri=metadata_uri,
            wallet=wallet
        )
        
        return jsonify({
            'success': True,
            'mint_result': mint_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/transaction-history/<wallet_id>')
@login_required
def transaction_history(wallet_id):
    wallet = BlockchainWallet.query.filter_by(
        id=wallet_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        blockchain_service = BlockchainService()
        
        # Get transaction history
        transactions = blockchain_service.get_transaction_history(wallet)
        
        return jsonify({
            'success': True,
            'transactions': transactions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/networks')
@login_required
def supported_networks():
    networks = {
        'ethereum': {
            'name': 'Ethereum',
            'currency': 'ETH',
            'chain_id': 1,
            'rpc_url': 'https://mainnet.infura.io/v3/',
            'explorer': 'https://etherscan.io'
        },
        'polygon': {
            'name': 'Polygon',
            'currency': 'MATIC',
            'chain_id': 137,
            'rpc_url': 'https://polygon-rpc.com/',
            'explorer': 'https://polygonscan.com'
        },
        'bsc': {
            'name': 'Binance Smart Chain',
            'currency': 'BNB',
            'chain_id': 56,
            'rpc_url': 'https://bsc-dataseed.binance.org/',
            'explorer': 'https://bscscan.com'
        },
        'arbitrum': {
            'name': 'Arbitrum',
            'currency': 'ETH',
            'chain_id': 42161,
            'rpc_url': 'https://arb1.arbitrum.io/rpc',
            'explorer': 'https://arbiscan.io'
        }
    }
    
    return jsonify({
        'success': True,
        'networks': networks
    })

@blockchain_bp.route('/gas-price/<network>')
@login_required
def gas_price(network):
    try:
        blockchain_service = BlockchainService()
        
        # Get current gas price
        gas_info = blockchain_service.get_gas_price(network)
        
        return jsonify({
            'success': True,
            'gas_info': gas_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
