#!/usr/bin/env python3
"""
Projection Model with Multi-Stat Support

Step 3: Generate projections for any NBA stat type
- Points (PTS)
- Assists (AST)
- Rebounds (REB)
- Blocks (BLK)
- Steals (STL)
- Combo stats: PRA (Points + Rebounds + Assists), PA, PR, AR, RA

Each stat type has its own standard deviation for accurate z-score calculations
"""

from feature_engineering import (
    get_full_player_features,
    compute_season_avg_for_stat,
    compute_last_n_games_for_stat,
    normalize_player_name
)


# Standard deviations by stat type (calibrated from historical data)
STD_DEVS = {
    'PTS': 5.5,      # Points have highest variance
    'AST': 2.2,      # Assists have lower variance
    'REB': 2.8,      # Rebounds have medium-low variance
    'BLK': 1.1,      # Blocks have very low variance
    'STL': 0.9,      # Steals have very low variance
    'PRA': 8.0,      # PTS+REB+AST combo (highest variance)
    'PA': 6.5,       # PTS+AST combo
    'PR': 7.0,       # PTS+REB combo
    'AR': 3.5,       # AST+REB combo
    'RA': 3.5,       # REB+AST combo (same as AR)
}


def simple_weighted_projection(season_avg, last10_avg, last5_avg):
    """
    Simple projection: 50% season avg, 30% last 10, 20% last 5
    Weights toward more recent games
    Works for any stat type
    """
    projection = (0.50 * season_avg) + (0.30 * last10_avg) + (0.20 * last5_avg)
    return round(projection, 2)


def advanced_weighted_projection(season_avg, last10_avg, last5_avg, last3_avg):
    """
    Advanced projection: 40% season, 35% last10, 15% last5, 10% last3
    More weight on recent performance
    Works for any stat type
    """
    projection = (0.40 * season_avg) + (0.35 * last10_avg) + (0.15 * last5_avg) + (0.10 * last3_avg)
    return round(projection, 2)


def compute_z_score(projection, line, stat_type='PTS'):
    """
    Compute z-score for the projection vs line
    
    Uses stat-type specific standard deviation for accurate lean calculation
    
    Z-score = (Projection - Line) / Std Dev
    Tells us how many standard deviations the projection is from the line
    
    Positive z-score = OVER lean (projection above line)
    Negative z-score = UNDER lean (projection below line)
    """
    std_dev = STD_DEVS.get(stat_type, 5.5)  # Default to PTS std dev if unknown
    z_score = (projection - line) / std_dev
    return round(z_score, 2)


def determine_lean(z_score, threshold=0.5):
    """
    Determine OVER/UNDER lean based on z-score
    
    |z_score| > threshold = Strong lean
    |z_score| <= threshold = Neutral
    """
    if z_score > threshold:
        return "OVER"
    elif z_score < -threshold:
        return "UNDER"
    else:
        return "NEUTRAL"


def generate_projection(
    player_name,
    season,
    line,
    stat_type='PTS',
    opponent=None,
    model='simple'
):
    """
    Generate projection for a player stat with line
    
    Parameters:
    -----------
    player_name : str
        Player name (case insensitive)
    season : int
        NBA season (2025 for 2025-26)
    line : float
        Sportsbook line to project against
    stat_type : str
        Type of stat: PTS, AST, REB, BLK, STL, PRA, PA, PR, AR, RA
        Default: 'PTS' (Points)
    opponent : str, optional
        Opponent code for matchup adjustment (e.g., 'GSW')
    model : str
        'simple' or 'advanced' projection model
        Default: 'simple' (50/30/20 weights)
    
    Returns:
    --------
    dict with projection, edge, lean, z-score, and features
    Returns None if player not found
    """
    
    # Get player features for this stat type
    features = get_full_player_features(player_name, season, stat_type=stat_type)
    
    if features is None:
        return None
    
    season_avg = features['season_avg']
    last10_avg = features['last10_avg']
    last5_avg = features['last5_avg']
    
    # Generate projection based on model
    if model == 'advanced':
        last3_avg = features['last3_avg']
        projection = advanced_weighted_projection(season_avg, last10_avg, last5_avg, last3_avg)
    else:
        projection = simple_weighted_projection(season_avg, last10_avg, last5_avg)
    
    # Calculate edge (difference from line)
    edge = projection - line
    
    # Calculate z-score and determine lean
    z_score = compute_z_score(projection, line, stat_type=stat_type)
    lean = determine_lean(z_score, threshold=0.5)
    
    return {
        'projection': projection,
        'line': line,
        'edge': edge,
        'z_score': z_score,
        'lean': lean,
        'season_avg': season_avg,
        'last10_avg': last10_avg,
        'last5_avg': last5_avg,
        'games_played': features['games_played']
    }


