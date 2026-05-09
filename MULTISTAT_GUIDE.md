# Quick Reference: Multi-Stat NBA Prop Bot

## Available Stat Types

### Individual Stats (In Database)
- **PTS** - Points (σ=5.5)
- **AST** - Assists (σ=2.2)
- **REB** - Rebounds (σ=2.8)

### Combo Stats
- **PRA** - Points + Rebounds + Assists (σ=8.0)
- **PA** - Points + Assists (σ=6.5)
- **PR** - Points + Rebounds (σ=7.0)
- **AR** - Assists + Rebounds (σ=3.5)
- **RA** - Rebounds + Assists (σ=3.5)

> **Note:** Blocks (BLK) and Steals (STL) not in current database. Would require additional data source.

---

## Running Tests

### All Projection Tests
```bash
python3 projection_model.py
```
Outputs:
- Shai for all stat types
- Multiple players for PTS/AST/REB
- Combo stats (PRA)
- Rebounds with different lines

### All Bet Signal Tests
```bash
python3 bet_signals.py
```
Outputs:
- 5 example props across different stats
- Detailed signal analysis
- Summary table
- Actionable bets

---

## Interactive Mode

### Test Projections
```bash
python3 projection_model.py interactive
```

**Example Session:**
```
Enter player name: Shai Gilgeous-Alexander
Enter stat type: AST
Enter line: 5.5
Enter opponent: (leave blank)

📊 PROJECTION FOR SHAI GILGEOUS-ALEXANDER
================================
Stat Type:         AST
Line:              5.5 AST
Projection:        6.26 AST
Edge:              +0.76 AST
Lean:              OVER
Z-Score:           0.34σ

Season Stats:
  Season Avg:      6.59 AST
  Last 10 Avg:     6.00 AST
  Last 5 Avg:      5.80 AST
  Games Played:    42
```

### Test Bet Signals
```bash
python3 bet_signals.py interactive
```

**Example Session:**
```
Enter player name: Shai Gilgeous-Alexander
Enter stat type: AST
Enter line: 5.5
Enter American odds: -110
BET type (OVER or UNDER): OVER
Enter opponent: (leave blank)

🎯 BET SIGNAL: SHAI GILGEOUS-ALEXANDER
================================
Signal:              ✅ BET OVER
Stat Type:           AST
Reason:              Strong signal: 0.76 pt edge, 11.13% EV

📊 Numbers:
  Line:              5.5 AST
  Projection:        6.26 AST
  Edge:              +0.76 AST
  Confidence (σ):    0.76

💰 Probability & EV:
  Sportsbook odds:   -110
  Implied Prob:      52.38%
  Model Prob:        63.51%
  EV:                +11.13% 🔥

📈 Season Stats:
  Season Avg:        6.59 AST
  Last 10 Avg:       6.00 AST
```

---

## Python API

### Get Projection
```python
from projection_model import generate_projection

proj = generate_projection(
    player_name='Shai Gilgeous-Alexander',
    season=2025,
    line=5.5,
    stat_type='AST',  # Key: specify stat type
    opponent=None,    # Optional
    model='simple'    # or 'advanced'
)

# Returns:
# {
#     'projection': 6.26,
#     'edge': +0.76,
#     'z_score': 0.34,
#     'lean': 'OVER',
#     'season_avg': 6.59,
#     'last10_avg': 6.00,
# }
```

### Get Bet Signal
```python
from bet_signals import generate_bet_signal

signal = generate_bet_signal(
    player_name='Shai Gilgeous-Alexander',
    season=2025,
    line=5.5,
    american_odds=-110,
    stat_type='AST',  # Key: specify stat type
    bet_type='OVER',  # or 'UNDER'
    min_ev=0.03,      # 3% minimum EV
    min_edge=0.5,     # 0.5 point minimum edge
    opponent=None
)

# Returns:
# {
#     'signal': 'BET',
#     'ev': 0.1113,
#     'model_prob': 0.6351,
#     'implied_prob': 0.5238,
#     'projection': 6.26,
#     ...
# }
```

