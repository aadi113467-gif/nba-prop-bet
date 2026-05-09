#!/usr/bin/env python3
"""
Quick test to validate database and data fetching
"""

import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'nba_data.db'

def test_database():
    """Test database connectivity and schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_logs'")
        if not cursor.fetchone():
            print("❌ game_logs table not found")
            return False
        
        print("✅ game_logs table exists")
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM game_logs")
        count = cursor.fetchone()[0]
        print(f"✅ Total records: {count}")
        
        # Show recent games
        cursor.execute("""
            SELECT player_name, team, game_date, points, minutes 
            FROM game_logs 
            ORDER BY game_date DESC 
            LIMIT 5
        """)
        
        print("\n📋 Latest 5 games:")
        for row in cursor.fetchall():
            print(f"   {row[0]:20} {row[1]:3} {row[2]} {row[3]:2} pts {row[4]:5} min")
        
        # Show unique players
        cursor.execute("SELECT COUNT(DISTINCT player_id) FROM game_logs")
        unique_players = cursor.fetchone()[0]
        print(f"\n✅ Unique players tracked: {unique_players}")
        
        # Show seasons covered
        cursor.execute("SELECT DISTINCT season FROM game_logs ORDER BY season")
        seasons = [row[0] for row in cursor.fetchall()]
        print(f"✅ Seasons available: {seasons}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == '__main__':
    print(f"Testing NBA Prop Bot Database")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    success = test_database()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed. Run 'python fetch_game_logs.py' first to initialize.")
