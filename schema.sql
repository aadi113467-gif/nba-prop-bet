CREATE TABLE IF NOT EXISTS game_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    game_date TEXT NOT NULL,
    season INTEGER NOT NULL,
    points INTEGER,
    assists INTEGER,
    rebounds INTEGER,
    minutes REAL,
    fga INTEGER,
    fta INTEGER,
    fgm INTEGER,
    ftm INTEGER,
    opponent TEXT,
    game_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, game_date, season)
);

CREATE INDEX IF NOT EXISTS idx_player_date ON game_logs(player_name, game_date);
CREATE INDEX IF NOT EXISTS idx_season ON game_logs(season);
CREATE INDEX IF NOT EXISTS idx_player_id ON game_logs(player_id);
