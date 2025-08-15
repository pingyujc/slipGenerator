#!/usr/bin/env python3
"""
Slip Generator - Automated +EV prop finder for OddsJam -> PrizePicks
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import schedule

# Load environment variables
load_dotenv()

@dataclass
class Prop:
    """Represents a sports betting proposition"""
    prizepicks_id: str
    side: str  # 'o' for over, 'u' for under
    line: float
    ev_percent: float
    player_name: str
    stat_type: str
    sport: str
    
    def to_prizepicks_format(self) -> str:
        """Convert to PrizePicks URL format: id-side-line"""
        return f"{self.prizepicks_id}-{self.side}-{self.line}"

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration values"""
        required_keys = [
            'oddsjam.url',
            'prizepicks.base_url',
            'telegram.bot_token',
            'telegram.chat_id'
        ]
        
        for key in required_keys:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value.get(k)
                if value is None:
                    raise ValueError(f"Missing required config: {key}")
    
    def get(self, key: str, default=None):
        """Get config value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value

class OddsJamExtractor:
    """Extracts prop data from OddsJam"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def login(self) -> bool:
        """Login to OddsJam if credentials are provided"""
        email = os.getenv('ODDSJAM_EMAIL')
        password = os.getenv('ODDSJAM_PASSWORD')
        
        if not email or not password:
            logging.warning("No OddsJam credentials provided. Attempting to scrape without login.")
            return False
        
        try:
            # Get login page
            login_url = "https://app.oddsjam.com/login"
            response = self.session.get(login_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find CSRF token or other required fields
            csrf_token = soup.find('meta', {'name': 'csrf-token'})
            if csrf_token:
                self.session.headers['X-CSRF-TOKEN'] = csrf_token.get('content')
            
            # Submit login
            login_data = {
                'email': email,
                'password': password
            }
            
            response = self.session.post(login_url, data=login_data)
            
            # Check if login was successful
            if 'dashboard' in response.url or response.status_code == 200:
                logging.info("Successfully logged into OddsJam")
                return True
            else:
                logging.error("Failed to login to OddsJam")
                return False
                
        except Exception as e:
            logging.error(f"Error during OddsJam login: {e}")
            return False
    
    def extract_props(self) -> List[Prop]:
        """Extract props from OddsJam dashboard"""
        try:
            dashboard_url = self.config.get('oddsjam.url')
            response = self.session.get(dashboard_url)
            
            if response.status_code != 200:
                logging.error(f"Failed to fetch OddsJam dashboard: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            props = []
            
            # Look for "Place Bet" links that contain PrizePicks URLs
            bet_links = soup.find_all('a', href=re.compile(r'app\.prizepicks\.com'))
            
            for link in bet_links:
                href = link.get('href')
                prop = self._parse_prizepicks_link(href, link)
                if prop:
                    props.append(prop)
            
            # Alternative: Look for data attributes or structured data
            if not props:
                props = self._extract_from_data_attributes(soup)
            
            logging.info(f"Extracted {len(props)} props from OddsJam")
            return props
            
        except Exception as e:
            logging.error(f"Error extracting props from OddsJam: {e}")
            return []
    
    def _parse_prizepicks_link(self, href: str, element) -> Optional[Prop]:
        """Parse PrizePicks link to extract prop data"""
        try:
            # Extract projections parameter from URL
            parsed_url = urlparse(href)
            query_params = parse_qs(parsed_url.query)
            projections = query_params.get('projections', [])
            
            if not projections:
                return None
            
            # Parse projection format: id-side-line
            projection = projections[0]
            parts = projection.split('-')
            
            if len(parts) != 3:
                return None
            
            prizepicks_id, side, line = parts
            
            # Extract additional data from surrounding elements
            ev_percent = self._extract_ev_from_element(element)
            player_name = self._extract_player_name(element)
            stat_type = self._extract_stat_type(element)
            sport = self._extract_sport(element)
            
            return Prop(
                prizepicks_id=prizepicks_id,
                side=side,
                line=float(line),
                ev_percent=ev_percent,
                player_name=player_name,
                stat_type=stat_type,
                sport=sport
            )
            
        except Exception as e:
            logging.error(f"Error parsing PrizePicks link {href}: {e}")
            return None
    
    def _extract_ev_from_element(self, element) -> float:
        """Extract EV percentage from element or nearby elements"""
        try:
            # Look for EV percentage in the element or parent elements
            current = element
            for _ in range(5):  # Check up to 5 parent levels
                if current is None:
                    break
                
                # Look for percentage text
                text = current.get_text()
                ev_match = re.search(r'(\d+\.?\d*)%', text)
                if ev_match:
                    return float(ev_match.group(1))
                
                current = current.parent
            
            # Default to 0 if not found
            return 0.0
            
        except:
            return 0.0
    
    def _extract_player_name(self, element) -> str:
        """Extract player name from element"""
        try:
            # Look for player name in various possible locations
            current = element
            for _ in range(3):
                if current is None:
                    break
                
                # Look for elements that might contain player names
                name_elem = current.find(class_=re.compile(r'player|name', re.I))
                if name_elem:
                    return name_elem.get_text().strip()
                
                current = current.parent
            
            return "Unknown Player"
            
        except:
            return "Unknown Player"
    
    def _extract_stat_type(self, element) -> str:
        """Extract stat type from element"""
        try:
            text = element.get_text()
            # Common stat types
            stat_patterns = [
                r'points?', r'rebounds?', r'assists?', r'steals?', r'blocks?',
                r'touchdowns?', r'yards?', r'receptions?', r'goals?', r'saves?'
            ]
            
            for pattern in stat_patterns:
                if re.search(pattern, text, re.I):
                    return re.search(pattern, text, re.I).group()
            
            return "Unknown Stat"
            
        except:
            return "Unknown Stat"
    
    def _extract_sport(self, element) -> str:
        """Extract sport from element"""
        try:
            text = element.get_text()
            sports = ['NBA', 'NFL', 'NHL', 'MLB', 'Soccer', 'Tennis', 'Golf']
            
            for sport in sports:
                if sport.lower() in text.lower():
                    return sport
            
            return "Unknown Sport"
            
        except:
            return "Unknown Sport"
    
    def _extract_from_data_attributes(self, soup) -> List[Prop]:
        """Alternative extraction method using data attributes"""
        props = []
        try:
            # Look for elements with data attributes that might contain prop data
            prop_elements = soup.find_all(attrs={'data-prop': True})
            
            for elem in prop_elements:
                # Parse data attributes
                data_prop = elem.get('data-prop')
                if data_prop:
                    # Assume JSON format in data attribute
                    prop_data = json.loads(data_prop)
                    prop = self._create_prop_from_data(prop_data)
                    if prop:
                        props.append(prop)
            
        except Exception as e:
            logging.error(f"Error extracting from data attributes: {e}")
        
        return props
    
    def _create_prop_from_data(self, data: dict) -> Optional[Prop]:
        """Create Prop object from data dictionary"""
        try:
            return Prop(
                prizepicks_id=data.get('prizepicks_id', ''),
                side=data.get('side', ''),
                line=float(data.get('line', 0)),
                ev_percent=float(data.get('ev_percent', 0)),
                player_name=data.get('player_name', 'Unknown'),
                stat_type=data.get('stat_type', 'Unknown'),
                sport=data.get('sport', 'Unknown')
            )
        except:
            return None

class PropFilter:
    """Filters and selects props based on criteria"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def filter_and_select(self, props: List[Prop]) -> List[Prop]:
        """Filter props and select top candidates"""
        # Filter by minimum EV
        min_ev = self.config.get('filters.min_ev_percent', 5.0)
        filtered_props = [p for p in props if p.ev_percent >= min_ev]
        
        # Filter by sports if specified
        allowed_sports = self.config.get('filters.sports', [])
        if allowed_sports:
            filtered_props = [p for p in filtered_props if p.sport in allowed_sports]
        
        # Sort by EV percentage (highest first)
        filtered_props.sort(key=lambda x: x.ev_percent, reverse=True)
        
        # Select top N legs
        max_legs = self.config.get('filters.max_legs', 3)
        selected_props = filtered_props[:max_legs]
        
        logging.info(f"Filtered {len(props)} props to {len(selected_props)} top picks")
        return selected_props

class PrizePicksLinkGenerator:
    """Generates PrizePicks parlay links"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def generate_link(self, props: List[Prop]) -> str:
        """Generate PrizePicks parlay link"""
        if not props:
            return ""
        
        base_url = self.config.get('prizepicks.base_url')
        projections = [prop.to_prizepicks_format() for prop in props]
        link = base_url + ",".join(projections)
        
        logging.info(f"Generated PrizePicks link with {len(props)} legs")
        return link

class TelegramNotifier:
    """Sends notifications via Telegram"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or config.get('telegram.bot_token')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID') or config.get('telegram.chat_id')
    
    def send_slip(self, props: List[Prop], link: str):
        """Send slip notification to Telegram"""
        if not self.config.get('telegram.enabled', True):
            logging.info("Telegram notifications disabled")
            return
        
        if not self.bot_token or not self.chat_id:
            logging.error("Telegram bot token or chat ID not configured")
            return
        
        try:
            # Calculate total EV
            total_ev = sum(prop.ev_percent for prop in props)
            
            # Build message
            message = "🎯 **New +EV Slip Found!**\n\n"
            
            for i, prop in enumerate(props, 1):
                side_text = "Over" if prop.side == 'o' else "Under"
                message += f"{i}. **{prop.player_name}** - {prop.stat_type}\n"
                message += f"   {side_text} {prop.line} ({prop.ev_percent:+.1f}% EV)\n\n"
            
            message += f"**Total EV:** {total_ev:+.1f}%\n"
            message += f"**Legs:** {len(props)}\n\n"
            message += f"[🔗 **Click to Bet on PrizePicks**]({link})"
            
            # Send message
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logging.info("Successfully sent Telegram notification")
            else:
                logging.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                
        except Exception as e:
            logging.error(f"Error sending Telegram notification: {e}")

class SlipGenerator:
    """Main application class"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = ConfigManager(config_path)
        self.oddsjam = OddsJamExtractor(self.config)
        self.filter = PropFilter(self.config)
        self.link_generator = PrizePicksLinkGenerator(self.config)
        self.notifier = TelegramNotifier(self.config)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get('logging.level', 'INFO'))
        log_file = self.config.get('logging.file', 'slip_generator.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def run_once(self):
        """Run one iteration of the slip generation process"""
        logging.info("Starting slip generation cycle")
        
        try:
            # Login to OddsJam if needed
            if self.config.get('oddsjam.login_required', False):
                self.oddsjam.login()
            
            # Extract props
            props = self.oddsjam.extract_props()
            
            if not props:
                logging.info("No props found, skipping this cycle")
                return
            
            # Filter and select props
            selected_props = self.filter.filter_and_select(props)
            
            if not selected_props:
                logging.info("No props met filtering criteria")
                return
            
            # Generate PrizePicks link
            link = self.link_generator.generate_link(selected_props)
            
            if not link:
                logging.error("Failed to generate PrizePicks link")
                return
            
            # Send notification
            self.notifier.send_slip(selected_props, link)
            
            logging.info(f"Successfully generated and sent slip with {len(selected_props)} props")
            
        except Exception as e:
            logging.error(f"Error in slip generation cycle: {e}")
    
    def run_scheduled(self):
        """Run with scheduling"""
        if not self.config.get('schedule.enabled', True):
            logging.info("Scheduling disabled, running once")
            self.run_once()
            return
        
        interval_minutes = self.config.get('schedule.refresh_interval_minutes', 1)
        
        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.run_once)
        
        logging.info(f"Scheduled to run every {interval_minutes} minutes")
        logging.info("Press Ctrl+C to stop")
        
        # Run once immediately
        self.run_once()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Stopping slip generator")

def main():
    """Main entry point"""
    try:
        generator = SlipGenerator()
        generator.run_scheduled()
    except Exception as e:
        logging.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()