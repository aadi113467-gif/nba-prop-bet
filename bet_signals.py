#!/usr/bin/env python3
"""
Bet Signal Generator
Converts projections + odds into actionable BET/NO BET signals

Step 4A: Expected Value (EV) Calculation
Step 4B: Bet Signal Logic
"""

from projection_model import generate_projection, get_latest_season


def american_odds_to_implied_prob(american_odds):
    """
    Convert American odds to implied probability
    
    Positive odds: +110 means you win $110 on $100 bet
        Prob = 100 / (100 + odds)
    
    Negative odds: -110 means you bet $110 to win $100
        Prob = abs(odds) / (abs(odds) + 100)
    """
    if american_odds > 0:
        # Positive odds
        implied_prob = 100 / (100 + american_odds)
    else:
        # Negative odds
        implied_prob = abs(american_odds) / (abs(american_odds) + 100)
    
    return round(implied_prob, 4)


def calculate_ev(model_prob, american_odds):
    """
    Calculate Expected Value (EV)
    
    EV = (Model Probability) - (Implied Probability)
    
    Positive EV = Good bet (model has edge)
    Negative EV = Bad bet (sportsbook has edge)
    
    Example:
        Model: 55% to go OVER
        Odds: -110 (implied prob 52.38%)
        EV = 55% - 52.38% = +2.62% ✅ BET IT
    """
    implied_prob = american_odds_to_implied_prob(american_odds)
    ev = model_prob - implied_prob
    return round(ev, 4)


def projection_to_probability(projection, line, stat_type='PTS', std_dev=None):
    """
    Convert projection + line to probability using normal distribution
    
    If projection > line: probability of going OVER
    If projection < line: probability of going UNDER
    
    Uses z-score and normal CDF
    
    Parameters:
    -----------
    projection : float
        Model's projected value for the stat
    line : float
        Sportsbook line
    stat_type : str
        Type of stat (PTS, AST, REB, BLK, STL, PRA, etc.)
        Used to look up the correct standard deviation
    std_dev : float, optional
        Override standard deviation (if None, uses stat-type default)
    """
    from scipy.stats import norm
    
    # If std_dev not provided, use stat-type defaults
    if std_dev is None:
        STD_DEVS = {
            'PTS': 5.5, 'AST': 2.2, 'REB': 2.8, 'BLK': 1.1, 'STL': 0.9,
            'PRA': 8.0, 'PA': 6.5, 'PR': 7.0, 'AR': 3.5, 'RA': 3.5
        }
        std_dev = STD_DEVS.get(stat_type, 5.5)  # Default to points std_dev if unknown
    
    # Z-score tells us how many std devs away from the line
    z_score = (projection - line) / std_dev
    
    # Convert z-score to probability (OVER probability)
    over_prob = norm.cdf(z_score)
    
    return round(over_prob, 4)


def generate_bet_signal(
    player_name,
    season,
    line,
    american_odds,
    stat_type='PTS',
    bet_type='OVER',
    min_ev=0.03,
    min_edge=0.5,
    opponent=None
):
    """
    Full pipeline: Projection → Probability → EV → Signal
    
    Parameters:
    -----------
    player_name : str
        Player name (e.g., "LeBron James")
    season : int
        NBA season (e.g., 2025)
    line : float
        Sportsbook line (e.g., 24.5)
    american_odds : int
        Betting odds (e.g., -110, +110)
    stat_type : str
        Type of stat (PTS, AST, REB, BLK, STL, PRA, PA, PR, AR, RA)
        Default: 'PTS' (points)
    bet_type : str
        'OVER' or 'UNDER'
    min_ev : float
        Minimum EV to trigger signal (default 3%)
    min_edge : float
        Minimum edge in points (default 0.5)
    opponent : str
        Opponent code for adjustment (optional)
    
    Returns:
    --------
    dict with signal, ev, prob, confidence, etc.
    """
    
    # Step 1: Generate projection
    projection_data = generate_projection(
        player_name=player_name,
        season=season,
        line=line,
        stat_type=stat_type,
        opponent=opponent,
        model='simple'
    )
    
    if projection_data is None:
        return {
            'signal': 'NO DATA',
            'player_name': player_name,
            'line': line,
            'stat_type': stat_type,
            'error': f'Player {player_name} not found for {stat_type}'
        }
    
    projection = projection_data['projection']
    edge = projection_data['edge']
    
    # Step 2: Calculate probability based on bet type
    if bet_type == 'OVER':
        # OVER probability = probability projection > line
        model_prob = projection_to_probability(projection, line, stat_type=stat_type)
    else:  # UNDER
        # UNDER probability = probability projection < line
        model_prob = 1 - projection_to_probability(projection, line, stat_type=stat_type)
    
    # Step 3: Calculate EV
    ev = calculate_ev(model_prob, american_odds)
    
    # Step 4: Generate signal
    # Only BET if edge > threshold AND EV > threshold
    if abs(edge) < min_edge:
        signal = "NO BET"
        reason = f"Edge too small: {edge:.2f} pts (min {min_edge})"
    elif ev < min_ev:
        signal = "NO BET"
        reason = f"EV too low: {ev:.2%} (min {min_ev:.2%})"
    else:
        signal = "BET"
        reason = f"Strong signal: {edge:.2f} pt edge, {ev:.2%} EV"
    
    # Determine implied probability for display
    implied_prob = american_odds_to_implied_prob(american_odds)
    
    return {
        'player_name': player_name,
        'line': line,
        'stat_type': stat_type,
        'projection': projection,
        'edge': edge,
        'bet_type': bet_type,
        'american_odds': american_odds,
        'implied_prob': implied_prob,
        'model_prob': model_prob,
        'ev': ev,
        'signal': signal,
        'reason': reason,
        'confidence': abs(edge),  # Confidence is edge magnitude
        'z_score': projection_data['z_score'],
        'season_avg': projection_data['season_avg'],
        'last10_avg': projection_data['last10_avg'],
    }


