import logging
import json
import os
from datetime import datetime
from models import BlockchainTransaction
from app import db
import hashlib
import secrets

class BlockchainService:
    def __init__(self):
        self.networks = {
            'ethereum': self._get_ethereum_config,
            'polygon': self._get_polygon_config,
            'arbitrum': self._get_arbitrum_config,
            'optimism': self._get_optimism_config
        }
        self.contract_addresses = {
            'token': os.getenv('AUTOGENT_TOKEN_ADDRESS', '0x0000000000000000000000000000000000000000'),
            'nft': os.getenv('AUTOGENT_NFT_ADDRESS', '0x0000000000000000000000000000000000000000'),
            'marketplace': os.getenv('AUTOGENT_MARKETPLACE_ADDRESS', '0x0000000000000000000000000000000000000000'),
            'revenue_sharing': os.getenv('REVENUE_SHARING_ADDRESS', '0x0000000000000000000000000000000000000000')
        }
    
    def _get_ethereum_config(self):
        """Get Ethereum network configuration"""
        return {
            'network': 'ethereum',
            'rpc_url': os.getenv('ETHEREUM_RPC_URL', 'https://mainnet.infura.io/v3/YOUR-PROJECT-ID'),
            'chain_id': 1,
            'gas_price': 'fast',
            'confirmations': 12
        }
    
    def _get_polygon_config(self):
        """Get Polygon network configuration"""
        return {
            'network': 'polygon',
            'rpc_url': os.getenv('POLYGON_RPC_URL', 'https://polygon-mainnet.infura.io/v3/YOUR-PROJECT-ID'),
            'chain_id': 137,
            'gas_price': 'fast',
            'confirmations': 5
        }
    
    def _get_arbitrum_config(self):
        """Get Arbitrum network configuration"""
        return {
            'network': 'arbitrum',
            'rpc_url': os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc'),
            'chain_id': 42161,
            'gas_price': 'fast',
            'confirmations': 1
        }
    
    def _get_optimism_config(self):
        """Get Optimism network configuration"""
        return {
            'network': 'optimism',
            'rpc_url': os.getenv('OPTIMISM_RPC_URL', 'https://mainnet.optimism.io'),
            'chain_id': 10,
            'gas_price': 'fast',
            'confirmations': 1
        }
    
    def connect_wallet(self, user_id, wallet_address, wallet_type='metamask'):
        """Connect user wallet to Autogent Studio"""
        try:
            # Validate wallet address
            if not self._is_valid_address(wallet_address):
                raise ValueError("Invalid wallet address")
            
            # Create wallet connection record
            wallet_connection = {
                'user_id': user_id,
                'wallet_address': wallet_address,
                'wallet_type': wallet_type,
                'connected_at': datetime.utcnow().isoformat(),
                'status': 'connected'
            }
            
            # Store in database (this would extend the User model)
            # For now, log the connection
            logging.info(f"Wallet connected: {wallet_address} for user {user_id}")
            
            return wallet_connection
        
        except Exception as e:
            logging.error(f"Error connecting wallet: {str(e)}")
            return None
    
    def _is_valid_address(self, address):
        """Validate Ethereum address format"""
        if not address or len(address) != 42:
            return False
        
        if not address.startswith('0x'):
            return False
        
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    
    def create_nft_agent(self, user_id, agent_data, metadata):
        """Create NFT for AI agent"""
        try:
            # Generate unique token ID
            token_id = self._generate_token_id()
            
            # Create NFT metadata
            nft_metadata = {
                'name': agent_data['name'],
                'description': agent_data['description'],
                'image': agent_data.get('image_url', ''),
                'attributes': [
                    {'trait_type': 'Agent Type', 'value': agent_data.get('type', 'General')},
                    {'trait_type': 'Capabilities', 'value': len(agent_data.get('capabilities', []))},
                    {'trait_type': 'Created By', 'value': agent_data.get('creator', 'Unknown')},
                    {'trait_type': 'Version', 'value': agent_data.get('version', '1.0')},
                    {'trait_type': 'Rating', 'value': agent_data.get('rating', 0)}
                ],
                'properties': {
                    'agent_id': agent_data['id'],
                    'user_id': user_id,
                    'capabilities': agent_data.get('capabilities', []),
                    'model_info': agent_data.get('model_info', {}),
                    'created_at': datetime.utcnow().isoformat()
                }
            }
            
            # Store metadata on IPFS (simulated)
            ipfs_hash = self._store_on_ipfs(nft_metadata)
            
            # Create blockchain transaction
            transaction = BlockchainTransaction(
                user_id=user_id,
                transaction_hash=self._generate_transaction_hash(),
                transaction_type='nft_mint',
                metadata={
                    'token_id': token_id,
                    'contract_address': self.contract_addresses['nft'],
                    'ipfs_hash': ipfs_hash,
                    'agent_data': agent_data
                }
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'token_id': token_id,
                'transaction_hash': transaction.transaction_hash,
                'ipfs_hash': ipfs_hash,
                'metadata': nft_metadata
            }
        
        except Exception as e:
            logging.error(f"Error creating NFT agent: {str(e)}")
            return None
    
    def _generate_token_id(self):
        """Generate unique token ID"""
        return int(hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{secrets.token_hex(16)}".encode()
        ).hexdigest()[:16], 16)
    
    def _store_on_ipfs(self, metadata):
        """Store metadata on IPFS (simulated)"""
        # This would integrate with actual IPFS
        # For now, return simulated hash
        content_hash = hashlib.sha256(json.dumps(metadata).encode()).hexdigest()
        return f"QmT{content_hash[:44]}"
    
    def _generate_transaction_hash(self):
        """Generate transaction hash"""
        return f"0x{hashlib.sha256(f'{datetime.utcnow().isoformat()}{secrets.token_hex(16)}'.encode()).hexdigest()}"
    
    def setup_revenue_sharing(self, user_id, agent_id, revenue_split):
        """Setup revenue sharing for AI agent"""
        try:
            # Validate revenue split
            if not isinstance(revenue_split, dict) or sum(revenue_split.values()) != 100:
                raise ValueError("Revenue split must total 100%")
            
            # Create revenue sharing contract
            contract_data = {
                'agent_id': agent_id,
                'user_id': user_id,
                'revenue_split': revenue_split,
                'contract_address': self.contract_addresses['revenue_sharing'],
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Create transaction
            transaction = BlockchainTransaction(
                user_id=user_id,
                transaction_hash=self._generate_transaction_hash(),
                transaction_type='revenue_sharing_setup',
                metadata=contract_data
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return contract_data
        
        except Exception as e:
            logging.error(f"Error setting up revenue sharing: {str(e)}")
            return None
    
    def process_payment(self, user_id, amount, currency='ETH', recipient=None):
        """Process blockchain payment"""
        try:
            # Validate payment parameters
            if amount <= 0:
                raise ValueError("Payment amount must be positive")
            
            # Create payment transaction
            payment_data = {
                'amount': amount,
                'currency': currency,
                'recipient': recipient,
                'sender': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Simulate payment processing
            transaction_hash = self._generate_transaction_hash()
            
            # Create transaction record
            transaction = BlockchainTransaction(
                user_id=user_id,
                transaction_hash=transaction_hash,
                transaction_type='payment',
                amount=amount,
                metadata=payment_data
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'transaction_hash': transaction_hash,
                'amount': amount,
                'currency': currency,
                'status': 'confirmed',
                'confirmations': 0
            }
        
        except Exception as e:
            logging.error(f"Error processing payment: {str(e)}")
            return None
    
    def deploy_plugin_contract(self, user_id, plugin_data):
        """Deploy smart contract for plugin"""
        try:
            # Create plugin contract data
            contract_data = {
                'plugin_name': plugin_data['name'],
                'plugin_version': plugin_data['version'],
                'plugin_code': plugin_data['code'],
                'access_control': plugin_data.get('access_control', 'public'),
                'pricing': plugin_data.get('pricing', 'free'),
                'deployed_at': datetime.utcnow().isoformat()
            }
            
            # Generate contract address
            contract_address = f"0x{hashlib.sha256(json.dumps(contract_data).encode()).hexdigest()[:40]}"
            
            # Create deployment transaction
            transaction = BlockchainTransaction(
                user_id=user_id,
                transaction_hash=self._generate_transaction_hash(),
                transaction_type='contract_deployment',
                metadata={
                    'contract_address': contract_address,
                    'contract_data': contract_data,
                    'plugin_id': plugin_data['id']
                }
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'contract_address': contract_address,
                'transaction_hash': transaction.transaction_hash,
                'deployment_status': 'success'
            }
        
        except Exception as e:
            logging.error(f"Error deploying plugin contract: {str(e)}")
            return None
    
    def create_dao_proposal(self, user_id, proposal_data):
        """Create DAO governance proposal"""
        try:
            # Create proposal
            proposal = {
                'id': self._generate_proposal_id(),
                'title': proposal_data['title'],
                'description': proposal_data['description'],
                'proposer': user_id,
                'proposal_type': proposal_data.get('type', 'general'),
                'voting_period': proposal_data.get('voting_period', 7),  # days
                'required_quorum': proposal_data.get('quorum', 10),  # percentage
                'status': 'active',
                'votes_for': 0,
                'votes_against': 0,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Create transaction
            transaction = BlockchainTransaction(
                user_id=user_id,
                transaction_hash=self._generate_transaction_hash(),
                transaction_type='dao_proposal',
                metadata=proposal
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return proposal
        
        except Exception as e:
            logging.error(f"Error creating DAO proposal: {str(e)}")
            return None
    
    def _generate_proposal_id(self):
        """Generate unique proposal ID"""
        return f"PROP_{datetime.utcnow().strftime('%Y%m%d')}_{secrets.token_hex(4).upper()}"
    
    def stake_tokens(self, user_id, amount, staking_period=30):
        """Stake tokens for governance or rewards"""
        try:
            # Validate staking parameters
            if amount <= 0:
                raise ValueError("Staking amount must be positive")
            
            if staking_period < 1:
                raise ValueError("Staking period must be at least 1 day")
            
            # Calculate rewards
            annual_rate = 0.05  # 5% annual rate
            daily_rate = annual_rate / 365
            expected_rewards = amount * daily_rate * staking_period
            
            # Create staking transaction
            staking_data = {
                'amount': amount,
                'staking_period': staking_period,
                'expected_rewards': expected_rewards,
                'start_date': datetime.utcnow().isoformat(),
                'end_date': (datetime.utcnow().timestamp() + staking_period * 86400),
                'status': 'active'
            }
            
            transaction = BlockchainTransaction(
                user_id=user_id,
                transaction_hash=self._generate_transaction_hash(),
                transaction_type='token_staking',
                amount=amount,
                metadata=staking_data
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return staking_data
        
        except Exception as e:
            logging.error(f"Error staking tokens: {str(e)}")
            return None
    
    def get_wallet_balance(self, wallet_address, network='ethereum'):
        """Get wallet balance"""
        try:
            # This would integrate with actual blockchain APIs
            # For now, return simulated balance
            return {
                'wallet_address': wallet_address,
                'network': network,
                'balances': {
                    'ETH': 1.5,
                    'AUTOGENT': 1000.0,
                    'USDC': 500.0
                },
                'nfts': [
                    {
                        'contract_address': self.contract_addresses['nft'],
                        'token_id': 1,
                        'name': 'AI Agent #1',
                        'image': 'https://example.com/nft1.png'
                    }
                ]
            }
        
        except Exception as e:
            logging.error(f"Error getting wallet balance: {str(e)}")
            return None
    
    def get_transaction_history(self, user_id, limit=50):
        """Get user's blockchain transaction history"""
        try:
            transactions = BlockchainTransaction.query.filter_by(
                user_id=user_id
            ).order_by(BlockchainTransaction.created_at.desc()).limit(limit).all()
            
            return [{
                'transaction_hash': tx.transaction_hash,
                'transaction_type': tx.transaction_type,
                'amount': tx.amount,
                'status': tx.status,
                'created_at': tx.created_at.isoformat(),
                'metadata': tx.metadata
            } for tx in transactions]
        
        except Exception as e:
            logging.error(f"Error getting transaction history: {str(e)}")
            return []
    
    def verify_transaction(self, transaction_hash):
        """Verify transaction on blockchain"""
        try:
            # This would verify with actual blockchain
            # For now, return simulated verification
            return {
                'transaction_hash': transaction_hash,
                'status': 'confirmed',
                'confirmations': 12,
                'block_number': 18500000,
                'gas_used': 21000,
                'gas_price': 20000000000,
                'verified': True
            }
        
        except Exception as e:
            logging.error(f"Error verifying transaction: {str(e)}")
            return None
    
    def get_network_stats(self):
        """Get blockchain network statistics"""
        try:
            return {
                'ethereum': {
                    'block_number': 18500000,
                    'gas_price': 20,
                    'network_congestion': 'moderate',
                    'average_block_time': 12.5
                },
                'polygon': {
                    'block_number': 48000000,
                    'gas_price': 30,
                    'network_congestion': 'low',
                    'average_block_time': 2.2
                },
                'arbitrum': {
                    'block_number': 120000000,
                    'gas_price': 0.1,
                    'network_congestion': 'very_low',
                    'average_block_time': 0.25
                }
            }
        
        except Exception as e:
            logging.error(f"Error getting network stats: {str(e)}")
            return {}
