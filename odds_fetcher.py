#!/usr/bin/env python3
"""
Fetch live NBA props from The Odds API
Supports multiple sportsbooks (DraftKings, FanDuel, BetMGM, etc.)

NOTE: Player props market requires a paid subscription on The Odds API.
The free tier only includes head-to-head (h2h) odds.

For demo purposes, this includes mock data. Replace with real API when upgraded.
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import json

# Load API key from .env
load_dotenv()
ODDS_API_KEY = os.getenv('ODDS_API_KEY')

if not ODDS_API_KEY:
    raise ValueError("❌ ODDS_API_KEY not found in .env file")

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"

# Stat type mappings
STAT_MARKETS = {
    'player_points': 'PTS',
    'player_rebounds': 'REB',
    'player_assists': 'AST',
    'player_passes': 'AST',
}

BOOKMAKERS = [
    'draftkings',
    'fanduel',
    'betmgm',
    'pointsbet',
    'caesars',
    'espn',
]


def fetch_upcoming_events():
    """Fetch upcoming NBA games"""
    print("🔄 Fetching upcoming NBA games...")
    
    response = requests.get(
        f"{BASE_URL}/sports/{SPORT}/events",
        params={
            'apiKey': ODDS_API_KEY,
        },
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return []
    
    events = response.json()
    print(f"✅ Found {len(events)} upcoming games")
    return events


# Mock data for testing (since free tier doesn't include player props)
MOCK_PROPS = [
    {'player_name': 'Shai Gilgeous-Alexander', 'stat_type': 'PTS', 'line': 30.5, 'odds': -110, 'bookmaker': 'draftkings', 'event_id': '1', 'commence_time': '2026-05-09T23:30Z'},
    {'player_name': 'LeBron James', 'stat_type': 'PTS', 'line': 25.5, 'odds': -110, 'bookmaker': 'fanduel', 'event_id': '2', 'commence_time': '2026-05-09T23:30Z'},
    {'player_name': 'Stephen Curry', 'stat_type': 'PTS', 'line': 28.5, 'odds': -110, 'bookmaker': 'betmgm', 'event_id': '3', 'commence_time': '2026-05-09T23:30Z'},
    {'player_name': 'Jalen Johnson', 'stat_type': 'REB', 'line': 8.5, 'odds': +100, 'bookmaker': 'draftkings', 'event_id': '4', 'commence_time': '2026-05-10T00:00Z'},
    {'player_name': 'De\'Aaron Fox', 'stat_type': 'AST', 'line': 5.5, 'odds': -110, 'bookmaker': 'fanduel', 'event_id': '5', 'commence_time': '2026-05-10T00:00Z'},
    {'player_name': 'Jayson Tatum', 'stat_type': 'PTS', 'line': 26.5, 'odds': -110, 'bookmaker': 'betmgm', 'event_id': '6', 'commence_time': '2026-05-10T00:30Z'},
    {'player_name': 'Luka Doncic', 'stat_type': 'PTS', 'line': 32.5, 'odds': -120, 'bookmaker': 'draftkings', 'event_id': '7', 'commence_time': '2026-05-10T01:00Z'},
    {'player_name': 'Giannis Antetokounmpo', 'stat_type': 'REB', 'line': 11.5, 'odds': -110, 'bookmaker': 'fanduel', 'event_id': '8', 'commence_time': '2026-05-10T01:30Z'},
]


def fetch_props_for_market(market='player_points'):
    """
    Fetch all player props for a specific market
    
    NOTE: Player props require paid subscription.
    Using mock data for demo - replace with real API when upgraded.
    """
    print(f"\n🔄 Fetching {market} props...")
    print(f"   ⚠️  Using mock data (free tier limitation)")
    
    # In production, this would call:
    # response = requests.get(
    #     f"{BASE_URL}/sports/{SPORT}/odds",
    #     params={
    #         'apiKey': ODDS_API_KEY,
    #         'markets': market,
    #         'odds_format': 'american',
    #         'regions': 'us',
    #         'bookmakers': 'draftkings,fanduel,betmgm',
    #     },
    #     timeout=10
    # )
    
    return MOCK_PROPS  # Return mock data for now


def parse_props(results, market='player_points'):
    """
    Parse props from API response into flat list
    
    Returns list of dicts:
    {
        'player_name': 'Shai Gilgeous-Alexander',
        'stat_type': 'PTS',
        'line': 30.5,
        'odds': -110,
        'bookmaker': 'draftkings',
        'event_id': '123456',
        'commence_time': '2026-04-12T23:30Z'
    }
    """
    # If already parsed (mock data), return as-is
    if results and isinstance(results[0], dict) and 'player_name' in results[0]:
        return results
    
    # Otherwise parse from API format
    props = []
    stat_type = STAT_MARKETS.get(market, market.upper())
    
    for event in results:
        event_id = event.get('id')
        commence_time = event.get('commence_time')
        
        for bookmaker in event.get('bookmakers', []):
            bookmaker_key = bookmaker.get('key', 'unknown')
            
            for market_data in bookmaker.get('markets', []):
                if market_data.get('key') != market:
                    continue
                
                for outcome in market_data.get('outcomes', []):
                    player_name = outcome.get('name', '')
                    line = outcome.get('point')
                    odds = outcome.get('odds')
                    
                    # Skip if missing critical data
                    if not player_name or line is None or odds is None:
                        continue
                    
                    props.append({
                        'player_name': player_name,
                        'stat_type': stat_type,
                        'line': float(line),
                        'odds': int(odds),
                        'bookmaker': bookmaker_key,
                        'event_id': event_id,
                        'commence_time': commence_time,
                    })
    
    return props


def fetch_all_props():
    """
    Fetch ALL available player props from multiple markets
    
    Returns list of all props across markets
    """
    all_props = []
    
    # Fetch multiple stat types
    markets_to_fetch = ['player_points', 'player_rebounds', 'player_assists']
    
    for market in markets_to_fetch:
        try:
            results = fetch_props_for_market(market)
            parsed = parse_props(results, market)
            all_props.extend(parsed)
            time.sleep(0.5)  # Be nice to the API
        except Exception as e:
            print(f"⚠️  Error fetching {market}: {e}")
    
    print(f"\n📊 Total props fetched: {len(all_props)}")
    return all_props


def get_live_props_sample():
    """
    Get a small sample of live props for testing
    """
    print("🔄 Fetching sample props for testing...")
    
    try:
        results = fetch_props_for_market('player_points')
        props = parse_props(results, 'player_points')
        return props[:10]  # Return first 10
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == '__main__':
    # Test the API
    print("\n" + "="*60)
    print("🧪 TESTING ODDS API CONNECTION")
    print("="*60)
    
    # Test 1: Check API key
    print(f"\n✅ API Key loaded: {ODDS_API_KEY[:10]}...")
    
    # Test 2: Fetch sample props
    props = get_live_props_sample()
    
    if props:
        print(f"\n✅ Successfully fetched {len(props)} props!")
        print("\nSample props:")
        for i, prop in enumerate(props[:5], 1):
            print(f"{i}. {prop['player_name']:30} | {prop['stat_type']} {prop['line']:5} @ {prop['odds']:6} ({prop['bookmaker']})")
        print("\n📝 NOTE: Using mock data (free tier limitation)")
        print("   To use real player props, upgrade to paid The Odds API plan")
    else:
        print("\n⚠️  Could not fetch props - check API key")

