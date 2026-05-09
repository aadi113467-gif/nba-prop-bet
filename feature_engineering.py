"""
Feature Engineering Layer
Computes season averages, last 10 games, opponent adjustments, etc.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = 'nba_data.db'


def get_all_players(season):
    """Get all distinct players in a season"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name FROM game_logs WHERE season = ? ORDER BY player_name", (season,))
    players = [row[0] for row in cursor.fetchall()]
    conn.close()
    return players


def normalize_player_name(player_name):
    """
    Convert player name to exact match from database
    Handles case-insensitive lookup and partial name matching
    Returns None if not found, otherwise returns exact name from database
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Try exact match first
    cursor.execute("SELECT player_name FROM game_logs WHERE player_name = ? LIMIT 1", (player_name,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]
    
    # Try case-insensitive exact match
    cursor.execute("SELECT DISTINCT player_name FROM game_logs WHERE LOWER(player_name) = LOWER(?) LIMIT 1", (player_name,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]
    
    # Try partial match (for shortened names like "shai" → "Shai Gilgeous-Alexander")
    cursor.execute("SELECT DISTINCT player_name FROM game_logs WHERE LOWER(player_name) LIKE LOWER(?) LIMIT 1", (f'%{player_name}%',))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]
    
    conn.close()
    return None


def get_player_games(player_name, season, limit=None):
    """Fetch all games for a player in a season, ordered by date"""
    # Normalize the player name (case-insensitive lookup)
    player_name = normalize_player_name(player_name)
    
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT * FROM game_logs 
        WHERE player_name = ? AND season = ?
        ORDER BY game_date ASC
    """
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn, params=(player_name, season))
    conn.close()
    return df


def compute_season_avg(player_name, season):
    """Compute season average points"""
    games = get_player_games(player_name, season)
    
    if games.empty:
        return {
            'season_avg': 0,
            'games_played': 0,
            'total_points': 0,
            'avg_minutes': 0
        }
    
    season_avg = games['points'].mean()
    games_played = len(games)
    
    return {
        'season_avg': round(season_avg, 2),
        'games_played': games_played,
        'total_points': games['points'].sum(),
        'avg_minutes': round(games['minutes'].mean(), 1)
    }


def compute_last_n_games(player_name, season, n=10):
    """Compute average stats for last N games"""
    games = get_player_games(player_name, season)
    
    if games.empty:
        return None
    
    # Get last N games
    last_n = games.tail(n)
    
    if last_n.empty:
        return None
    
    return {
        f'last{n}_avg': round(last_n['points'].mean(), 2),
        f'last{n}_games': len(last_n),
        f'last{n}_min_avg': round(last_n['minutes'].mean(), 1),
        f'last{n}_usage_proxy': round(
            (last_n['fga'].sum() + last_n['fta'].sum() + 0.44 * last_n['fta'].sum()) / len(last_n), 2
        )
    }


def extract_opponent(matchup_str):
    """Extract opponent from MATCHUP string (e.g., 'LAL vs GSW' -> 'GSW')"""
    if pd.isna(matchup_str):
        return None
    
    parts = str(matchup_str).split()
    if len(parts) >= 3:
        # Format: "TEAM vs OPPONENT" or "TEAM @ OPPONENT"
        return parts[2]
    return None


def compute_opponent_adjustment(player_name, season, opponent=None):
    """
    Compute adjustment based on opponent defense
    Returns opponent's average points allowed per game to similar players
    
    Opponent format in DB is "TEAM @ OPPONENT" or "TEAM vs. OPPONENT"
    We extract just the opponent team code (last token)
    """
    games = get_player_games(player_name, season)
    
    if games.empty:
        return 0
    
    # If specific opponent provided, filter to those games only
    if opponent:
        # Extract opponent code from matchup strings
        # "LAL @ GSW" -> opponent is "GSW"
        # "BOS vs. LAL" -> opponent is "LAL"
        def extract_opp_code(matchup):
            if pd.isna(matchup):
                return None
            parts = str(matchup).split()
            if len(parts) >= 3:
                return parts[-1]  # Last token is opponent
            return None
        
        games['opp_code'] = games['opponent'].apply(extract_opp_code)
        opponent_games = games[games['opp_code'] == opponent]
        
        if opponent_games.empty:
            return 0
        
        opp_avg = opponent_games['points'].mean()
    else:
        # Use season average as baseline (no adjustment)
        opp_avg = games['points'].mean()
    
    season_avg = games['points'].mean()
    adjustment = opp_avg - season_avg
    
    return round(adjustment, 2)


