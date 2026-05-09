#!/usr/bin/env python3
"""
Daily Bet Generation Pipeline
Fetches live props from The Odds API
Generates bet signals for all props
Outputs actionable bets to CSV
"""

import csv
import sqlite3
from datetime import datetime
from odds_fetcher import fetch_all_props
from bet_signals import generate_bet_signal
from projection_model import get_latest_season
from feature_engineering import normalize_player_name

OUTPUT_DIR = 'daily_bets'
import os
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_all_players_in_db(season):
    """Get list of all players in database"""
    conn = sqlite3.connect('nba_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name FROM game_logs WHERE season = ?", (season,))
    players = [row[0] for row in cursor.fetchall()]
    conn.close()
    return players


def match_player_to_db(player_name, season):
    """
    Try to match prop player name to database player name
    Returns normalized name or None if not found
    """
    # Try exact match first
    normalized = normalize_player_name(player_name)
    if normalized:
        return normalized
    
    # If normalize fails, return None
    return None


def generate_daily_bets(max_props=None):
    """
    Main pipeline:
    1. Fetch props from API
    2. Match to players in database
    3. Generate signals for all
    4. Output bets to CSV
    """
    
    print("\n" + "="*80)
    print("🎯 DAILY BET GENERATION PIPELINE")
    print("="*80)
    
    season = get_latest_season()
    print(f"\n📅 Season: {season}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Step 1: Fetch props
    print("\n[1/4] Fetching props from The Odds API...")
    props = fetch_all_props()
    
    if not props:
        print("❌ No props found!")
        return
    
    print(f"✅ Found {len(props)} total props")
    
    if max_props:
        props = props[:max_props]
        print(f"⚠️  Limiting to {max_props} for testing")
    
    # Step 2: Match players and generate signals
    print(f"\n[2/4] Matching players and generating signals...")
    
    matched_bets = []
    skipped_players = set()
    
    for i, prop in enumerate(props, 1):
        player_api = prop['player_name']
        stat_type = prop['stat_type']
        line = prop['line']
        odds = prop['odds']
        bookmaker = prop['bookmaker']
        
        # Try to match to database
        player_db = match_player_to_db(player_api, season)
        
        if not player_db:
            skipped_players.add(player_api)
            continue
        
        # Generate bet signal
        try:
            signal = generate_bet_signal(
                player_name=player_db,
                stat_type=stat_type,
                line=line,
                american_odds=odds,
                bet_type='OVER',  # Default to OVER (can be enhanced)
                opponent='',
                season=season
            )
            
            # Add metadata
            signal['player_api_name'] = player_api
            signal['bookmaker'] = bookmaker
            signal['commence_time'] = prop.get('commence_time', '')
            signal['event_id'] = prop.get('event_id', '')
            
            matched_bets.append(signal)
            
            if i % 20 == 0:
                print(f"  ✓ Processed {i}/{len(props)} props...")
        
        except Exception as e:
            print(f"  ⚠️  Error processing {player_db} {stat_type}: {e}")
    
    print(f"✅ Generated signals for {len(matched_bets)} props")
    print(f"⚠️  Skipped {len(skipped_players)} players not in database")
    
    if skipped_players and len(skipped_players) <= 20:
        print(f"   Skipped players: {', '.join(list(skipped_players)[:10])}")
    
    # Step 3: Filter to actionable bets
    print(f"\n[3/4] Filtering to actionable bets...")
    
    actionable_bets = [
        b for b in matched_bets 
        if b.get('signal') == 'BET' and b.get('ev_percentage', 0) > 3.0
    ]
    
    print(f"✅ Found {len(actionable_bets)} actionable bets (EV > 3%)")
    
    # Sort by EV descending
    actionable_bets.sort(key=lambda x: x.get('ev_percentage', 0), reverse=True)
    
    # Step 4: Output to CSV
    print(f"\n[4/4] Outputting results to CSV...")
    
    timestamp = datetime.now().strftime('%Y-%m-%d')
    csv_file = f"{OUTPUT_DIR}/bets_{timestamp}.csv"
    
    if actionable_bets:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'player_name',
                'stat_type',
                'line',
                'projection',
                'edge',
                'odds',
                'probability',
                'ev_percentage',
                'signal',
                'bookmaker',
                'season_avg',
                'last_10_avg',
            ])
            writer.writeheader()
            
            for bet in actionable_bets:
                writer.writerow({
                    'player_name': bet.get('player_name', ''),
                    'stat_type': bet.get('stat_type', ''),
                    'line': bet.get('line', ''),
                    'projection': round(bet.get('projection', 0), 2),
                    'edge': round(bet.get('edge', 0), 2),
                    'odds': bet.get('odds', ''),
                    'probability': round(bet.get('probability', 0), 4),
                    'ev_percentage': round(bet.get('ev_percentage', 0), 2),
                    'signal': bet.get('signal', ''),
                    'bookmaker': bet.get('bookmaker', ''),
                    'season_avg': round(bet.get('season_avg', 0), 2),
                    'last_10_avg': round(bet.get('last_10_avg', 0), 2),
                })
        
        print(f"✅ Saved to: {csv_file}")
    else:
        print(f"⚠️  No actionable bets found (EV > 3%)")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Total props fetched:        {len(props)}")
    print(f"Matched to database:        {len(matched_bets)}")
    print(f"Actionable bets (EV > 3%):  {len(actionable_bets)}")
    
    if actionable_bets:
        avg_ev = sum(b.get('ev_percentage', 0) for b in actionable_bets) / len(actionable_bets)
        print(f"Average EV:                 {avg_ev:.2f}%")
        print(f"\n🎯 Top 3 Bets:")
        for i, bet in enumerate(actionable_bets[:3], 1):
            print(f"   {i}. {bet['player_name']:25} {bet['stat_type']} {bet['line']:.1f} @ {bet['odds']:6} | EV: {bet['ev_percentage']:6.2f}%")
    
    print(f"\n✅ Completed at {datetime.now().isoformat()}\n")
    
    return actionable_bets


if __name__ == '__main__':
    # Run the pipeline
    actionable_bets = generate_daily_bets(max_props=50)  # Test with 50 props
