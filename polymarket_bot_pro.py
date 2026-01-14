#!/usr/bin/env python3
"""
Polymarket Copy Trading Bot - Production Version with Automated Sells
Uses official Polymarket SDK for proper order signing and placement
Copies both buys AND sells proportionally
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
        
        # Validate private key
        if not self.your_private_key:
            logger.error("❌ YOUR_PRIVATE_KEY not set!")
            self.client = None
            self.your_wallet = None
            return
            
        self.copy_percentage = float(os.getenv('COPY_PERCENTAGE', '100'))
        self.min_bet_size = float(os.getenv('MIN_BET_SIZE', '0.01'))
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
        
        # Position tracking for proportional sells
        self.target_positions = {}  # {token_id: position_size}
        self.your_positions = {}    # {token_id: position_size}
        
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
                    self.target_positions = data.get('target_positions', {})
                    self.your_positions = data.get('your_positions', {})
                logger.info(f"Loaded {len(self.processed_orders)} processed orders")
        except Exception as e:
            logger.error(f"Error loading processed orders: {e}")
    
    def save_processed_orders(self):
        """Save processed orders to file"""
        try:
            data = {
                'orders': list(self.processed_orders),
                'last_check': self.last_check_time,
                'target_positions': self.target_positions,
                'your_positions': self.your_positions,
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
    
    def get_position_size(self, wallet_address: str, token_id: str) -> float:
        """Get current position size for a specific token"""
        try:
            import requests
            
            # Try to get positions from API
            url = f"https://gamma-api.polymarket.com/positions"
            response = requests.get(url, params={"address": wallet_address}, timeout=10)
            
            if response.status_code == 200:
                positions = response.json()
                for position in positions:
                    if position.get('asset_id') == token_id:
                        return float(position.get('size', 0))
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting position size: {e}")
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
            
            # Apply ONLY max limit (no minimum enforcement for proportional matching)
            your_bet_size = min(your_bet_size, self.max_bet_size)
            
            # Don't bet more than available balance
            your_bet_size = min(your_bet_size, your_balance * 0.95)  # Keep 5% buffer
            
            logger.info(f"📊 Target: ${target_bet_size:.2f} ({target_percentage:.2f}%)")
            logger.info(f"📊 Your bet: ${your_bet_size:.2f} ({adjusted_percentage:.2f}%)")
            
            return your_bet_size
            
        except Exception as e:
            logger.error(f"Error calculating copy size: {e}")
            return 0.0
    
    def calculate_proportional_sell(self, token_id: str, target_sell_size: float) -> float:
        """Calculate proportional sell amount based on position sizes"""
        try:
            # Get current positions
            target_position = self.target_positions.get(token_id, 0.0)
            your_position = self.your_positions.get(token_id, 0.0)
            
            if target_position <= 0 or your_position <= 0:
                logger.warning(f"No position found to sell. Target: {target_position}, Yours: {your_position}")
                return 0.0
            
            # Calculate what % of their position they're selling
            sell_percentage = (target_sell_size / target_position) * 100
            
            # Apply same % to your position
            your_sell_size = (your_position * sell_percentage) / 100
            
            # Make sure we don't try to sell more than we have
            your_sell_size = min(your_sell_size, your_position)
            
            logger.info(f"📉 Target selling: ${target_sell_size:.2f} ({sell_percentage:.1f}% of position)")
            logger.info(f"📉 You selling: ${your_sell_size:.2f} ({sell_percentage:.1f}% of position)")
            
            return your_sell_size
            
        except Exception as e:
            logger.error(f"Error calculating proportional sell: {e}")
            return 0.0
    
    def place_market_order(self, token_id: str, size: float, side: str) -> bool:
        """Place a market order on Polymarket"""
        try:
            if not self.client:
                logger.error("Client not initialized")
                return False
            
            if size < 0.01:
                logger.warning(f"Size ${size:.4f} too small to execute")
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
                
                # Update position tracking
                if side == "BUY":
                    self.your_positions[token_id] = self.your_positions.get(token_id, 0.0) + size
                elif side == "SELL":
                    self.your_positions[token_id] = max(0, self.your_positions.get(token_id, 0.0) - size)
                
                self.save_processed_orders()
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
            
            # Handle BUY orders
            if side == "BUY":
                # Get balances
                target_balance = self.get_balance(self.target_wallet)
                your_balance = self.get_balance(self.your_wallet)
                
                logger.info(f"💰 Target balance: ${target_balance:.2f}")
                logger.info(f"💰 Your balance: ${your_balance:.2f}")
                
                # Check minimum balance
                if your_balance < self.min_bet_size:
                    logger.warning(f"⚠️  Insufficient balance (${your_balance:.2f} < ${self.min_bet_size:.2f})")
                    return
                
                # Calculate copy size
                copy_size = self.calculate_copy_size(matched_size, target_balance, your_balance)
                
                if copy_size < 0.01:
                    logger.warning(f"⚠️  Copy size ${copy_size:.4f} too small to execute")
                    return
                
                # Place the buy order
                success = self.place_market_order(token_id, copy_size, "BUY")
                
                if success:
                    # Update position tracking
                    self.target_positions[token_id] = self.target_positions.get(token_id, 0.0) + matched_size
                    self.processed_orders.add(order_id)
                    self.save_processed_orders()
                    logger.info(f"✅ Successfully copied BUY order!")
                else:
                    logger.error(f"❌ Failed to copy BUY order")
            
            # Handle SELL orders
            elif side == "SELL":
                logger.info(f"📉 SELL ORDER detected - calculating proportional exit...")
                
                # Calculate proportional sell size
                copy_size = self.calculate_proportional_sell(token_id, matched_size)
                
                if copy_size < 0.01:
                    logger.warning(f"⚠️  Sell size ${copy_size:.4f} too small to execute or no position held")
                    return
                
                # Place the sell order
                success = self.place_market_order(token_id, copy_size, "SELL")
                
                if success:
                    # Update position tracking
                    self.target_positions[token_id] = max(0, self.target_positions.get(token_id, 0.0) - matched_size)
                    self.processed_orders.add(order_id)
                    self.save_processed_orders()
                    logger.info(f"✅ Successfully copied SELL order!")
                else:
                    logger.error(f"❌ Failed to copy SELL order")
            
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"Error processing order: {e}", exc_info=True)
    
    def sync_positions(self):
        """Sync position tracking with actual on-chain positions"""
        try:
            import requests
            
            # Get target wallet positions
            logger.info("🔄 Syncing positions with on-chain data...")
            
            target_url = f"https://gamma-api.polymarket.com/positions"
            target_response = requests.get(target_url, params={"address": self.target_wallet}, timeout=10)
            
            if target_response.status_code == 200:
                target_positions = target_response.json()
                self.target_positions = {}
                for pos in target_positions:
                    token_id = pos.get('asset_id')
                    size = float(pos.get('size', 0))
                    if size > 0:
                        self.target_positions[token_id] = size
                
                logger.info(f"✅ Target wallet has {len(self.target_positions)} active positions")
            
            # Get your positions
            your_url = f"https://gamma-api.polymarket.com/positions"
            your_response = requests.get(your_url, params={"address": self.your_wallet}, timeout=10)
            
            if your_response.status_code == 200:
                your_positions = your_response.json()
                self.your_positions = {}
                for pos in your_positions:
                    token_id = pos.get('asset_id')
                    size = float(pos.get('size', 0))
                    if size > 0:
                        self.your_positions[token_id] = size
                
                logger.info(f"✅ Your wallet has {len(self.your_positions)} active positions")
            
            self.save_processed_orders()
            
        except Exception as e:
            logger.error(f"Error syncing positions: {e}")
    
    async def monitor_wallet(self):
        """Main monitoring loop"""
        logger.info(f"\n🤖 Bot Started - FULL COPY MODE (Buys + Sells)")
        logger.info(f"👀 Monitoring: {self.target_wallet}")
        logger.info(f"💼 Your wallet: {self.your_wallet}")
        logger.info(f"📊 Copy percentage: {self.copy_percentage}%")
        logger.info(f"💵 Max bet: ${self.max_bet_size} (proportional matching enabled)")
        logger.info(f"{'='*70}\n")
        
        # Load previous state
        self.load_processed_orders()
        
        # Sync positions on startup
        self.sync_positions()
        
        consecutive_errors = 0
        max_errors = 5
        sync_counter = 0
        
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
                
                # Sync positions every 10 minutes (40 cycles)
                sync_counter += 1
                if sync_counter >= 40:
                    self.sync_positions()
                    sync_counter = 0
                
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