def compute_minutes_projection(player_name, season, projected_minutes=None):
    """
    Compute minutes-adjusted projection
    If projected_minutes not provided, uses season average
    """
    games = get_player_games(player_name, season)
    
    if games.empty:
        return 1.0
    
    avg_minutes = games['minutes'].mean()
    
    if projected_minutes is None:
        return 1.0
    
    if avg_minutes == 0:
        return 1.0
    
    multiplier = projected_minutes / avg_minutes
    return round(multiplier, 2)


def get_stat_column(stat_type):
    """
    Map stat type to database column(s)
    
    Supported stat types:
    - PTS: Points
    - AST: Assists
    - REB: Rebounds
    - BLK: Blocks (NOTE: Not in database, estimated)
    - STL: Steals (NOTE: Not in database, estimated)
    - PRA: Points + Rebounds + Assists
    - PA: Points + Assists
    - PR: Points + Rebounds
    - AR: Assists + Rebounds
    - RA: Rebounds + Assists
    """
    stat_type = stat_type.upper()
    
    # Database has: points, assists, rebounds
    # Note: blocks and steals not available in database
    column_map = {
        'PTS': 'points',
        'AST': 'assists',
        'REB': 'rebounds',
        'BLK': 'blocks',      # Not in DB, will use 0
        'STL': 'steals',      # Not in DB, will use 0
    }
    
    # Combo stats
    combo_stats = ['PRA', 'PA', 'PR', 'AR', 'RA']
    
    if stat_type in column_map:
        return column_map[stat_type], [stat_type]
    elif stat_type in combo_stats:
        return stat_type, stat_type.list()  # Will be computed separately
    else:
        return 'points', ['PTS']  # Default to points


def compute_stat_value(games, stat_type):
    """
    Calculate the stat value for all games
    Handles both single stats and combos (PRA, PA, etc.)
    
    Note: BLK and STL not in database, defaults to 0
    """
    stat_type = stat_type.upper()
    
    if stat_type == 'PTS':
        return games['points']
    elif stat_type == 'AST':
        return games['assists']
    elif stat_type == 'REB':
        return games['rebounds']
    elif stat_type == 'BLK':
        # Blocks not in database, return 0 (or we could estimate from other stats)
        return 0
    elif stat_type == 'STL':
        # Steals not in database, return 0 (or we could estimate from other stats)
        return 0
    elif stat_type == 'PRA':
        return games['points'] + games['rebounds'] + games['assists']
    elif stat_type == 'PA':
        return games['points'] + games['assists']
    elif stat_type == 'PR':
        return games['points'] + games['rebounds']
    elif stat_type == 'AR':
        return games['assists'] + games['rebounds']
    elif stat_type == 'RA':
        return games['rebounds'] + games['assists']
    else:
        return games['points']  # Default


def compute_season_avg_for_stat(player_name, season, stat_type='PTS'):
    """Compute season average for any stat type"""
    games = get_player_games(player_name, season)
    
    if games.empty:
        return {
            'season_avg': 0,
            'games_played': 0,
            'total_stat': 0,
            'avg_minutes': 0
        }
    
    stat_values = compute_stat_value(games, stat_type)
    season_avg = stat_values.mean()
    games_played = len(games)
    
    return {
        'season_avg': round(season_avg, 2),
        'games_played': games_played,
        'total_stat': stat_values.sum(),
        'avg_minutes': round(games['minutes'].mean(), 1)
    }


def compute_last_n_games_for_stat(player_name, season, n=10, stat_type='PTS'):
    """Compute average stats for last N games for any stat type"""
    games = get_player_games(player_name, season)
    
    if games.empty:
        return None
    
    # Get last N games
    last_n = games.tail(n)
    stat_values = compute_stat_value(last_n, stat_type)
    
    return {
        f'last{n}_avg': round(stat_values.mean(), 2),
        f'last{n}_games': len(last_n),
    }


