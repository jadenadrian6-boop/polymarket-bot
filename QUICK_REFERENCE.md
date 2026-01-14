# Quick Reference Guide

## 🚀 Common Commands

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test your setup
python test_setup.py

# Run the bot locally
python polymarket_bot_pro.py

# Stop the bot
Ctrl+C
```

### Railway Deployment
```bash
# View logs
railway logs

# Restart bot
railway restart

# Update environment variables
railway variables set COPY_PERCENTAGE=50

# Delete deployment
railway down
```

### Fly.io Deployment
```bash
# View logs
fly logs

# Restart bot
fly restart

# Update secrets
fly secrets set COPY_PERCENTAGE=50

# Delete deployment
fly destroy
```

### Docker
```bash
# Build image
docker build -t polymarket-bot .

# Run container
docker run -d --env-file .env polymarket-bot

# View logs
docker logs <container_id>

# Stop container
docker stop <container_id>
```

## 🔧 Configuration Examples

### Conservative Trading (Low Risk)
```bash
COPY_PERCENTAGE=30
MIN_BET_SIZE=5
MAX_BET_SIZE=50
```

### Moderate Trading (Medium Risk)
```bash
COPY_PERCENTAGE=100
MIN_BET_SIZE=1
MAX_BET_SIZE=200
```

### Aggressive Trading (High Risk)
```bash
COPY_PERCENTAGE=200
MIN_BET_SIZE=1
MAX_BET_SIZE=1000
```

## 📊 Monitoring

### What to Look For in Logs

**Good Signs:**
```
✅ Connected - Your wallet: 0x...
🤖 Bot Started
👀 Monitoring: 0x...
🔔 Found 1 new order(s)!
✅ Order placed successfully!
```

**Warning Signs:**
```
⚠️ Insufficient balance
⚠️ Copy size below minimum
```

**Error Signs:**
```
❌ Could not fetch orders
❌ Error placing order
❌ Client not initialized
```

## 🐛 Quick Fixes

### Bot Not Starting
```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Verify .env file
cat .env
```

### No Trades Being Copied
```bash
# Check target wallet activity on Polymarket
# Check your balance: Need USDC + MATIC
# Lower MIN_BET_SIZE if filtering too much
# Check logs for detection messages
```

### Orders Failing
```bash
# Verify balance
# Check private key is correct
# Try different RPC URL
# Ensure MATIC for gas
```

## 💡 Pro Tips

1. **Start Small**: Test with COPY_PERCENTAGE=10 first
2. **Monitor Daily**: Check logs and portfolio daily
3. **Use Limits**: Always set MAX_BET_SIZE
4. **Separate Wallet**: Use dedicated trading wallet
5. **Gas Buffer**: Keep 1-2 MATIC for gas
6. **Balance Buffer**: Keep 10% USDC as buffer

## 📱 View Your Bets

1. Go to https://polymarket.com
2. Connect your wallet
3. Click "Portfolio"
4. All copied bets appear here!

## 🔄 Update Bot

```bash
# Pull latest version
git pull

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# On cloud platform:
# - Railway: Push to GitHub (auto-deploys)
# - Render: Manual deploy from dashboard
# - Fly.io: fly deploy
```

## 📞 Emergency Stop

**Stop Immediately:**
1. Go to your cloud platform dashboard
2. Click "Stop" or "Pause"
3. Your existing positions remain
4. No new bets will be placed

**Resume Later:**
1. Click "Start" or "Resume"
2. Bot resumes from last checkpoint
3. Won't duplicate previous bets

## 🎯 Finding Good Wallets to Copy

1. **Browse Polymarket Leaderboards**
   - Look for consistent performers
   - Check their win rate
   - View their bet history

2. **Check Activity Level**
   - Active traders (several bets/day)
   - Consistent over time
   - Diversified markets

3. **Analyze Strategy**
   - Do they have a edge?
   - What markets do they focus on?
   - What's their typical position size?

## ⚙️ Advanced Configuration

### Multiple Wallets
Create separate .env files:
```bash
# .env.whale
TARGET_WALLET_ADDRESS=0x...whale...

# .env.analyst  
TARGET_WALLET_ADDRESS=0x...analyst...

# Run both
python polymarket_bot_pro.py  # Uses .env
python polymarket_bot_pro.py --config .env.analyst
```

### Custom Sizing Logic
Edit `calculate_copy_size()` in polymarket_bot_pro.py:
```python
def calculate_copy_size(self, target_bet_size, target_balance, your_balance):
    # Your custom logic here
    # Example: Fixed $10 per bet
    return 10.0
```

### Notifications (Coming Soon)
Add to .env:
```bash
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

## 📖 Resources

- **Polymarket API Docs**: https://docs.polymarket.com
- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **README**: [README.md](README.md)
- **Web3 Docs**: https://web3py.readthedocs.io

## 🆘 Still Having Issues?

1. Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed help
2. Check logs for specific error messages
3. Verify all prerequisites are met
4. Test locally before deploying
5. Open GitHub issue with error details

---

**Pro Tip**: Bookmark this page for quick reference! 📌
