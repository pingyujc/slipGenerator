# Slip Generator

Automates finding top +EV props from OddsJam and generates PrizePicks parlay links sent via Telegram.

## Features

- ✅ Scrapes OddsJam for +EV props
- ✅ Extracts PrizePicks projection data from "Place Bet" links
- ✅ Filters props by EV threshold and other criteria
- ✅ Generates PrizePicks parlay links
- ✅ Sends notifications via Telegram bot
- ✅ Configurable scheduling and filtering
- ✅ Comprehensive logging

## Quick Start

1. **Setup**:
   ```bash
   python setup.py
   ```

2. **Configure**:
   - Edit `.env` with your Telegram bot credentials
   - Adjust settings in `config.json`

3. **Run**:
   ```bash
   ./run.sh          # Linux/Mac
   run.bat           # Windows
   ```

## Configuration

### Environment Variables (.env)

```bash
# Required: Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional: OddsJam Login
ODDSJAM_EMAIL=your_email@example.com
ODDSJAM_PASSWORD=your_password
```

### Settings (config.json)

Key settings you can adjust:

- `filters.min_ev_percent`: Minimum EV % (default: 5.0)
- `filters.max_legs`: Maximum parlay legs (default: 3)
- `schedule.refresh_interval_minutes`: How often to check (default: 5)
- `filters.sports`: Limit to specific sports (empty = all)

## How It Works

1. **Data Extraction**: Scrapes OddsJam dashboard for props with PrizePicks "Place Bet" links
2. **Parsing**: Extracts projection ID, side (o/u), line value, and EV% from URLs like:
   ```
   https://app.prizepicks.com/?projections=6052266-o-7.5
   ```
3. **Filtering**: Sorts by EV% and applies your criteria
4. **Link Generation**: Creates parlay links like:
   ```
   https://app.prizepicks.com/?projections=6052266-o-7.5,6054008-u-29.5
   ```
5. **Notification**: Sends formatted message with clickable link via Telegram

## Telegram Setup

1. **Create Bot**:
   - Message [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow instructions
   - Copy token to `.env`

2. **Get Chat ID**:
   - Message [@userinfobot](https://t.me/userinfobot)
   - Copy your user ID to `.env`

## Example Output

```
🎯 New +EV Slip Found!

1. LeBron James - Points
   Over 25.5 (+8.2% EV)

2. Stephen Curry - 3-Pointers
   Over 3.5 (+6.1% EV)

3. Nikola Jokic - Rebounds
   Under 12.5 (+5.8% EV)

Total EV: +20.1%
Legs: 3

🔗 Click to Bet on PrizePicks
```

## Files

- `slip_generator.py`: Main application
- `config.json`: Settings and preferences
- `.env`: Sensitive credentials
- `requirements.txt`: Python dependencies
- `setup.py`: Automated setup script

## Troubleshooting

- **No props found**: Check OddsJam login or try without login
- **Telegram not working**: Verify bot token and chat ID
- **Missing data**: OddsJam may have changed their HTML structure

## 🧪 Local Testing

### Setup
```bash
python setup.py    # Creates venv and installs dependencies
```

### Configure
Edit `.env` with your Telegram credentials:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Run
```bash
./run.sh          # Mac/Linux
run.bat           # Windows
```

## 📱 Getting Telegram Credentials

### Bot Token
1. Message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow prompts to name your bot
4. Copy the token to `.env`

### Chat ID
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your user ID to `.env`

## Legal Notice

This tool is for educational purposes. Users are responsible for compliance with all applicable laws and terms of service.
