#!/usr/bin/env python3
"""
Polymarket Copy Trading Bot - Fixed Bet Percentage Strategy
Copies a fixed percentage of the trader's bet size (not wallet percentage)
Simple, reliable, and scalable
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.constants import POLYGON

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('polymarket_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PolymarketCopyBotPro:
    """Professional Polymarket copy trading bot using fixed bet percentage"""
    
    def __init__(self):
        # Configuration
        self.target_wallet = os.getenv('TARGET_WALLET_ADDRESS', '').lower()
        self.your_private_key = os.getenv('YOUR_PRIVATE_KEY')
        
        # Validate private key
        if not self.your_private_key:
            logger.error("❌ YOUR_PRIVATE_KEY not set!")
            self.client = None
            self.your_wallet = None
            return
        
        # NEW STRATEGY: Copy a fixed % of their bet size
        self.copy_percentage = float(os.getenv('COPY_PERCENTAGE', '0.1'))  # Default 0.1% of their bet
        self.min_bet_size = float(os.getenv('MIN_BET_SIZE', '1'))
        self.max_bet_size = float(os.getenv('MAX_BET_SIZE', '1000'))
        
        # Initialize Polymarket client
        try:
            self.client = ClobClient(
                host="https://clob.polymarket.com",
                key=self.your_private_key,
                chain_id=POLYGON,
            )
            self.your_wallet = self.client.get_address().lower()
            logger.info(f"✅ Connected - Your wallet: {self.your_wallet}")
        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            self.client = None
            self.your_wallet = None
        
        # Position tracking for detecting trades
        self.last_target_positions = {}
        self.current_target_positions = {}
        self.your_positions = {}
        
        # Market cache
        self.market_cache = {}
        
    def load_state(self):
        """Load previous state from file"""
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    data = json.load(f)
                    self.last_target_positions = data.get('last_target_positions', {})
                    self.your_positions = data.get('your_positions', {})
                logger.info(f"Loaded previous state")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        """Save current state to file"""
        try:
            data = {
                'last_target_positions': self.last_target_positions,
                'your_positions': self.your_positions,
                'updated_at': datetime.now().isoformat()
            }
            with open('bot_state.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def get_all_positions(self, wallet_address: str) -> Dict[str, float]:
        """Get all current positions for a wallet"""
        try:
            import requests
            
            url = f"https://data-api.polymarket.com/positions"
            response = requests.get(url, params={"user": wallet_address}, timeout=10)
            
            positions = {}
            if response.status_code == 200:
                data = response.json()
                
                # Handle if response is a list
                if isinstance(data, list):
                    for position in data:
                        asset = position.get('asset')
                        size = float(position.get('size', 0))
                        if asset and size > 0:
                            positions[asset] = size
                else:
                    logger.warning(f"⚠️ Unexpected response format: {type(data)}")
            else:
                logger.error(f"❌ API returned status {response.status_code}")
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    def get_market_info(self, token_id: str) -> Optional[Dict]:
        """Get market information with caching"""
        if token_id in self.market_cache:
            return self.market_cache[token_id]
        
        try:
            import requests
            url = f"https://gamma-api.polymarket.com/markets/{token_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                market_info = response.json()
                self.m
