#!/usr/bin/env python3
"""
Polymarket Copy Trading Bot - Production Version
Uses official Polymarket SDK for proper order signing and placement
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
    """Professional Polymarket copy trading bot using official SDK"""
    
    def __init__(self):
        # Configuration
        self.target_wallet = os.getenv('TARGET_WALLET_ADDRESS', '').lower()
        self.your_private_key = os.getenv('YOUR_PRIVATE_KEY')
        self.copy_percentage = float(os.getenv('COPY_PERCENTAGE', '100'))
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
        
        # Tracking
        self.processed_orders = set()
        self.last_check_time = int(time.time()) - 3600
        
        # Market cache to reduce API calls
        self.market_cache = {}
        
    def load_processed_orders(self):
        """Load previously processed orders from file"""
        try:
            if os.path.exists('processed_orders.json'):
                with open('processed_orders.json', 'r') as f:
                    data = json.load(f)
                    self.processed_orders = set(data.get('orders', []))
                    self.last_check_time = data.get('last_check', self.last_check_time)
                logger.info(f"Loaded {len(self.processed_orders)} processed orders")
        except Exception as e:
            logger.error(f"Error loading processed orders: {e}")
    
    def save_processed_orders(self):
        """Save processed orders to file"""
        try:
            data = {
                'orders': list(self.processed_orders),
                'last_check': self.last_check_time,
                'updated_at': datetime.now().isoformat()
            }
            with open('processed_orders.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed orders: {e}")
    
    def get_balance(self, wallet_address: str) -> float:
        """Get USDC balance for a wallet"""
        try:
            if wallet_address.lower() == self.your_wallet:
                # Use SDK for own balance
                balance_info = self.client.get_balance_allowance()
                balance = float(balance_info.get('balance', 0)) / 1e6
            else:
                # Use API for other wallets
                import requests
                url = f"https://gamma-api.polymarket.com/balance"
                response = requests.get(url, params={"address": wallet_address}, timeout=10)
                if response.status_code == 200:
                    balance = float(response.json().get('balance', 0)) / 1e6
                else:
                    balance = 0.0
            
            return balance
        except Exception as e:
            logger.error(f"Error getting balance for {wallet_address[:10]}...: {e}")
            return 0.0
    
    def get_recent_orders(self, wallet_address: str) -> List[Dict]:
        """Fetch recent orders for a wallet"""
        try:
            # Use Polymarket API to get orders
            import requests
            url = "https://clob.polymarket.com/orders"
            params = {
                "maker": wallet_address,
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get('data', [])
                
                # Filter for filled/partially filled orders since last check
                new_orders = []
                for order in orders:
                    created_at = int(order.get('created_at', 0))
                    order_id = order.get('order_id')
                    status = order.get('status', '')
                    
                    # Only process filled orders that are new
                    if (created_at > self.last_check_time and 
                        order_id not in self.processed_orders and
                        status in ['FILLED', 'MATCHED']):
                        new_orders.append(order)
                
                return new_orders
            else:
                logger.warning(f"Could not fetch orders: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    def get_market_info(self, token_id: str) -> Optional[Dict]:
        """Get market information with caching"""
        if token_id in self.market_cache:
            return self.market_cache[token_id]
        
        try:
            import requests
            # Get market info from Gamma API
            url = f"https://gamma-api.polymarket.com/markets/{token_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                market_info = response.json()
                self.market_cache[token_id] = market_info
                return market_info
            return None
        except Exception as e:
            logger.error(f"Error getting market info: {e}")
            return None
    
    def calculate_copy_size(self, target_bet_size: float, target_balance: float, 
                           your_balance: float) -> float:
        """Calculate copy bet size with safety limits"""
        try:
            if target_balance <= 0 or your_balance <= 0:
                return 0.0
            
            # Calculate percentage of target wallet used
            target_percentage = (target_bet_size / target_balance) * 100
            
            # Apply copy percentage adjustment
            adjusted_percentage = target_percentage * (self.copy_percentage / 100)
            
            # Calculate your bet size
            your_bet_size = (your_balance * adjusted_percentage) / 100
            
            # Apply min/max limits
            your_bet_size = max(self.min_bet_size, min(your_bet_size, self.max_bet_size))
            
            # Don't bet more than available balance
            your_bet_size = min(your_bet_size, your_balance * 0.95)  # Keep 5% buffer
            
            logger.info(f"📊 Target: ${target_bet_size:.2f} ({target_percentage:.2f}%)")
            logger.info(f"📊 Your bet: ${your_bet_size:.2f} ({adjusted_percentage:.2f}%)")
            
            return your_bet_size
            
        except Exception as e:
            logger.error(f"Error calculating copy size: {e}")
            return 0.0
    
    def place_market_order(self, token_id: str, size: float, side: str) -> bool:
        """Place a market order on Polymarket"""
        try:
            if not self.client:
                logger.error("Client not initialized")
                return False
            
            # Convert size to contract units (6 decimals)
            size_in_units = int(size * 1e6)
            
            logger.info(f"📤 Placing {side} order: ${size:.2f} on token {token_id[:10]}...")
            
            # Create market order
            order_args = OrderArgs(
                token_id=token_id,
                price=1.0 if side == "BUY" else 0.0,  # Market order prices
                size=size_in_units,
                side=side,
                fee_rate_bps=0,
            )
            
            # Sign and post order
            signed_order = self.client.create_order(order_args)
            resp = self.client.post_order(signed_order, OrderType.FOK)  # Fill or Kill
            
            if resp.get('success'):
                logger.info(f"✅ Order placed successfully! Order ID: {resp.get('orderID')}")
                return True
            else:
                logger.error(f"❌ Order failed: {resp.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return False
    
    def process_new_order(self, order: Dict):
        """Process and copy a new order from target wallet"""
        try:
            order_id = order.get('order_id')
            
            if order_id in self.processed_orders:
                return
            
            # Extract order details
            token_id = order.get('asset_id')
            original_size = float(order.get('original_size', 0)) / 1e6
            matched_size = float(order.get('size_matched', original_size * 1e6)) / 1e6
            price = float(order.get('price', 0))
            side = order.get('side')
            
            logger.info(f"\n{'='*70}")
            logger.info(f"🎯 NEW ORDER DETECTED from {self.target_wallet[:10]}...")
            logger.info(f"Order ID: {order_id}")
            logger.info(f"Token: {token_id}")
            logger.info(f"Size: ${matched_size:.2f} @ {price}")
            logger.info(f"Side: {side}")
            
            # Get market context
            market_info = self.get_market_info(token_id)
            if market_info:
                question = market_info.get('question', 'Unknown')
                logger.info(f"📋 Market: {question}")
            
            # Get balances
            target_balance = self.get_balance(self.target_wallet)
            your_balance = self.get_balance(self.your_wallet)
            
            logger.info(f"💰 Target balance: ${target_balance:.2f}")
            logger.info(f"💰 Your balance: ${your_balance:.2f}")
            
            if your_balance < self.min_bet_size:
                logger.warning(f"⚠️  Insufficient balance (${your_balance:.2f} < ${self.min_bet_size:.2f})")
                return
            
            # Calculate copy size
            copy_size = self.calculate_copy_size(matched_size, target_balance, your_balance)
            
            if copy_size < self.min_bet_size:
                logger.warning(f"⚠️  Copy size ${copy_size:.2f} below minimum ${self.min_bet_size:.2f}")
                return
            
            # Place the order
            success = self.place_market_order(token_id, copy_size, side)
            
            if success:
                self.processed_orders.add(order_id)
                self.save_processed_orders()
                logger.info(f"✅ Successfully copied order!")
            else:
                logger.error(f"❌ Failed to copy order")
            
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"Error processing order: {e}", exc_info=True)
    
    async def monitor_wallet(self):
        """Main monitoring loop"""
        logger.info(f"\n🤖 Bot Started")
        logger.info(f"👀 Monitoring: {self.target_wallet}")
        logger.info(f"💼 Your wallet: {self.your_wallet}")
        logger.info(f"📊 Copy percentage: {self.copy_percentage}%")
        logger.info(f"💵 Min bet: ${self.min_bet_size} | Max bet: ${self.max_bet_size}")
        logger.info(f"{'='*70}\n")
        
        # Load previous state
        self.load_processed_orders()
        
        consecutive_errors = 0
        max_errors = 5
        
        while True:
            try:
                # Fetch recent orders
                orders = self.get_recent_orders(self.target_wallet)
                
                if orders:
                    logger.info(f"🔔 Found {len(orders)} new order(s)!")
                    
                    for order in orders:
                        self.process_new_order(order)
                        await asyncio.sleep(2)  # Slight delay between orders
                
                # Update last check time
                self.last_check_time = int(time.time())
                
                # Reset error counter on success
                consecutive_errors = 0
                
                # Wait before next check
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Bot stopped by user")
                self.save_processed_orders()
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"❌ Error in monitoring loop ({consecutive_errors}/{max_errors}): {e}")
                
                if consecutive_errors >= max_errors:
                    logger.error("Too many consecutive errors. Stopping bot.")
                    break
                
                await asyncio.sleep(60)  # Wait longer on error
    
    def run(self):
        """Start the bot"""
        if not self.target_wallet:
            logger.error("❌ TARGET_WALLET_ADDRESS not set in .env file!")
            return
        
        if not self.client or not self.your_wallet:
            logger.error("❌ Could not initialize client. Check YOUR_PRIVATE_KEY in .env!")
            return
        
        # Run the monitoring loop
        try:
            asyncio.run(self.monitor_wallet())
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.save_processed_orders()
            logger.info("Bot stopped. State saved.")


if __name__ == "__main__":
    bot = PolymarketCopyBotPro()
    bot.run()
