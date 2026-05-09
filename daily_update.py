#!/usr/bin/env python3
"""
Daily update script
Run this daily via cron to keep game logs fresh
"""

import sys
import sqlite3
from fetch_game_logs import update_daily_logs
from datetime import datetime

def main():
    print(f"\n{'='*50}")
    print(f"NBA Game Logs Daily Update")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*50}\n")
    
    # Update daily
    update_daily_logs()
    
    # Show last update stats
    conn = sqlite3.connect('nba_data.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM game_logs")
    total_games = cursor.fetchone()[0]
    
    # Get ALL game dates and find the latest chronologically
    cursor.execute("SELECT DISTINCT game_date FROM game_logs")
    all_dates = cursor.fetchall()
    
    # Parse dates properly to find latest
    from datetime import datetime as dt
    latest_date = None
    date_format = "%b %d, %Y"  # "Apr 09, 2026"
    
    for (date_str,) in all_dates:
        try:
            parsed_date = dt.strptime(date_str, date_format)
            if latest_date is None or parsed_date > latest_date:
                latest_date = parsed_date
        except:
            pass
    
    conn.close()
    
    print(f"\n📊 Database Stats:")
    print(f"   Total games stored: {total_games}")
    if latest_date:
        print(f"   Latest game date: {latest_date.strftime('%B %d, %Y')}")
        days_old = (datetime.now() - latest_date).days
        print(f"   Data is {days_old} days old")
    else:
        print(f"   Latest game date: Unknown")
    print(f"\n✅ Update finished at {datetime.now().isoformat()}\n")


if __name__ == '__main__':
    main()