def print_bet_signal(signal_data):
    """Pretty print a bet signal"""
    
    print(f"\n{'='*80}")
    print(f"🎯 BET SIGNAL: {signal_data['player_name'].upper()}")
    print(f"{'='*80}")
    
    if signal_data.get('error'):
        print(f"❌ Error: {signal_data['error']}")
        print(f"{'='*80}\n")
        return
    
    # Color code the signal
    if signal_data['signal'] == 'BET':
        signal_display = f"✅ {signal_data['signal']} {signal_data['bet_type']}"
    else:
        signal_display = f"⏸️  {signal_data['signal']}"
    
    print(f"Signal:              {signal_display}")
    print(f"Stat Type:           {signal_data['stat_type']}")
    print(f"Reason:              {signal_data['reason']}")
    
    print(f"\n📊 Numbers:")
    print(f"  Line:              {signal_data['line']:.1f} {signal_data['stat_type']}")
    print(f"  Projection:        {signal_data['projection']:.2f} {signal_data['stat_type']}")
    print(f"  Edge:              {signal_data['edge']:+.2f} {signal_data['stat_type']}")
    print(f"  Confidence (σ):    {signal_data['confidence']:.2f}")
    
    print(f"\n💰 Probability & EV:")
    print(f"  Sportsbook odds:   {signal_data['american_odds']}")
    print(f"  Implied Prob:      {signal_data['implied_prob']:.2%}")
    print(f"  Model Prob:        {signal_data['model_prob']:.2%}")
    print(f"  EV:                {signal_data['ev']:+.2%} {'🔥' if signal_data['ev'] > 0.05 else '✓' if signal_data['ev'] > 0 else '❌'}")
    
    print(f"\n📈 Season Stats:")
    print(f"  Season Avg:        {signal_data['season_avg']:.2f} {signal_data['stat_type']}")
    print(f"  Last 10 Avg:       {signal_data['last10_avg']:.2f} {signal_data['stat_type']}")
    
    print(f"{'='*80}\n")


