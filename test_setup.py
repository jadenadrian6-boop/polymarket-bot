#!/usr/bin/env python3
"""
Test script to verify your Polymarket bot setup
Run this before deploying to make sure everything works
"""

import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists and is configured"""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Create it by copying .env.template:")
        print("   cp .env.template .env")
        return False
    
    print("✅ .env file found")
    return True

def check_configuration():
    """Check if required environment variables are set"""
    load_dotenv()
    
    issues = []
    
    target_wallet = os.getenv('TARGET_WALLET_ADDRESS')
    if not target_wallet or target_wallet == '':
        issues.append("TARGET_WALLET_ADDRESS not set")
    elif not target_wallet.startswith('0x'):
        issues.append("TARGET_WALLET_ADDRESS should start with 0x")
    else:
        print(f"✅ Target wallet: {target_wallet[:10]}...{target_wallet[-8:]}")
    
    private_key = os.getenv('YOUR_PRIVATE_KEY')
    if not private_key or private_key == '':
        issues.append("YOUR_PRIVATE_KEY not set")
    elif not private_key.startswith('0x'):
        issues.append("YOUR_PRIVATE_KEY should start with 0x")
    else:
        print("✅ Private key configured")
    
    copy_pct = os.getenv('COPY_PERCENTAGE', '100')
    try:
        pct = float(copy_pct)
        if pct <= 0 or pct > 1000:
            issues.append("COPY_PERCENTAGE should be between 1 and 1000")
        else:
            print(f"✅ Copy percentage: {pct}%")
    except:
        issues.append("COPY_PERCENTAGE must be a number")
    
    if issues:
        print("\n❌ Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import web3
        print("✅ web3 installed")
    except ImportError:
        print("❌ web3 not installed")
        print("   Run: pip install -r requirements.txt")
        return False
    
    try:
        import requests
        print("✅ requests installed")
    except ImportError:
        print("❌ requests not installed")
        return False
    
    try:
        from py_clob_client.client import ClobClient
        print("✅ py-clob-client installed")
    except ImportError:
        print("❌ py-clob-client not installed")
        return False
    
    return True

def test_connection():
    """Test connection to Polymarket API"""
    try:
        import requests
        response = requests.get("https://clob.polymarket.com/health", timeout=5)
        if response.status_code == 200:
            print("✅ Polymarket API is reachable")
            return True
        else:
            print(f"⚠️  Polymarket API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach Polymarket API: {e}")
        return False

def test_wallet_connection():
    """Test if we can initialize the wallet"""
    try:
        load_dotenv()
        from web3 import Web3
        from eth_account import Account
        
        private_key = os.getenv('YOUR_PRIVATE_KEY')
        if not private_key:
            print("❌ Cannot test wallet - private key not set")
            return False
        
        account = Account.from_key(private_key)
        print(f"✅ Wallet initialized: {account.address[:10]}...{account.address[-8:]}")
        return True
    except Exception as e:
        print(f"❌ Error initializing wallet: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing Polymarket Bot Setup\n")
    print("="*50)
    
    all_passed = True
    
    print("\n1️⃣ Checking .env file...")
    if not check_env_file():
        all_passed = False
        print("\nPlease create .env file before continuing")
        sys.exit(1)
    
    print("\n2️⃣ Checking configuration...")
    if not check_configuration():
        all_passed = False
    
    print("\n3️⃣ Checking dependencies...")
    if not check_dependencies():
        all_passed = False
        print("\nPlease install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n4️⃣ Testing API connection...")
    if not test_connection():
        all_passed = False
    
    print("\n5️⃣ Testing wallet initialization...")
    if not test_wallet_connection():
        all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to run the bot!")
        print("\n📝 Next steps:")
        print("   1. Test locally: python polymarket_bot_pro.py")
        print("   2. Deploy to cloud: See SETUP_GUIDE.md")
        print("   3. Monitor logs to see it working!")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("   See SETUP_GUIDE.md for help")
        sys.exit(1)

if __name__ == "__main__":
    main()
