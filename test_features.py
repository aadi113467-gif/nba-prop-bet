"""
Test script for feature engineering and projections
"""

from feature_engineering import (
    generate_player_report,
    get_full_player_features,
    export_features_to_csv,
    compute_season_avg,
    compute_last_n_games
)
from projection_model import generate_projection, print_projection
import sqlite3


def test_db_opponent_data():
    """Check what opponent data we have in the database"""
    print("\n" + "="*70)
    print("TEST 0: Database Opponent Data Check")
    print("="*70)
    
    conn = sqlite3.connect('nba_data.db')
    cursor = conn.cursor()
    
    # Check if opponent column has data
    cursor.execute("SELECT opponent FROM game_logs LIMIT 10")
    samples = cursor.fetchall()
    
    print("\n📊 Sample opponent values from database:")
    for i, (opp,) in enumerate(samples, 1):
        print(f"  {i}. {repr(opp)}")
    
    # Count non-null opponents
    cursor.execute("SELECT COUNT(*) FROM game_logs WHERE opponent IS NOT NULL AND opponent != ''")
    non_null = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM game_logs")
    total = cursor.fetchone()[0]
    
    print(f"\n✅ Non-null opponents: {non_null}/{total} ({100*non_null/total:.1f}%)")
    
    # Show unique opponents
    cursor.execute("SELECT DISTINCT opponent FROM game_logs WHERE opponent IS NOT NULL AND opponent != '' ORDER BY opponent LIMIT 20")
    unique_opps = cursor.fetchall()
    
    print(f"\n🏀 Unique opponents (first 20):")
    for (opp,) in unique_opps:
        print(f"  - {opp}")
    
    conn.close()


def test_single_player():
    """Test features and projection for one player"""
    print("\n" + "="*70)
    print("TEST 1: Single Player Features & Projection")
    print("="*70)
    
    player = "LeBron James"
    season = 2025
    
    # Generate report
    generate_player_report(player, season)
    
    # Get full features
    features = get_full_player_features(
        player,
        season,
        opponent="GSW",
        projected_minutes=35
    )
    
    if features:
        print("Full Features:")
        for key, val in features.items():
            print(f"  {key}: {val}")


def test_projection():
    """Test projection models"""
    print("\n" + "="*70)
    print("TEST 2: Projection Models")
    print("="*70)
    
    players_to_test = [
        ("LeBron James", 24.5, "GSW", 35),
        ("Stephen Curry", 28.5, "LAL", 32),
        ("Jayson Tatum", 27.0, "MIL", 34),
    ]
    
    for player, line, opponent, minutes in players_to_test:
        result = generate_projection(
            player_name=player,
            season=2025,
            line=line,
            opponent=opponent,
            projected_minutes=minutes,
            model='simple'
        )
        print_projection(result)


def test_multiple_opponents():
    """Test same player vs different opponents"""
    print("\n" + "="*70)
    print("TEST 3: Opponent Adjustment Impact")
    print("="*70)
    
    player = "LeBron James"
    season = 2025
    line = 25.0
    
    opponents = ["GSW", "LAL", "BOS", "MIL", None]
    
    print(f"\nTesting {player} at {line} PPG line vs different opponents:")
    for opponent in opponents:
        result = generate_projection(
            player_name=player,
            season=season,
            line=line,
            opponent=opponent,
            projected_minutes=34,
        )
        
        if result:
            opp_label = opponent if opponent else "No Adjustment"
            print(f"  {opp_label:10} → Projection {result['projection']:5.1f} | Edge {result['edge']:+5.2f} | {result['lean']}")


def test_export():
    """Test CSV export"""
    print("\n" + "="*70)
    print("TEST 4: Export All Player Features")
    print("="*70)
    
    df = export_features_to_csv(season=2025, output_file='test_features.csv')
    print(f"\n✅ Sample of exported data (first 10 rows):")
    print(df[['player_name', 'season_avg', 'last10_avg', 'opponent_adjustment']].head(10))


def test_comparison():
    """Compare simple vs advanced models"""
    print("\n" + "="*70)
    print("TEST 5: Model Comparison (Simple vs Advanced)")
    print("="*70)
    
    players = ["LeBron James", "Stephen Curry", "Jayson Tatum", "Nikola Jokic"]
    line = 26.0
    
    print(f"\nComparing models at {line} PPG line:")
    print(f"{'Player':<20} {'Simple':>10} {'Advanced':>10} {'Diff':>8}")
    print("-" * 50)
    
    for player in players:
        result_simple = generate_projection(player, 2025, line, model='simple')
        result_advanced = generate_projection(player, 2025, line, model='advanced')
        
        if result_simple and result_advanced:
            diff = result_advanced['projection'] - result_simple['projection']
            print(f"{player:<20} {result_simple['projection']:>10.2f} {result_advanced['projection']:>10.2f} {diff:>8.2f}")


if __name__ == '__main__':
    test_db_opponent_data()
    test_single_player()
    test_projection()
    test_multiple_opponents()
    test_export()
    test_comparison()
    
    print("\n" + "="*70)
    print("✅ All feature engineering tests complete!")
    print("="*70 + "\n")