def test_multiple_signals():
    """Test multiple prop bets with different odds and stat types"""
    
    season = get_latest_season()
    
    # Examples covering different stat types and odds
    test_props = [
        # Points
        {
            'player_name': 'LeBron James',
            'stat_type': 'PTS',
            'line': 24.5,
            'american_odds': -110,
            'bet_type': 'OVER',
            'opponent': 'GSW'
        },
        # Assists
        {
            'player_name': 'Shai Gilgeous-Alexander',
            'stat_type': 'AST',
            'line': 5.5,
            'american_odds': -110,
            'bet_type': 'OVER',
            'opponent': None
        },
        # Rebounds
        {
            'player_name': 'Jalen Johnson',
            'stat_type': 'REB',
            'line': 8.5,
            'american_odds': +100,
            'bet_type': 'OVER',
            'opponent': 'MIA'
        },
        # Points + Rebounds + Assists (PRA combo)
        {
            'player_name': 'Stephen Curry',
            'stat_type': 'PRA',
            'line': 54.5,
            'american_odds': -110,
            'bet_type': 'UNDER',
            'opponent': None
        },
        # Points + Assists (PA combo)
        {
            'player_name': 'De\'Aaron Fox',
            'stat_type': 'PA',
            'line': 35.5,
            'american_odds': -130,
            'bet_type': 'OVER',
            'opponent': None
        },
    ]
    
    print(f"\n{'='*80}")
    print(f"🏀 NBA PROP BET SIGNAL GENERATOR (MULTI-STAT)")
    print(f"Season: {season}")
    print(f"{'='*80}")
    
    # Generate all signals
    all_signals = []
    for prop in test_props:
        signal = generate_bet_signal(
            player_name=prop['player_name'],
            season=season,
            line=prop['line'],
            american_odds=prop['american_odds'],
            stat_type=prop['stat_type'],
            bet_type=prop['bet_type'],
            min_ev=0.03,
            min_edge=0.5,
            opponent=prop['opponent']
        )
        all_signals.append(signal)
        print_bet_signal(signal)
    
    # Summary table
    print(f"\n{'='*80}")
    print(f"📋 SUMMARY TABLE")
    print(f"{'='*80}\n")
    
    print(f"{'Player':<20} {'Stat':<6} {'Line':<8} {'Proj':<8} {'Edge':<8} {'Odds':<8} {'EV':<8} {'Signal':<12}")
    print("-" * 95)
    
    for signal in all_signals:
        if signal.get('error'):
            print(f"{signal['player_name']:<20} {'ERROR':<6}")
            continue
        
        signal_text = f"{'✅ BET' if signal['signal'] == 'BET' else '⏸️  PASS':<12}"
        
        print(f"{signal['player_name']:<20} {signal['stat_type']:<6} {signal['line']:<8.1f} {signal['projection']:<8.2f} "
              f"{signal['edge']:<8.2f} {signal['american_odds']:<8} {signal['ev']:<8.2%} {signal_text}")
    
    print()
    
    # Bet summary
    bets = [s for s in all_signals if s['signal'] == 'BET']
    print(f"\n🎯 Actionable Bets: {len(bets)} out of {len(all_signals)}")
    if bets:
        avg_ev = sum(b['ev'] for b in bets) / len(bets)
        print(f"   Average EV: {avg_ev:.2%}")
        print(f"   \nBets:")
        for b in bets:
            print(f"      • {b['player_name']} {b['bet_type']} {b['line']} {b['stat_type']} @ {b['american_odds']} (EV: {b['ev']:+.2%})")


def interactive_bet_signal():
    """Interactive mode for testing individual prop bets with any stat type"""
    from feature_engineering import get_all_players, normalize_player_name
    
    season = get_latest_season()
    
    print(f"\n{'='*70}")
    print(f"💰 INTERACTIVE BET SIGNAL TESTER")
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
            line = float(input("Enter line: "))
            
            # STEP 4: Get odds
            odds_input = input("Enter American odds (e.g., -110, +100): ").strip()
            american_odds = int(odds_input)
            
            # STEP 5: Get bet type
            bet_type = input("BET type (OVER or UNDER): ").strip().upper()
            if bet_type not in ['OVER', 'UNDER']:
                print("❌ Invalid bet type. Use OVER or UNDER\n")
                continue
            
            # STEP 6: Get opponent (optional)
            opponent = input("Enter opponent (optional, press Enter for none): ").strip() or None
            
            # Generate signal
            signal = generate_bet_signal(
                player_name=player,
                season=season,
                line=line,
                american_odds=american_odds,
                stat_type=stat_type,
                bet_type=bet_type,
                min_ev=0.03,
                min_edge=0.5,
                opponent=opponent
            )
            
            print_bet_signal(signal)
        
        except ValueError as e:
            print(f"❌ Invalid input: {e}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
            
            opponent = input("Enter opponent code (or press Enter for none): ").strip() or None
            
            # Generate signal
            signal = generate_bet_signal(
                player_name=player,
                season=season,
                line=line,
                american_odds=american_odds,
                stat_type=stat_type,
                bet_type=bet_type,
                min_ev=0.03,
                min_edge=0.5,
                opponent=opponent
            )
            
            print_bet_signal(signal)
        
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_bet_signal()
    else:
        test_multiple_signals()
