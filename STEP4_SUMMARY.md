# NBA Prop Bot - Steps 4A & 4B Summary

## ✅ What's Complete

### Step 4A: Expected Value (EV) Calculation
```python
from bet_signals import calculate_ev, american_odds_to_implied_prob

# Convert odds to probability
implied_prob = american_odds_to_implied_prob(-110)  # 52.38%

# Calculate EV
ev = calculate_ev(model_prob=0.6172, american_odds=-110)  # +9.34%
```

**EV Formula:**
```
EV = (Your Win Probability) - (Sportsbook's Implied Probability)
```

**Interpretation:**
- **EV > 3%** = Good bet ✅
- **EV > 5%** = Great bet 🔥
- **EV < 0%** = Bad bet ❌

---

### Step 4B: Bet Signal Logic
```python
from bet_signals import generate_bet_signal

signal = generate_bet_signal(
    player_name='Shai Gilgeous-Alexander',
    season=2025,
    line=30.5,
    american_odds=-110,
    bet_type='OVER',
    min_ev=0.03,      # Only bet if EV > 3%
    min_edge=0.5      # Only bet if edge > 0.5 pts
)

if signal['signal'] == 'BET':
    print(f"✅ BET {signal['bet_type']} at {signal['american_odds']}")
    print(f"   EV: {signal['ev']:+.2%}")
else:
    print(f"⏸️ NO BET - {signal['reason']}")
```

**Signal Requirements:**
1. **Edge > 0.5 pts** (Projection vs Line difference)
2. **EV > 3%** (Model edge over implied odds)
3. Both must be true

---

## 🎯 Usage

### Run All Test Examples
```bash
python3 bet_signals.py
```

**Output:**
- 5 example prop bets
- Full signal cards for each
- Summary table
- Actionable bets highlighted

### Interactive Mode
```bash
python3 bet_signals.py interactive
```

**Prompts:**
```
Enter player name: Jayson Tatum
Enter line (points): 25.5
Enter American odds: -120
BET type (OVER or UNDER): OVER
Enter opponent code: MIL
```

**Returns:**
```
✅ BET OVER (or ⏸️ NO BET)
EV: +X.XX%
Edge: +X.XX pts
```

---

## 📊 Real Results from Test

### ✅ BET SIGNALS
```
1. Shai Gilgeous-Alexander OVER 30.5 @ -110
   Projection: 32.14 pts
   Edge: +1.64 pts
   EV: +9.34% 🔥
   
2. Stephen Curry UNDER 28.5 @ -110
   Projection: 27.27 pts
   Edge: -1.23 pts
   EV: +6.47% 🔥
```

### ❌ NO BET SIGNALS
```
1. LeBron James OVER 24.5 @ -110
   Projection: 19.46 pts
   Edge: -5.04 pts
   EV: -34.41% ❌ (Way below line)

2. Jalen Johnson OVER 22.5 @ -100
   Projection: 22.62 pts
   Edge: +0.12 pts
   EV: +0.87% (Edge too small)
```

---

## 🔧 Key Functions

### `american_odds_to_implied_prob(odds)`
Converts betting odds to probability
```python
american_odds_to_implied_prob(-110)  # 0.5238 (52.38%)
american_odds_to_implied_prob(+100)  # 0.5000 (50.00%)
```

### `calculate_ev(model_prob, american_odds)`
Calculates expected value
```python
calculate_ev(0.6172, -110)  # 0.0934 (+9.34%)
```

### `projection_to_probability(projection, line)`
Converts projection to win probability using normal distribution
```python
projection_to_probability(32.14, 30.5)  # 0.6172 (61.72%)
```

### `generate_bet_signal(...)`
Full pipeline: projection → probability → EV → signal
```python
signal = generate_bet_signal(
    player_name='Shai Gilgeous-Alexander',
    season=2025,
    line=30.5,
    american_odds=-110,
    bet_type='OVER',
    min_ev=0.03,
    min_edge=0.5
)
```

### `print_bet_signal(signal_data)`
Pretty prints a bet signal card
```python
print_bet_signal(signal)
```

---

## 🎲 Understanding the Math

### Example: Shai OVER 30.5 @ -110

**Step 1: Get Projection**
```
Model says: 32.14 pts average
Line: 30.5 pts
Edge: 32.14 - 30.5 = +1.64 pts
```

**Step 2: Convert to Probability**
```
Using normal distribution (std_dev = 5.5):
P(score > 30.5 | avg = 32.14) = 61.72%
```

**Step 3: Get Implied Probability from Odds**
```
Odds: -110
Implied: 110 / (110 + 100) = 52.38%
```

**Step 4: Calculate EV**
```
EV = 61.72% - 52.38% = +9.34%
This means your edge is 9.34%
```

**Step 5: Make Decision**
```
Edge > 0.5 pts? ✅ YES (+1.64)
EV > 3%? ✅ YES (+9.34%)
Signal: ✅ BET OVER
```

---

## 💰 Profit Calculation

If you bet $100 on each signal with **+9.34% EV**:

```
Expected Profit per Bet = $100 × 9.34% = +$9.34

Over 10 bets:
Expected Total = $100 × 10 × 9.34% = $934

Over 100 bets:
Expected Total = $100 × 100 × 9.34% = $9,340
```

---

## 📈 Next Steps

**Step 5: The Odds API Integration**
- Fetch live prop lines from DraftKings, FanDuel, etc.
- Auto-match to player database
- Generate signals for ALL available props
- Set up daily alerts

**Step 6: Backtesting**
- Test model accuracy on historical data
- Calculate hit rates
- Optimize thresholds

---

## 📁 Files

| File | Purpose |
|------|---------|
| `bet_signals.py` | EV calc & bet signal logic (Steps 4A/4B) |
| `projection_model.py` | Player projections |
| `feature_engineering.py` | Season stats, last 10, opponent adj |
| `fetch_game_logs.py` | Fetch games from nba_api |
| `daily_update.py` | Keep database fresh |
| `nba_data.db` | SQLite database with 8,154+ games |

---

## ❓ FAQ

**Q: Why does -110 odds = 52.38%?**
A: Negative odds = you risk that amount to win $100
```
-110: Risk $110 to win $100
Prob = 110/(110+100) = 52.38%
```

**Q: What's a "good" EV threshold?**
A: 
- Casual: > 3%
- Semi-pro: > 5%
- Professional: > 2% (with high volume)

**Q: Can I change the thresholds?**
A: Yes! In `generate_bet_signal()`:
```python
min_ev=0.05      # Stricter: 5%
min_edge=1.0     # Stricter: 1.0 pt
```

**Q: How many bets should I make?**
A: More is better for long-term profit. With +9.34% EV, you break even around 90 bets.