def generate_all_projections(
    season,
    stat_type='PTS',
    custom_lines=None,
    custom_opponents=None,
    model='simple'
):
    """
    Generate projections for ALL players in season
    
    Parameters:
    -----------
    season : int
        NBA season
    stat_type : str
        Type of stat to project (default: 'PTS')
    custom_lines : dict, optional
        Custom lines for specific players {player_name: line}
    custom_opponents : dict, optional
        Custom opponents for specific players {player_name: opponent}
    model : str
        'simple' or 'advanced' projection model
    
    Returns:
    --------
    List of dicts, one per player with projection data
    """
    import sqlite3
    
    conn = sqlite3.connect('/Users/aadishah/nba-prop-bet/nba_data.db')
    cursor = conn.cursor()
    
    # Get distinct players
    cursor.execute('''
        SELECT DISTINCT player_name
        FROM game_logs
        WHERE season = ?
        ORDER BY player_name
    ''', (season,))
    
    players = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    projections = []
    for player in players:
        # Use custom line if provided, otherwise use season average
        if custom_lines and player in custom_lines:
            line = custom_lines[player]
        else:
            # Use season average as default line
            avg = compute_season_avg_for_stat(player, season, stat_type)
            if avg is None:
                continue
            line = avg
        
        # Get custom opponent if provided
        opponent = custom_opponents.get(player) if custom_opponents else None
        
        # Generate projection
        proj = generate_projection(player, season, line, stat_type, opponent, model)
        if proj is not None:
            projections.append({
                'player': player,
                'line': line,
                **proj
            })
    
    # Sort by edge (biggest OVER edge first)
    projections.sort(key=lambda x: x['edge'], reverse=True)
    
    return projections


def get_latest_season():
    """Get most recent season in database"""
    import sqlite3
    
    conn = sqlite3.connect('/Users/aadishah/nba-prop-bet/nba_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(season) FROM game_logs')
    season = cursor.fetchone()[0]
    conn.close()
    
    return season if season else 2025