### Get Player Features
```python
from feature_engineering import get_full_player_features

features = get_full_player_features(
    player_name='Shai Gilgeous-Alexander',
    season=2025,
    stat_type='AST'  # Key: specify stat type
)

# Returns:
# {
#     'season_avg': 6.59,
#     'last10_avg': 6.00,
#     'last5_avg': 5.80,
#     'last3_avg': 5.67,
#     'games_played': 42
# }
```

---

## Understanding Z-Scores & Leans

### Z-Score Calculation
```
Z-Score = (Projection - Line) / Standard Deviation

Example: Shai AST projection 6.26 vs line 5.5
Z-Score = (6.26 - 5.5) / 2.2 = 0.34σ
```

### Lean Rules
- **Z-Score > 0.5σ** → OVER lean (strong)
- **Z-Score > 0.0σ** → OVER lean (weak)
- **Z-Score between -0.5σ and 0.5σ** → NEUTRAL
- **Z-Score < -0.5σ** → UNDER lean (strong)

### Why Stat-Specific Std Devs Matter
```
Points variance: σ=5.5  (players have high game-to-game variance)
Assists variance: σ=2.2 (much tighter - playmakers are consistent)

Effect: Same +1.0 projection edge
- PTS +1.0: Z-Score = 1.0/5.5 = 0.18σ (weak lean)
- AST +1.0: Z-Score = 1.0/2.2 = 0.45σ (stronger lean!)
```

---

## EV Calculation

### Understanding Expected Value
```
EV = (Model Probability) - (Implied Probability)

Example:
- Model says Shai goes OVER 5.5 AST: 63.51% probability
- Sportsbook line -110 implies: 52.38% probability
- EV = 63.51% - 52.38% = +11.13%

Interpretation:
- +11.13% EV = Long-term edge of 11.13% per unit wagered
- Positive EV = Good bet (expected to win)
- Negative EV = Bad bet (sportsbook has edge)
```

### Bet Filtering
```python
# Only generates BET signal if BOTH conditions met:
1. Edge ≥ 0.5 points (min_edge)
2. EV ≥ 3.0% (min_ev)

# If edge is small, likely sportsbook odds too good
# If EV negative, sportsbook has the advantage
```

---

## Common Workflows

### Finding Best Assists Props
```bash
python3 bet_signals.py interactive
# Enter: multiple players with stat_type=AST
# Compare EV across different odds
# Find highest edge opportunities
```

### Testing Combo Stats
```bash
python3 projection_model.py interactive

# PRA (Points+Rebounds+Assists) example:
# Player: Stephen Curry
# Stat: PRA
# Line: 55.0
# Returns projection with standard deviation σ=8.0
```

### Building a Betting Portfolio
```
1. Run interactive mode
2. Test 10 props across different players/stats
3. Filter for EV > 5%
4. Note which stats/players have most edge
5. Size units by confidence level
```

---

## Troubleshooting

### "Player not found"
- Check exact spelling
- Try different case variation (case-insensitive lookup available)
- Verify player played in 2025 season

### "Stat type not recognized"
- Use: PTS, AST, REB (database has these)
- Or combos: PRA, PA, PR, AR, RA
- Blocks/Steals not available

### Projection seems low
- Check if player is "cold" (last5_avg might be below season_avg)
- Ensure correct stat type
- Compare season_avg to projection

### EV is negative on all bets
- Sportsbook line is too tight
- Model may be overestimating projection
- Try tighter min_ev threshold

---

## Database Info

**Current Data:**
- 8,281 game logs
- 75 NBA players
- Seasons: 2024-2025, 2025-2026
- Updated through: April 9, 2026

**Columns Available:**
- player_name, team, game_date, season
- points, assists, rebounds
- minutes, fga, fta, fgm, ftm
- opponent, game_id

---

## Next Steps

1. **Step 5: Odds API Integration**
   - Fetch live props from DK, FD, Fanduel, etc.
   - Auto-match with projections
   - Real-time EV calculation

2. **Risk Management**
   - Unit sizing based on edge
   - Portfolio tracking
   - ROI reporting

3. **Advanced Features**
   - Player injury tracking
   - Back-to-back game adjustments
   - Matchup adjustments (strength vs weak defense)
   - Regression detection
