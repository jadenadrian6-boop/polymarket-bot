#!/usr/bin/env python3
"""
Polymarket Copy Trading Bot - Position-Based Tracking
Tracks trades by monitoring position changes instead of order API
Works around 405 errors by using position snapshots
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
    """Professional Polymarket copy trading bot using position tracking"""
    
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
        
        # Position tracking for detecting trades
        self.last_target_positions = {}  # Previous snapshot
        self.current_target_positions = {}  # Current snapshot
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
    
    def get_balance(self, wallet_address: str) -> float:
        """Get USDC balance for a wallet"""
        try:
            if wallet_address.lower() == self.your_wallet:
                balance_info = self.client.get_balance_allowance()
                balance = float(balance_info.get('balance', 0)) / 1e6
            else:
                import requests
                url = f"https://gamma-api.polymarket.com/balance"
                response = requests.get(url, params={"address": wallet_address}, timeout=10)
                if response.status_code == 200:
                    balance = float(response.json().get('balance', 0)) / 1e6
                else:
                    balance = 0.0
            
            return balance
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
    
    def get_all_positions(self, wallet_address: str) -> Dict[str, float]:
        """Get all current positions for a wallet"""
        try:
            import requests
            
            url = f"https://data-api.polymarket.com/positions"
            response = requests.get(url, params={"user": wallet_address}, timeout=10)
            
            # Debug logging
            logger.info(f"📡 API Response Status: {response.status_code}")
            
            positions = {}
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📦 Raw response type: {type(data)}, length: {len(data) if isinstance(data, list) else 'N/A'}")
                
                # Handle if response is a list
                if isinstance(data, list):
                    for position in data:
                        asset = position.get('asset')
                        size = float(position.get('size', 0))
                        if asset and size > 0:
                            positions[asset] = size
                # Handle if response is a dict with positions array
                elif isinstance(data, dict) and 'positions' in data:
                    for position in data['positions']:
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
                self.market_cache[token_id] = market_info
                return market_info
            return None
        except Exception as e:
            logger.error(f"Error getting market info: {e}")
            return None
    
    def calculate_copy_size(self, target_bet_size: float, target_balance: float, 
                           your_balance: float) -> float:
        """Calculate copy bet size based on wallet percentages"""
        try:
            if target_balance <= 0 or your_balance <= 0:
                return 0.0
            
            # Calculate percentage of target wallet used
            target_percentage = (target_bet_size / target_balance) * 100
            
            # Apply copy percentage adjustment
            adjusted_percentage = target_percentage * (self.copy_percentage / 100)
            
            # Calculate your bet size
            your_bet_size = (your_balance * adjusted_percentage) / 100
            
            # Apply max limit
            your_bet_size = min(your_bet_size, self.max_bet_size)
            
            # Don't bet more than available balance
            your_bet_size = min(your_bet_size, your_balance * 0.95)
            
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
            
            if size < 0.01:
                logger.warning(f"Size ${size:.4f} too small to execute")
                return False
            
            size_in_units = int(size * 1e6)
            
            logger.info(f"📤 Placing {side} order: ${size:.2f} on token {token_id[:10]}...")
            
            order_args = OrderArgs(
                token_id=token_id,
                price=1.0 if side == "BUY" else 0.0,
                size=size_in_units,
                side=side,
                fee_rate_bps=0,
            )
            
            signed_order = self.client.create_order(order_args)
            resp = self.client.post_order(signed_order, OrderType.FOK)
            
            if resp.get('success'):
                logger.info(f"✅ Order placed! Order ID: {resp.get('orderID')}")
                
                # Update position tracking
                if side == "BUY":
                    self.your_positions[token_id] = self.your_positions.get(token_id, 0.0) + size
                elif side == "SELL":
                    self.your_positions[token_id] = max(0, self.your_positions.get(token_id, 0.0) - size)
                
                self.save_state()
                return True
            else:
                logger.error(f"❌ Order failed: {resp.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return False
    
    def detect_and_copy_trades(self):
        """Detect trades by comparing position snapshots"""
        try:
            # Get current positions
            self.current_target_positions = self.get_all_positions(self.target_wallet)
            
            if not self.last_target_positions:
                # First run - just save current state
                logger.info(f"📊 Initial scan: {len(self.current_target_positions)} positions found")
                logger.info(f"🔄 Baseline established - now monitoring for changes...")
                self.last_target_positions = self.current_target_positions.copy()
                self.save_state()
                return
            
            # Log that we're actively monitoring
            changes_detected = 0
            
            # Compare positions to detect changes
            all_tokens = set(list(self.last_target_positions.keys()) + list(self.current_target_positions.keys()))
            
            for token_id in all_tokens:
                old_size = self.last_target_positions.get(token_id, 0.0)
                new_size = self.current_target_positions.get(token_id, 0.0)
                
                change = new_size - old_size
                
                if abs(change) < 0.01:
                    continue  # No significant change
                
                changes_detected += 1
                
                # Trade detected!
                logger.info(f"\n{'='*70}")
                logger.info(f"🎯 TRADE DETECTED!")
                logger.info(f"Token: {token_id}")
                logger.info(f"Previous position: ${old_size:.2f}")
                logger.info(f"New position: ${new_size:.2f}")
                logger.info(f"Change: ${change:+.2f}")
                
                # Get market info
                market_info = self.get_market_info(token_id)
                if market_info:
                    question = market_info.get('question', 'Unknown')
                    logger.info(f"📋 Market: {question}")
                
                # Determine if BUY or SELL
                if change > 0:
                    # Position increased = BUY
                    self.copy_buy(token_id, change)
                else:
                    # Position decreased = SELL
                    self.copy_sell(token_id, abs(change), old_size)
                
                logger.info(f"{'='*70}\n")
            
            # Log if no changes (only every 12 checks = 1 minute)
            if not hasattr(self, '_quiet_check_counter'):
                self._quiet_check_counter = 0
            
            self._quiet_check_counter += 1
            if self._quiet_check_counter >= 12 and changes_detected == 0:
                logger.info(f"✓ No position changes (monitoring {len(self.current_target_positions)} positions)")
                self._quiet_check_counter = 0
            
            # Update last positions
            self.last_target_positions = self.current_target_positions.copy()
            self.save_state()
            
        except Exception as e:
            logger.error(f"Error detecting trades: {e}")
    
    def copy_buy(self, token_id: str, target_buy_size: float):
        """Copy a BUY trade"""
        try:
            # Get balances
            target_balance = self.get_balance(self.target_wallet)
            your_balance = self.get_balance(self.your_wallet)
            
            logger.info(f"💰 Target balance: ${target_balance:.2f}")
            logger.info(f"💰 Your balance: ${your_balance:.2f}")
            
            if your_balance < self.min_bet_size:
                logger.warning(f"⚠️  Insufficient balance")
                return
            
            # Calculate copy size
            copy_size = self.calculate_copy_size(target_buy_size, target_balance, your_balance)
            
            # Calculate percentages for logging
            target_pct = (target_buy_size / target_balance * 100) if target_balance > 0 else 0
            your_pct = (copy_size / your_balance * 100) if your_balance > 0 else 0
            
            logger.info(f"📊 Target BUY: ${target_buy_size:.2f} ({target_pct:.2f}% of wallet)")
            logger.info(f"📊 Your BUY: ${copy_size:.2f} ({your_pct:.2f}% of wallet)")
            
            if copy_size < 0.01:
                logger.warning(f"⚠️  Copy size too small")
                return
            
            # Place order
            success = self.place_market_order(token_id, copy_size, "BUY")
            
            if success:
                logger.info(f"✅ Successfully copied BUY!")
            else:
                logger.error(f"❌ Failed to copy BUY")
                
        except Exception as e:
            logger.error(f"Error copying buy: {e}")
    
    def copy_sell(self, token_id: str, target_sell_size: float, target_old_position: float):
        """Copy a SELL trade proportionally"""
        try:
            your_position = self.your_positions.get(token_id, 0.0)
            
            if your_position < 0.01:
                logger.warning(f"⚠️  No position to sell (you have ${your_position:.2f})")
                return
            
            # Calculate sell percentage
            sell_pct = (target_sell_size / target_old_position * 100) if target_old_position > 0 else 100
            
            # Apply same percentage to your position
            your_sell_size = (your_position * sell_pct) / 100
            your_sell_size = min(your_sell_size, your_position)
            
            logger.info(f"📉 Target SELL: ${target_sell_size:.2f} ({sell_pct:.1f}% of position)")
            logger.info(f"📉 Your SELL: ${your_sell_size:.2f} ({sell_pct:.1f}% of position)")
            
            if your_sell_size < 0.01:
                logger.warning(f"⚠️  Sell size too small")
                return
            
            # Place order
            success = self.place_market_order(token_id, your_sell_size, "SELL")
            
            if success:
                logger.info(f"✅ Successfully copied SELL!")
            else:
                logger.error(f"❌ Failed to copy SELL")
                
        except Exception as e:
            logger.error(f"Error copying sell: {e}")
    
    async def monitor_wallet(self):
        """Main monitoring loop"""
        logger.info(f"\n🤖 Bot Started - POSITION TRACKING MODE")
        logger.info(f"👀 Monitoring: {self.target_wallet}")
        logger.info(f"💼 Your wallet: {self.your_wallet}")
        logger.info(f"📊 Copy percentage: {self.copy_percentage}%")
        logger.info(f"💵 Max bet: ${self.max_bet_size}")
        logger.info(f"⚡ Checking every 5 seconds for real-time detection")
        logger.info(f"{'='*70}\n")
        
        # Load previous state
        self.load_state()
        
        consecutive_errors = 0
        max_errors = 5
        
        while True:
            try:
                # Check for trades by comparing positions
                self.detect_and_copy_trades()
                
                # Reset error counter
                consecutive_errors = 0
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Bot stopped by user")
                self.save_state()
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"❌ Error in monitoring loop ({consecutive_errors}/{max_errors}): {e}")
                
                if consecutive_errors >= max_errors:
                    logger.error("Too many consecutive errors. Stopping bot.")
                    break
                
                await asyncio.sleep(30)
    
    def run(self):
        """Start the bot"""
        if not self.target_wallet:
            logger.error("❌ TARGET_WALLET_ADDRESS not set!")
            return
        
        if not self.client or not self.your_wallet:
            logger.error("❌ Could not initialize client. Check YOUR_PRIVATE_KEY!")
            return
        
        try:
            asyncio.run(self.monitor_wallet())
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.save_state()
            logger.info("Bot stopped. State saved.")


if __name__ == "__main__":
    bot = PolymarketCopyBotPro()
    bot.run()
