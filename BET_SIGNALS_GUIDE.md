# Bet Signals Guide - Steps 4A & 4B

## Overview

`bet_signals.py` converts your player projections into **actionable BET/NO BET signals** using Expected Value (EV) calculation.

## How It Works

### Step 4A: Expected Value (EV) Calculation

**The Problem:** Your model says Shai will score 32.14, but the sportsbook line is 30.5. Should you bet?

**The Solution:** Calculate EV

```
1. Convert odds to IMPLIED PROBABILITY
   Odds: -110
   Implied Prob = 110 / (110 + 100) = 52.38%
   
2. Convert projection to MODEL PROBABILITY  
   Projection: 32.14 (above line 30.5)
   Model Prob = 61.72% (using normal distribution)
   
3. Calculate EV
   EV = Model Prob - Implied Prob
   EV = 61.72% - 52.38% = +9.34% 🔥
```

**Interpretation:**
- **EV > 3%** = Good bet (model has edge)
- **EV > 5%** = Excellent bet
- **EV < 0%** = Avoid (sportsbook has edge)

### Step 4B: Bet Signal Logic

```python
if abs(edge) < 0.5 pts:
    signal = "NO BET"  # Edge too small
elif ev < 3%:
    signal = "NO BET"  # EV too low
else:
    signal = "✅ BET"  # All conditions met
```

**Example Results:**
```
✅ Shai OVER 30.5 @ -110
   Edge: +1.64 pts (Projection 32.14 > Line 30.5)
   Model Prob: 61.72%
   Implied Prob: 52.38%
   EV: +9.34% 🔥 STRONG BET

⏸️  Jalen OVER 22.5 @ +100
   Edge: +0.20 pts (too small)
   EV: +1.45% (below 3% threshold)
   NO BET - Edge too small
```

---

## Usage

### Run Test Suite (5 Example Props)
```bash
python3 bet_signals.py
```

Shows:
- Individual bet signal cards for each prop
- Summary table
- Total actionable bets and average EV

**Example Output:**
```
🎯 Actionable Bets: 2 out of 5
   Average EV: 7.90%
   
Bets:
   • Shai Gilgeous-Alexander OVER 30.5 @ -110 (EV: +9.34%)
   • Stephen Curry UNDER 28.5 @ -110 (EV: +6.47%)
```

### Interactive Mode (Test Your Own Props)
```bash
python3 bet_signals.py interactive
```

Prompts you for:
```
Enter player name: Jayson Tatum
Enter line (points): 25.5
Enter American odds (e.g., -110, +100): -120
BET type (OVER or UNDER): OVER
Enter opponent code (or press Enter): MIL
```

Then generates signal with full EV breakdown.

---

## Understanding the Bet Signal Card

```
================================================================================
🎯 BET SIGNAL: SHAI GILGEOUS-ALEXANDER
================================================================================
Signal:              ✅ BET OVER
Reason:              Strong signal: 1.64 pt edge, 9.34% EV

📊 Numbers:
  Line:              30.5 pts
  Projection:        32.14 pts
  Edge:              +1.64 pts
  Confidence (σ):    1.64

💰 Probability & EV:
  Sportsbook odds:   -110
  Implied Prob:      52.38%
  Model Prob:        61.72%
  EV:                +9.34% 🔥

📈 Season Stats:
  Season Avg:        31.13 PPG
  Last 10 Avg:       34.50 PPG
```

**Key Fields:**

- **Signal**: ✅ BET or ⏸️ NO BET
- **Reason**: Why the signal was generated
- **Line**: Sportsbook line
- **Projection**: Your model's prediction
- **Edge**: How many points above/below the line (projection - line)
- **Implied Prob**: Sportsbook's probability (from odds)
- **Model Prob**: Your model's probability
- **EV**: Expected value per $1 wagered
- **Confidence**: Standard deviations from line (larger = more confident)

---

## Odds Reference

### American Odds to Probability

**Negative Odds (-110):**
```
Prob = 110 / (110 + 100) = 52.38%
Better for sportsbook
```

**Positive Odds (+100):**
```
Prob = 100 / (100 + 100) = 50.00%
Better for bettor
```

**Quick Reference:**
```
-110  → 52.38% implied prob
-120  → 54.55% implied prob
-130  → 56.52% implied prob
+100  → 50.00% implied prob
+110  → 47.62% implied prob
```

---

## What EV Means for Profit

If you bet $100 on a play with **+9.34% EV**:

```
Expected Value = $100 × 9.34% = +$9.34
(Per bet, long-term average)

Over 100 bets at +9.34% EV:
Expected Profit = $100 × 100 × 9.34% = $9,340
```

---

## Thresholds (Configurable)

Default settings in `generate_bet_signal()`:
```python
min_ev = 0.03        # 3% - Only bet if EV > 3%
min_edge = 0.5       # 0.5 pts - Only bet if edge > 0.5 pts
```

You can adjust these:
```python
signal = generate_bet_signal(
    player_name='LeBron James',
    season=2025,
    line=24.5,
    american_odds=-110,
    bet_type='OVER',
    min_ev=0.05,      # Stricter: 5% EV threshold
    min_edge=1.0,     # Stricter: 1.0 pt edge threshold
)
```

---

## Integration with Projection Model

The bet signal uses:
1. **Projection** from `projection_model.py`
2. **Features** (season avg, last 10, opponent adjustment)
3. **Odds** from sportsbooks (manual for now, API later)

---

## Next Steps

1. ✅ **Step 4A**: EV Calculation (DONE)
2. ✅ **Step 4B**: Bet Signal Logic (DONE)
3. **Step 5**: The Odds API Integration (NEXT)
   - Fetch live prop lines from sportsbooks
   - Auto-generate signals for all available props
   - Set up daily alerts

4. **Step 6**: Backtesting
   - Test projections against historical results
   - Calculate hit rate
   - Optimize thresholds

---

## Files

- `bet_signals.py` - Main signal generator
- `projection_model.py` - Player projections
- `feature_engineering.py` - Player statistics
- `fetch_game_logs.py` - Game data
- `daily_update.py` - Daily data refresh

---

## Questions?

**Q: How do I know if a signal is good?**
A: Look for EV > 3% AND edge > 0.5 pts. Higher EV = better bet.

**Q: Why is Stephen Curry UNDER even though his projection is lower?**
A: When projection < line, the probability of going UNDER is high. If the implied probability is lower, there's positive EV.

**Q: Can I use this with other bet types?**
A: Currently supports player points (OVER/UNDER). Can extend to assists, rebounds, etc.

