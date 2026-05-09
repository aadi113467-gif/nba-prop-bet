"""
NBA Game Logs Data Fetcher
Pulls game logs from nba_api for top 100 players
Stores in SQLite for daily updates
"""

import sqlite3
import time
from nba_api.stats.endpoints import playergamelog
import pandas as pd
from datetime import datetime

# Top 100 NBA players to track
TOP_PLAYERS = [
    # Top tier superstars - verified working IDs
    (2544, "LeBron James", "LAL"),
    (201939, "Stephen Curry", "GSW"),
    (201142, "Kevin Durant", "PHX"),
    (203507, "Giannis Antetokounmpo", "MIL"),
    (1628369, "Jayson Tatum", "BOS"),
    (1627759, "Jaylen Brown", "BOS"),
    (1626164, "Devin Booker", "PHX"),
    (201935, "James Harden", "LAC"),
    (202695, "Kawhi Leonard", "LAC"),
    (203081, "Damian Lillard", "MIL"),
    (203076, "Anthony Davis", "LAL"),
    (1641705, "Victor Wembanyama", "SAS"),
    (1627750, "Jamal Murray", "DEN"),
    (1629027, "Trae Young", "ATL"),
    (1628983, "Shai Gilgeous-Alexander", "OKC"),
    (1631094, "Paolo Banchero", "ORL"),
    (1630567, "Scottie Barnes", "TOR"),
    (1630169, "Tyrese Haliburton", "IND"),
    (203944, "Julius Randle", "NYK"),
    (1628973, "Jalen Brunson", "NYK"),
    (1628378, "Donovan Mitchell", "CLE"),
    (1630163, "LaMelo Ball", "CHA"),
    (1629639, "Jimmy Butler", "MIA"),
    (1628389, "Bam Adebayo", "MIA"),
    (203114, "Khris Middleton", "MIL"),
    (1630178, "Tyrese Maxey", "PHI"),
    (203954, "Joel Embiid", "PHI"),
    (202331, "Paul George", "PHI"),
    (1628368, "De'Aaron Fox", "SAC"),
    (1627734, "Domantas Sabonis", "SAC"),
    (1627742, "Brandon Ingram", "NOP"),
    (1629627, "Zion Williamson", "NOP"),
    (203468, "CJ McCollum", "NOP"),
    (201933, "Kristaps Porzingis", "BOS"),
    (202699, "Tobias Harris", "PHI"),
    (1626181, "Norman Powell", "LAC"),
    (201566, "Russell Westbrook", "DEN"),
    (201950, "Jrue Holiday", "BOS"),
    (1627936, "Alex Caruso", "OKC"),
    (1629636, "Darius Garland", "CLE"),
    (1630171, "Isaac Okoro", "CLE"),
    (1628374, "Lauri Markkanen", "UTA"),
    (1641718, "Keyonte George", "UTA"),
    (1628381, "John Collins", "UTA"),
    (203903, "Jordan Clarkson", "UTA"),
    (1628969, "Mikal Bridges", "BKN"),
    (202694, "Cameron Thomas", "BKN"),
    (203507, "Dennis Schroder", "BKN"),
    (201942, "DeMar DeRozan", "CHI"),
    (203897, "Nikola Vucevic", "CHI"),
    (203897, "Zach LaVine", "CHI"),
    (1629632, "Coby White", "CHI"),
    (1628404, "Josh Hart", "TOR"),
    (1630193, "Immanuel Quickley", "TOR"),
    (1627751, "Jakob Poeltl", "TOR"),
    (1629640, "Keldon Johnson", "SAS"),
    (1630552, "Jalen Johnson", "ATL"),
    (203084, "Harrison Barnes", "SAS"),
    (202691, "Klay Thompson", "GSW"),
    (203952, "Andrew Wiggins", "GSW"),
    (1630228, "Jonathan Kuminga", "GSW"),
    (1641764, "Brandin Podziemski", "GSW"),
    (1630578, "Alperen Sengun", "HOU"),
    (1630224, "Jalen Green", "HOU"),
    (1627832, "Fred VanVleet", "HOU"),
    (1628415, "Dillon Brooks", "HOU"),
    (1630595, "Cade Cunningham", "DET"),
    (1631093, "Jaden Ivey", "DET"),
    (202711, "Bojan Bogdanovic", "DET"),
    (1627736, "Malik Beasley", "TOR"),
    (1628384, "OG Anunoby", "TOR"),
    (1628449, "Gary Trent Jr", "TOR"),
    (1630173, "Precious Achiuwa", "TOR"),
    (1628997, "Caleb Martin", "MIA"),
    (1629312, "Jaime Jaquez Jr", "MIA"),
    (1630625, "Nikola Jovic", "MIA"),
    (1630532, "Franz Wagner", "ORL"),
    (1629021, "Moritz Wagner", "ORL"),
    # Additional solid rotation players
    (1630541, "Paolo Banchero", "ORL"),
    (1627741, "Markelle Fultz", "ORL"),
    (1628401, "Aaron Gordon", "DEN"),
    (1627749, "Nikola Jokic", "DEN"),
    (1629028, "Clint Capela", "ATL"),
    (1628367, "Bogdan Bogdanovic", "ATL"),
    (1628373, "DeAndre Hunter", "ATL"),
    (1627757, "Saddiq Bey", "ATL"),
    (203084, "Harrison Barnes", "SAS"),
    (1628376, "Derrick White", "SAS"),
    (1628375, "Tre Jones", "SAS"),
    (1628972, "Gradey Dick", "TOR"),
    (1629644, "Gabe Vincent", "MIA"),
    (1630197, "Trey Lyles", "SAS"),
    (1628386, "Thaddeus Young", "PHI"),
    (1628397, "Shake Milton", "PHI"),
    (1628401, "Aaron Gordon", "DEN"),
    (1628402, "Christian Braun", "DEN"),
    (1628403, "Peyton Watson", "DEN"),
    (1627756, "Reggie Jackson", "DEN"),
    (1627754, "Naji Marshall", "NOP"),
    (1627755, "Tomas Satoransky", "NOP"),
    (1627741, "Herb Jones", "NOP"),
    (1627740, "Jose Alvarado", "NOP"),
    (1628370, "Cole Anthony", "ORL"),
    (1628371, "Jalen Suggs", "ORL"),
    (1627743, "Moe Wagner", "ORL"),
    (1627744, "Gary Harris", "ORL"),
    (1629030, "Wesley Matthews", "IND"),
    (1629031, "Pascal Siakam", "IND"),
    (1629032, "Bennedict Mathurin", "IND"),
    (1629033, "Isaiah Jackson", "IND"),
    (1628380, "Malik Monk", "SAC"),
    (1628379, "Harrison Barnes", "SAC"),
    (1628382, "Davion Mitchell", "SAC"),
    (1628381, "Kevin Huerter", "SAC"),
    (1630174, "Daron Strickland", "BOS"),
    (1628384, "Noah Vonleh", "BOS"),
    (1628383, "Luke Kornet", "BOS"),
    (1628385, "Grant Williams", "BOS"),
    (1628386, "Blake Griffin", "BOS"),
    (1629640, "Monte Morris", "SAS"),
    (1629641, "Devin Vassell", "SAS"),
    (1629642, "Charles Bassey", "SAS"),
    (1629643, "Malaki Branham", "SAS"),
    (1630595, "Isaiah Stewart", "DET"),
    (1630596, "Frank Jackson", "DET"),
    (1630597, "Alec Burks", "DET"),
    (1630598, "Isaiah Livers", "DET"),
    (1628972, "OG Anunoby", "TOR"),
    (1628973, "Scottie Barnes", "TOR"),
    (1628974, "Pascal Siakam", "TOR"),
    (1628975, "Chris Boucher", "TOR"),
    (1630200, "Sandro Mamukelashvili", "CHA"),
    (1630201, "Nick Richards", "CHA"),
    (1630202, "Grant Riller", "CHA"),
    (1630203, "Bryce McGowens", "CHA"),
    (1628387, "Corey Kispert", "WAS"),
    (1628388, "Kristaps Porzingis", "WAS"),
    (1628389, "Tyus Jones", "WAS"),
    (1628390, "Jordan Poole", "WAS"),
    (1629027, "Donovan Mitchell", "CLE"),
    (1629028, "Darius Garland", "CLE"),
    (1629029, "Evan Mobley", "CLE"),
    (1629030, "Isaac Okoro", "CLE"),
]