def interactive_test():
    """Interactive mode to test projections for any player and stat type"""
    from feature_engineering import get_all_players, normalize_player_name
    
    season = get_latest_season()
    
    print(f"\n{'='*70}")
    print(f"🏀 INTERACTIVE PROJECTION TESTER")
    print(f"{'='*70}")
    print(f"Season: {season}\n")
    print(f"Available stats: PTS, AST, REB, PRA, PA, PR, AR\n")
    
    all_players = get_all_players(season)
    
    while True:
        try:
            # STEP 1: Get and validate player name
            player_input = input("Enter player name (or 'quit' to exit): ").strip()
            if player_input.lower() == 'quit':
                break
            
            # Check if player exists (case-insensitive)
            player = normalize_player_name(player_input)
            if player is None:
                print(f"❌ Player '{player_input}' not found")
                # Show similar names
                similar = [p for p in all_players if player_input.lower() in p.lower()]
                if similar:
                    print(f"   Did you mean? {', '.join(similar[:5])}")
                else:
                    print(f"   Available: {', '.join(all_players[:10])}...")
                print()
                continue
            
            print(f"✅ Found: {player}\n")
            
            # STEP 2: Get stat type
            stat_type = input("Enter stat type (PTS/AST/REB/PRA/PA/PR/AR): ").strip().upper()
            if not stat_type:
                stat_type = 'PTS'
            if stat_type not in ['PTS', 'AST', 'REB', 'PRA', 'PA', 'PR', 'AR']:
                print(f"❌ Invalid stat type. Use: PTS, AST, REB, PRA, PA, PR, AR\n")
                continue
            
            # STEP 3: Get line
            line = float(input("Enter line (or press Enter for season average): ").strip() or '0')
            
            # If no line provided, use season average
            if line == 0:
                line = compute_season_avg_for_stat(player, season, stat_type)
                if line is None:
                    print(f"❌ Could not compute season average\n")
                    continue
                print(f"   (Using season average: {line:.2f})")
            
            # STEP 4: Get opponent (optional)
            opponent = input("Enter opponent (optional, press Enter for none): ").strip() or None
            
            # Generate projection
            projection_data = generate_projection(
                player_name=player,
                season=season,
                line=line,
                stat_type=stat_type,
                opponent=opponent,
                model='simple'
            )
            
            if projection_data is None:
                print(f"❌ Could not generate projection\n")
                continue
            
            # Print results
            print(f"\n{'='*70}")
            print(f"📊 PROJECTION FOR {player.upper()}")
            print(f"{'='*70}")
            print(f"Stat Type:         {stat_type}")
            print(f"Line:              {projection_data['line']:.1f} {stat_type}")
            print(f"Projection:        {projection_data['projection']:.2f} {stat_type}")
            print(f"Edge:              {projection_data['edge']:+.2f} {stat_type}")
            print(f"Lean:              {projection_data['lean']}")
            print(f"Z-Score:           {projection_data['z_score']:.2f}σ")
            print(f"\nSeason Stats:")
            print(f"  Season Avg:      {projection_data['season_avg']:.2f} {stat_type}")
            print(f"  Last 10 Avg:     {projection_data['last10_avg']:.2f} {stat_type}")
            print(f"  Last 5 Avg:      {projection_data['last5_avg']:.2f} {stat_type}")
            print(f"  Games Played:    {projection_data['games_played']}")
            print(f"{'='*70}\n")
        
        except ValueError as e:
            print(f"❌ Invalid input: {e}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
            print(f"Line:              {projection_data['line']:.1f} {stat_type}")
            print(f"Projection:        {projection_data['projection']:.2f} {stat_type}")
            print(f"Edge:              {projection_data['edge']:+.2f} {stat_type}")
            print(f"Lean:              {projection_data['lean']}")
            print(f"Z-Score:           {projection_data['z_score']:.2f}σ")
            print(f"\nSeason Stats:")
            print(f"  Season Avg:      {projection_data['season_avg']:.2f} {stat_type}")
            print(f"  Last 10 Avg:     {projection_data['last10_avg']:.2f} {stat_type}")
            print(f"  Last 5 Avg:      {projection_data['last5_avg']:.2f} {stat_type}")
            print(f"  Games Played:    {projection_data['games_played']}")
            print(f"{'='*70}\n")
        
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")


def test_projections():
    """Run comprehensive tests for multi-stat projections"""
    
    season = get_latest_season()
    print(f"\n{'='*80}")
    print(f"🧪 MULTI-STAT PROJECTION TESTS")
    print(f"{'='*80}")
    print(f"Season: {season}\n")
    
    # TEST 1: Shai for all stat types
    print(f"\n{'='*70}")
    print(f"TEST 1: Shai Gilgeous-Alexander - All Stat Types")
    print(f"{'='*70}\n")
    
    shai_tests = ['PTS', 'AST', 'REB', 'PRA']  # Only stats in database
    for stat in shai_tests:
        proj = generate_projection('Shai Gilgeous-Alexander', season, 50.5, stat_type=stat)
        if proj:
            print(f"{stat:6} | Line: {proj['line']:6.1f} | Proj: {proj['projection']:6.2f} | "
                  f"Edge: {proj['edge']:+6.2f} | Z-Score: {proj['z_score']:+5.2f}σ | Lean: {proj['lean']:<8}")
        else:
            print(f"{stat:6} | NOT FOUND")
    
    # TEST 2: Different players for PTS
    print(f"\n{'='*70}")
    print(f"TEST 2: Multiple Players - Points (PTS)")
    print(f"{'='*70}\n")
    
    players = ['LeBron James', 'Stephen Curry', 'Jalen Johnson']
    for player in players:
        proj = generate_projection(player, season, 25.5, stat_type='PTS')
        if proj:
            print(f"{player:<25} | Proj: {proj['projection']:6.2f} | Edge: {proj['edge']:+6.2f} | "
                  f"Lean: {proj['lean']:<8}")
        else:
            print(f"{player:<25} | NOT FOUND")
    
    # TEST 3: Different players for AST
    print(f"\n{'='*70}")
    print(f"TEST 3: Multiple Players - Assists (AST)")
    print(f"{'='*70}\n")
    
    for player in players:
        proj = generate_projection(player, season, 5.5, stat_type='AST')
        if proj:
            print(f"{player:<25} | Proj: {proj['projection']:6.2f} | Edge: {proj['edge']:+6.2f} | "
                  f"Lean: {proj['lean']:<8}")
        else:
            print(f"{player:<25} | NOT FOUND")
    
    # TEST 4: Combo stat - PRA
    print(f"\n{'='*70}")
    print(f"TEST 4: Multiple Players - Combo (PRA = PTS + REB + AST)")
    print(f"{'='*70}\n")
    
    for player in players:
        proj = generate_projection(player, season, 50.5, stat_type='PRA')
        if proj:
            print(f"{player:<25} | Proj: {proj['projection']:6.2f} | Edge: {proj['edge']:+6.2f} | "
                  f"Lean: {proj['lean']:<8}")
        else:
            print(f"{player:<25} | NOT FOUND")
    
    # TEST 5: Rebounds with line variations
    print(f"\n{'='*70}")
    print(f"TEST 5: Multiple Players - Rebounds (REB) with Different Lines")
    print(f"{'='*70}\n")
    
    for player in players:
        for line in [5.5, 7.5, 9.5]:
            proj = generate_projection(player, season, line, stat_type='REB')
            if proj:
                print(f"  {player:<23} REB {line:4.1f} | Proj: {proj['projection']:5.2f} | Lean: {proj['lean']:<8}")
    
    print(f"\n{'='*80}")
    print(f"✅ All tests complete!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_test()
    else:
        test_projections()
