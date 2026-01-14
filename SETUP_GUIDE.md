# Polymarket Copy Trading Bot Setup Guide

## 🎯 What This Bot Does

- **Tracks** a specific wallet's bets on Polymarket in real-time
- **Copies** their bets automatically using percentage-based position sizing
- **Runs 24/7** on free cloud hosting (no need to keep your computer on)
- **Shows bets** in your actual Polymarket portfolio (uses your real wallet)

## 📋 Prerequisites

1. **A Polymarket account** with some USDC on Polygon network
2. **Your wallet's private key** (we'll show you how to get this safely)
3. **The wallet address** you want to copy trades from
4. **Basic command line knowledge** (we'll walk you through it)

## 🔑 Step 1: Get Your Private Key (SAFELY)

### Using MetaMask:

1. Open MetaMask
2. Click the three dots menu → Account Details
3. Click "Show Private Key"
4. Enter your password
5. Copy your private key (keep this SECRET!)

⚠️ **SECURITY WARNING**: Never share your private key. Anyone with it can access your funds.

## 🎯 Step 2: Find the Wallet to Copy

1. Go to Polymarket.com
2. Find a trader you want to copy
3. Click on their profile
4. Copy their wallet address (starts with 0x...)

## 💻 Step 3: Setup Locally (Test First)

### Install Python 3.8+

**Windows**: Download from python.org
**Mac**: `brew install python3`
**Linux**: `sudo apt install python3 python3-pip`

### Setup the bot:

```bash
# 1. Download the bot files (or clone from GitHub)
cd polymarket-copy-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your configuration file
cp .env.example .env

# 4. Edit .env file with your details:
# - Add your TARGET_WALLET_ADDRESS
# - Add your YOUR_PRIVATE_KEY
# - Set COPY_PERCENTAGE (100 = same %, 50 = half the %, etc.)
# - Set MIN_BET_SIZE and MAX_BET_SIZE

# 5. Test the bot locally
python polymarket_bot_pro.py
```

## ☁️ Step 4: Deploy for FREE 24/7 Operation

### Option A: Railway (Recommended - Free & Easy)

Railway offers $5/month free credit which is MORE than enough for this bot.

1. **Sign up at railway.app** (free account)

2. **Create New Project** → Deploy from GitHub

3. **Connect your GitHub**:
   - Fork this repository to your GitHub
   - Or create a new repo and push the bot files

4. **Configure Environment Variables** in Railway dashboard:
   ```
   TARGET_WALLET_ADDRESS=0x...
   YOUR_PRIVATE_KEY=0x...
   COPY_PERCENTAGE=100
   MIN_BET_SIZE=1
   MAX_BET_SIZE=1000
   ```

5. **Deploy** - Railway will automatically start your bot!

6. **Monitor Logs** - Check the logs tab to see your bot working

### Option B: Render.com (Alternative Free Option)

1. Sign up at render.com (free tier)
2. Create New → Background Worker
3. Connect your GitHub repo
4. Set environment variables
5. Deploy!

### Option C: Fly.io (Advanced Users)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
fly launch

# Set secrets
fly secrets set TARGET_WALLET_ADDRESS=0x...
fly secrets set YOUR_PRIVATE_KEY=0x...
fly secrets set COPY_PERCENTAGE=100

# Deploy
fly deploy
```

## 🔍 Step 5: Verify It's Working

### Check the logs:

**Railway**: Dashboard → Logs tab
**Render**: Dashboard → Logs
**Fly.io**: `fly logs`

You should see:
```
✅ Connected - Your wallet: 0x...
🤖 Bot Started
👀 Monitoring: 0x...
```

### Check your Polymarket portfolio:

1. Go to polymarket.com
2. Connect your wallet
3. View your portfolio
4. Your copied bets will appear here just like manual bets!

## ⚙️ Configuration Options

### In your .env file:

```bash
# Required
TARGET_WALLET_ADDRESS=0x1234...  # Wallet to copy
YOUR_PRIVATE_KEY=0xabcd...       # Your wallet private key

# Optional (with defaults)
COPY_PERCENTAGE=100              # 100 = same %, 50 = half, 200 = double
MIN_BET_SIZE=1                   # Minimum bet in USDC
MAX_BET_SIZE=1000                # Maximum bet in USDC
POLYGON_RPC_URL=https://polygon-rpc.com  # Polygon node
```

### Copy Percentage Examples:

- `COPY_PERCENTAGE=100` → If target bets 10% of their balance, you bet 10% of yours
- `COPY_PERCENTAGE=50` → If target bets 10%, you bet 5%
- `COPY_PERCENTAGE=200` → If target bets 10%, you bet 20% (risky!)

## 📊 Monitoring Your Bot

### View Real-Time Activity:

1. **Check cloud logs** - See every bet as it happens
2. **Check Polymarket portfolio** - See your positions
3. **Check bot logs file** - Local file: `polymarket_bot.log`

### What you'll see in logs:

```
🎯 NEW ORDER DETECTED from 0x1234...
📋 Market: Will Biden win 2024?
💰 Target balance: $5000.00
💰 Your balance: $1000.00
📊 Target: $500.00 (10.00%)
📊 Your bet: $100.00 (10.00%)
📤 Placing BUY order: $100.00...
✅ Order placed successfully!
```

## 🔒 Security Best Practices

1. **Never commit .env to git**
   - Already in .gitignore
   - Double-check before pushing

2. **Use a dedicated trading wallet**
   - Don't use your main wallet
   - Transfer only what you want to trade

3. **Set reasonable limits**
   - Use MAX_BET_SIZE to cap risk
   - Keep some USDC as buffer

4. **Monitor regularly**
   - Check logs daily
   - Verify bets on Polymarket

## ❌ Troubleshooting

### Bot won't start:

```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check .env file
cat .env  # Should show your config
```

### No orders being copied:

1. **Check target wallet is active** - Visit their Polymarket profile
2. **Check logs** - Are new orders being detected?
3. **Check your balance** - Need enough USDC for bets
4. **Check MIN_BET_SIZE** - Might be filtering small bets

### Orders failing to place:

1. **Check balance** - Need USDC on Polygon
2. **Check private key** - Should start with 0x
3. **Check Polygon RPC** - Try different RPC URL
4. **Check gas** - Need small amount of MATIC for gas

### "Insufficient balance" error:

- Add more USDC to your wallet on Polygon network
- Or reduce COPY_PERCENTAGE

## 💰 Cost Breakdown

### Free Tier Options:

1. **Railway**: $5/month credit (FREE) - enough for this bot
2. **Render**: 750 hours/month free
3. **Fly.io**: 3 shared CPUs free

### Actual Costs:

- **Hosting**: $0/month (free tier)
- **Polygon gas**: ~$0.01 per bet (very cheap)
- **Total**: Basically free! 🎉

## 🎓 Advanced Features

### Track Multiple Wallets:

Run multiple bot instances with different configs:

```bash
# Bot 1: Copy whale trader
python polymarket_bot_pro.py --config whale.env

# Bot 2: Copy analyst
python polymarket_bot_pro.py --config analyst.env
```

### Custom Bet Sizing:

Edit the `calculate_copy_size()` function to implement:
- Kelly Criterion sizing
- Fixed dollar amounts
- Time-based adjustments
- Custom risk limits

### Notifications:

Add Discord/Telegram notifications:

```python
# In process_new_order(), add:
import requests

def send_discord_notification(message):
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    requests.post(webhook_url, json={"content": message})

# Call after successful bet:
send_discord_notification(f"✅ Copied {side} bet: ${copy_size:.2f}")
```

## 🆘 Support & Resources

- **Polymarket Docs**: https://docs.polymarket.com
- **Polymarket API**: https://docs.polymarket.com/api
- **Web3.py Docs**: https://web3py.readthedocs.io
- **Python-dotenv**: https://github.com/theskumar/python-dotenv

## ⚖️ Legal Disclaimer

This bot is for educational purposes. Use at your own risk. Trading involves risk of loss. Make sure you understand:

- How Polymarket works
- The risks of automated trading
- Your local regulations regarding prediction markets

Not financial advice. DYOR (Do Your Own Research).

## 🐛 Known Issues

1. **Order matching may fail during high volatility** - Bot uses market orders which might not fill during extreme moves
2. **API rate limits** - If target wallet is VERY active (100+ bets/day), may hit rate limits
3. **Slippage** - On illiquid markets, you might get worse prices than target wallet

## 🔄 Updates & Maintenance

The bot saves its state to `processed_orders.json`. This means:
- Safe to restart without duplicating bets
- Tracks what's been copied
- Resumes from last checkpoint

To update the bot:
```bash
git pull  # Get latest version
pip install -r requirements.txt --upgrade
# Restart on your cloud platform
```

## ✅ Final Checklist

Before deploying:

- [ ] Tested locally and saw "✅ Connected" message
- [ ] .env file has correct wallet addresses
- [ ] Your wallet has USDC on Polygon network
- [ ] Your wallet has small amount of MATIC for gas
- [ ] MIN_BET_SIZE and MAX_BET_SIZE are set appropriately
- [ ] Deployed to Railway/Render/Fly.io
- [ ] Checked logs and see monitoring messages
- [ ] Verified test bet appears in Polymarket portfolio

## 🚀 You're Ready!

Your bot is now running 24/7, copying trades automatically, and showing all bets in your actual Polymarket portfolio!

Happy trading! 📈
