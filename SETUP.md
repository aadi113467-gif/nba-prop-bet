# NBA Prop Bot - Daily Update Setup

## Run Initial Data Load

```bash
cd /Users/aadishah/nba-prop-bet
python3 fetch_game_logs.py
```

This will:
- ✅ Initialize SQLite database
- ✅ Fetch top 8 players from each NBA team
- ✅ Pull game logs from 2020-21 season through 2025-26
- ✅ Store ~2,500+ games total

## Schedule Daily Updates (macOS)

### Option 1: Cron Job (Recommended)

Edit crontab:
```bash
crontab -e
```

Add this line (runs daily at 12:00 AM):
```
0 0 * * * cd /Users/aadishah/nba-prop-bet && python3 daily_update.py >> logs/daily_update.log 2>&1
```

Or run at 1 AM:
```
0 1 * * * cd /Users/aadishah/nba-prop-bet && python3 daily_update.py >> logs/daily_update.log 2>&1
```

Create logs directory first:
```bash
mkdir -p /Users/aadishah/nba-prop-bet/logs
```

### Option 2: LaunchAgent (Alternative)

Create `~/Library/LaunchAgents/com.nbapropbot.daily.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nbapropbot.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Library/Frameworks/Python.framework/Versions/3.14/bin/python3</string>
        <string>/Users/aadishah/nba-prop-bet/daily_update.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>1</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/aadishah/nba-prop-bet/logs/daily_update.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aadishah/nba-prop-bet/logs/daily_update_error.log</string>
</dict>
</plist>
```

Then load it:
```bash
launchctl load ~/Library/LaunchAgents/com.nbapropbot.daily.plist
```

## Check Database

```bash
sqlite3 nba_data.db
SELECT COUNT(*) FROM game_logs;
SELECT player_name, COUNT(*) as games FROM game_logs GROUP BY player_name LIMIT 10;
```

## Monitor Logs

```bash
tail -f logs/daily_update.log
```