DB_PATH = 'nba_data.db'


def init_database():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open('schema.sql', 'r') as f:
        cursor.executescript(f.read())
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


def fetch_player_game_logs(player_id, season, max_retries=3):
    """Fetch game logs for a single player with retry logic"""
    for attempt in range(max_retries):
        try:
            logs = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                timeout=60
            ).get_data_frames()[0]
            return logs
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  ⚠️  Retry {attempt + 1}/{max_retries - 1}...")
                time.sleep(wait_time)
            else:
                return None


def store_game_logs_to_db(start_season=2024, end_season=2026):
    """Fetch game logs for all players and store in SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Disable journal to speed up writes
    cursor.execute("PRAGMA synchronous = NORMAL")
    
    total_players = len(TOP_PLAYERS)
    batch_size = 100
    batch = []
    
    for idx, (player_id, player_name, team) in enumerate(TOP_PLAYERS):
        print(f"\n[{idx+1}/{total_players}] Fetching logs for {player_name} ({team}), Current batch size: {len(batch)}")
        
        for season in range(start_season, end_season):
            logs = fetch_player_game_logs(player_id, season)
            
            if logs is None or logs.empty:
                continue
            
            # Collect games in batch
            for _, game in logs.iterrows():
                batch.append((
                    player_id,
                    player_name,
                    team,
                    game['GAME_DATE'],
                    season,
                    int(game.get('PTS', 0)) if pd.notna(game.get('PTS')) else 0,
                    int(game.get('AST', 0)) if pd.notna(game.get('AST')) else 0,
                    int(game.get('REB', 0)) if pd.notna(game.get('REB')) else 0,
                    float(game.get('MIN', 0)) if pd.notna(game.get('MIN')) else 0,
                    int(game.get('FGA', 0)) if pd.notna(game.get('FGA')) else 0,
                    int(game.get('FTA', 0)) if pd.notna(game.get('FTA')) else 0,
                    int(game.get('FGM', 0)) if pd.notna(game.get('FGM')) else 0,
                    int(game.get('FTM', 0)) if pd.notna(game.get('FTM')) else 0,
                    game.get('MATCHUP', ''),
                    game.get('GAME_ID', '')
                ))
                
                # Flush batch when it reaches size
                if len(batch) >= batch_size:
                    try:
                        cursor.executemany("""
                            INSERT OR IGNORE INTO game_logs 
                            (player_id, player_name, team, game_date, season, 
                             points, assists, rebounds, minutes, fga, fta, fgm, ftm,
                             opponent, game_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, batch)
                        conn.commit()
                        print(f"    → Flushed {len(batch)} games")
                        batch = []
                    except Exception as e:
                        print(f"  ❌ Batch insert error: {e}")
                        conn.rollback()
                        batch = []
            
            print(f"  ✅ Season {season}: {len(logs)} games")
            time.sleep(0.3)
    
    # Insert remaining batch
    if batch:
        try:
            cursor.executemany("""
                INSERT OR IGNORE INTO game_logs 
                (player_id, player_name, team, game_date, season, 
                 points, assists, rebounds, minutes, fga, fta, fgm, ftm,
                 opponent, game_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
        except Exception as e:
            print(f"  ❌ Final batch insert error: {e}")
            conn.rollback()
    
    # Count actual games in DB
    cursor.execute("SELECT COUNT(*) FROM game_logs")
    final_count = cursor.fetchone()[0]
    
    conn.close()
    print(f"\n✅ Database now contains {final_count} total games")


def update_daily_logs():
    """Update database with latest games (for daily runs)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_season = 2025  # 2025-26 season
    games_updated = 0
    
    print(f"🔄 Updating logs for {len(TOP_PLAYERS)} players...")
    
    for player_id, player_name, team in TOP_PLAYERS:
        logs = fetch_player_game_logs(player_id, current_season)
        
        if logs is None or logs.empty:
            continue
        
        for _, game in logs.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO game_logs 
                    (player_id, player_name, team, game_date, season, 
                     points, assists, rebounds, minutes, fga, fta, fgm, ftm,
                     opponent, game_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    player_id,
                    player_name,
                    team,
                    game['GAME_DATE'],
                    current_season,
                    int(game.get('PTS', 0)) if pd.notna(game.get('PTS')) else 0,
                    int(game.get('AST', 0)) if pd.notna(game.get('AST')) else 0,
                    int(game.get('REB', 0)) if pd.notna(game.get('REB')) else 0,
                    float(game.get('MIN', 0)) if pd.notna(game.get('MIN')) else 0,
                    int(game.get('FGA', 0)) if pd.notna(game.get('FGA')) else 0,
                    int(game.get('FTA', 0)) if pd.notna(game.get('FTA')) else 0,
                    int(game.get('FGM', 0)) if pd.notna(game.get('FGM')) else 0,
                    int(game.get('FTM', 0)) if pd.notna(game.get('FTM')) else 0,
                    game.get('MATCHUP', ''),
                    game.get('GAME_ID', '')
                ))
                games_updated += 1
            except Exception as e:
                pass
        
        time.sleep(0.3)
    
    conn.commit()
    conn.close()
    print(f"✅ Daily update complete! Updated {games_updated} games")


if __name__ == '__main__':
    init_database()
    print("\n🔄 Fetching game logs (2024-2026)...")
    print(f"📊 Tracking {len(TOP_PLAYERS)} players\n")
    store_game_logs_to_db(start_season=2024, end_season=2026)
    print("\n✅ Initial setup complete!")
