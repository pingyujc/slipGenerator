#!/usr/bin/env python3
"""
Setup script for Slip Generator
"""

import os
import subprocess
import sys
import venv

def create_virtual_environment():
    """Create virtual environment"""
    venv_dir = "venv"
    
    if os.path.exists(venv_dir):
        print("✓ Virtual environment already exists")
        return venv_dir
    
    print("Creating virtual environment...")
    venv.create(venv_dir, with_pip=True)
    print("✓ Created virtual environment")
    return venv_dir

def get_venv_python(venv_dir):
    """Get path to virtual environment Python executable"""
    return os.path.join(venv_dir, "bin", "python")

def install_requirements():
    """Install required packages in virtual environment"""
    print("Installing required packages in virtual environment...")
    venv_dir = create_virtual_environment()
    venv_python = get_venv_python(venv_dir)
    
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Packages installed in virtual environment")
    """Setup environment file"""
    if not os.path.exists('.env'):
        print("Creating .env file from template...")
        with open('.env.example', 'r') as template:
            content = template.read()
        
        with open('.env', 'w') as env_file:
            env_file.write(content)
        
        print("✓ Created .env file")
        print("⚠️  Please edit .env file with your actual credentials")
    else:
        print("✓ .env file already exists")


def main():
    """Main setup function"""
    print("🎯 Setting up Slip Generator...")
    print()
    
    try:
        install_requirements()
        
        print()
        print("✅ Setup complete!")
        print()
        print("Next steps for LOCAL TESTING:")
        print("1. Edit .env file with your Telegram bot token and chat ID")
        print("2. Optionally add OddsJam credentials to .env")  
        print("3. Run: ./run.sh (Mac/Linux) or run.bat (Windows)")
        print()
        print("To get a Telegram bot token:")
        print("1. Message @BotFather on Telegram")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the token to your .env file")
        print()
        print("To get your chat ID:")
        print("1. Message @userinfobot on Telegram")
        print("2. Copy the ID to your .env file")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()