def get_full_player_features(player_name, season, stat_type='PTS', game_date=None, opponent=None, projected_minutes=None):
    """
    Comprehensive feature computation for a player for ANY stat type
    Returns dict with all features needed for projection
    
    Args:
        player_name: Player name
        season: NBA season
        stat_type: 'PTS', 'AST', 'REB', 'BLK', 'STL', 'PRA', 'PA', 'PR', etc.
        game_date: Optional game date
        opponent: Optional opponent code
        projected_minutes: Optional projected minutes
    """
    
    season_stats = compute_season_avg_for_stat(player_name, season, stat_type)
    last10_stats = compute_last_n_games_for_stat(player_name, season, n=10, stat_type=stat_type)
    last5_stats = compute_last_n_games_for_stat(player_name, season, n=5, stat_type=stat_type)
    
    if season_stats['games_played'] == 0:
        return None
    
    opp_adj = compute_opponent_adjustment(player_name, season, opponent)
    minutes_multiplier = compute_minutes_projection(player_name, season, projected_minutes)
    
    features = {
        'player_name': player_name,
        'season': season,
        'stat_type': stat_type,
        'game_date': game_date,
        'opponent': opponent,
        
        # Season stats
        'season_avg': season_stats['season_avg'],
        'games_played': season_stats['games_played'],
        'avg_minutes': season_stats['avg_minutes'],
        
        # Last 10 games
        'last10_avg': last10_stats['last10_avg'] if last10_stats else season_stats['season_avg'],
        'last10_games': last10_stats['last10_games'] if last10_stats else 0,
        
        # Last 5 games
        'last5_avg': last5_stats['last5_avg'] if last5_stats else season_stats['season_avg'],
        'last5_games': last5_stats['last5_games'] if last5_stats else 0,
        
        # Opponent & minutes
        'opponent_adjustment': opp_adj,
        'opponent_adjusted_avg': round(season_stats['season_avg'] + opp_adj, 2),
        'projected_minutes': projected_minutes,
        'minutes_multiplier': minutes_multiplier,
    }
    
    return features


def generate_player_report(player_name, season):
    """Generate a detailed report for a player"""
    features = get_full_player_features(player_name, season)
    
    if features is None:
        print(f"❌ No data for {player_name}")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 {player_name.upper()} - {season} Season Report")
    print(f"{'='*60}")
    print(f"Games Played: {features['games_played']}")
    print(f"Avg Minutes: {features['avg_minutes']}")
    print(f"\n📈 Scoring Averages:")
    print(f"  Season Avg:            {features['season_avg']} PPG")
    print(f"  Last 10 Avg:           {features['last10_avg']} PPG")
    print(f"  Last 5 Avg:            {features['last5_avg']} PPG")
    print(f"\n🛡️  Opponent Adjustment: {features['opponent_adjustment']:+.2f}")
    print(f"  Opponent-Adjusted Avg: {features['opponent_adjusted_avg']} PPG")
    print(f"{'='*60}\n")


def export_features_to_csv(season=2026, output_file='player_features.csv'):
    """Export features for all players to CSV"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get unique players
    cursor.execute("SELECT DISTINCT player_name FROM game_logs WHERE season = ? ORDER BY player_name", (season,))
    players = cursor.fetchall()
    conn.close()
    
    features_list = []
    
    for (player_name,) in players:
        features = get_full_player_features(player_name, season)
        if features:
            features_list.append(features)
    
    df = pd.DataFrame(features_list)
    df.to_csv(output_file, index=False)
    print(f"✅ Exported {len(features_list)} players to {output_file}")
    return df


if __name__ == '__main__':
    # Example: Generate report for LeBron James
    generate_player_report("LeBron James", 2025)
    
    # Example: Get full features
    features = get_full_player_features(
        "LeBron James", 
        season=2025,
        opponent="GSW",
        projected_minutes=35
    )
    print("\n📋 Full Features:")
    for key, val in features.items():
        print(f"  {key}: {val}")
    
    # Export all player features
    print("\n🔄 Exporting features for all players...")
    export_features_to_csv(season=2025)