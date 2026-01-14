# 🤖 Polymarket Copy Trading Bot

Automatically copy trades from any Polymarket wallet with percentage-based position sizing. Runs 24/7 on free cloud hosting.

## ✨ Features

- ✅ **Real-time monitoring** - Tracks target wallet every 15 seconds
- ✅ **Percentage-based copying** - Mirrors bet sizes relative to your balance
- ✅ **24/7 operation** - Runs on free cloud hosting (Railway, Render, Fly.io)
- ✅ **Shows in your portfolio** - All bets appear in your actual Polymarket account
- ✅ **Safety limits** - Min/max bet size controls
- ✅ **Zero cost** - Free hosting + minimal gas fees (~$0.01 per bet)
- ✅ **Easy setup** - 10 minutes to deploy

## 🚀 Quick Start

### 1. Prerequisites

- Polymarket account with USDC on Polygon
- Your wallet's private key (from MetaMask)
- Wallet address you want to copy

### 2. Setup Locally (Test First)

```bash
# Clone or download this repo
git clone [your-repo-url]
cd polymarket-copy-bot

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.template .env
# Edit .env with your settings

# Test locally
python polymarket_bot_pro.py
```

### 3. Deploy to Cloud (FREE)

#### Railway (Recommended):

1. Sign up at https://railway.app
2. New Project → Deploy from GitHub
3. Add environment variables from your .env
4. Deploy! ✨

#### Render:

1. Sign up at https://render.com
2. New → Background Worker
3. Connect repo & add environment variables
4. Deploy!

#### Fly.io:

```bash
fly auth login
fly launch
fly secrets set TARGET_WALLET_ADDRESS=0x...
fly secrets set YOUR_PRIVATE_KEY=0x...
fly deploy
```

### 4. Verify It's Working

- Check cloud platform logs for "✅ Connected"
- Wait for target wallet to place a bet
- Check your Polymarket portfolio to see copied bet!

## 📖 Full Documentation

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for:
- Detailed setup instructions
- How to get your private key safely
- Configuration options
- Troubleshooting
- Advanced features

## ⚙️ Configuration

Key settings in `.env`:

```bash
TARGET_WALLET_ADDRESS=0x...    # Wallet to copy
YOUR_PRIVATE_KEY=0x...         # Your wallet (keep secret!)
COPY_PERCENTAGE=100            # 100 = same %, 50 = half
MIN_BET_SIZE=1                 # Minimum bet in USDC
MAX_BET_SIZE=1000              # Maximum bet in USDC
```

## 💰 Costs

- **Hosting**: $0/month (free tier)
- **Gas fees**: ~$0.01 per bet on Polygon
- **Total**: Essentially free! 🎉

## 📊 How It Works

1. Bot monitors target wallet for new orders
2. When bet detected, calculates percentage of their balance
3. Places same percentage bet with your balance
4. Respects your min/max limits
5. Bet shows up in your Polymarket portfolio!

## 🔒 Security

- Private key never leaves your cloud instance
- .env file excluded from git
- Use a dedicated trading wallet (recommended)
- Set MAX_BET_SIZE to limit risk

## ❓ FAQ

**Q: Will my bets show in my Polymarket portfolio?**  
A: Yes! The bot uses your actual wallet, so all bets appear in your portfolio just like manual trades.

**Q: How much does hosting cost?**  
A: $0/month on free tiers (Railway, Render, Fly.io all have free options).

**Q: What if the target wallet trades a lot?**  
A: The bot handles high-frequency trading. You can adjust CHECK_INTERVAL if needed.

**Q: Can I copy multiple wallets?**  
A: Run multiple bot instances with different .env configs.

**Q: What if I want to stop?**  
A: Just stop the cloud service. Your existing positions remain in your portfolio.

## 🛠️ Troubleshooting

**Bot not copying bets:**
- Check target wallet is actually trading
- Verify you have enough USDC balance
- Check MIN_BET_SIZE isn't filtering bets out
- Review logs for errors

**"Insufficient balance" errors:**
- Add more USDC to your Polygon wallet
- Or reduce COPY_PERCENTAGE

**Orders failing:**
- Ensure you have MATIC for gas fees
- Check POLYGON_RPC_URL is working
- Verify private key is correct

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting.

## 📁 Project Structure

```
polymarket-copy-bot/
├── polymarket_bot_pro.py    # Main bot (use this one!)
├── polymarket_copy_bot.py   # Basic version (reference)
├── requirements.txt         # Python dependencies
├── .env.template           # Configuration template
├── Procfile                # Railway/Heroku config
├── railway.json            # Railway specific config
├── Dockerfile              # Docker deployment
├── SETUP_GUIDE.md          # Detailed setup guide
└── README.md               # This file
```

## 🔄 Updates

To update your deployed bot:

```bash
git pull
pip install -r requirements.txt --upgrade
# Redeploy on your platform
```

## ⚖️ Disclaimer

This bot is for educational purposes. Trading involves risk. Not financial advice. DYOR.

- Understand Polymarket risks
- Check your local regulations
- Start with small amounts
- Monitor regularly

## 🤝 Contributing

Issues and pull requests welcome! Please ensure:
- Code follows existing style
- Tests pass locally
- Update documentation

## 📜 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Polymarket Docs**: https://docs.polymarket.com
- **Issues**: Open a GitHub issue

---

**Built with ❤️ for the Polymarket community**

*Star ⭐ this repo if it helps you!*
