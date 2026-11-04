from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd
import time

HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Connection': 'keep-alive',
}

def get_player_id(player_name: str):
    player_dict = players.get_players()
    
    for p in player_dict:
        if p['full_name'].lower() == player_name.lower():
            return p['id'], p['full_name']
    
    matches = [p for p in player_dict if player_name.lower() in p['full_name'].lower()]
    if matches:
        return matches[0]['id'], matches[0]['full_name']
    
    return None, None

def get_player_games(player_name: str, season_type="Regular Season", last_n=15):
    player_id, full_name = get_player_id(player_name)
    
    if not player_id:
        raise ValueError(f"Jugador '{player_name}' no encontrado")
    
    try:
        logs = playergamelog.PlayerGameLog(
            player_id=player_id,
            season="2025-26",  # Cambiamos temporalmente a la temporada anterior
            season_type_all_star=season_type,
            headers=HEADERS
        )
        df = logs.get_data_frames()[0]
    except Exception as e:
        raise ValueError(f"Error al obtener datos: {str(e)}")
    
    if df.empty:
        return pd.DataFrame(), full_name
    
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], errors='coerce')
    df = df.sort_values('GAME_DATE', ascending=False)
    
    if 'MIN' in df.columns:
        df['MIN'] = pd.to_numeric(df['MIN'], errors='coerce')
    
    return df.head(last_n), full_name

def is_double_double(row):
    categories = ['PTS', 'REB', 'AST', 'STL', 'BLK']
    count = sum(1 for cat in categories if row.get(cat, 0) >= 10)
    return 1 if count >= 2 else 0

def is_triple_double(row):
    categories = ['PTS', 'REB', 'AST', 'STL', 'BLK']
    count = sum(1 for cat in categories if row.get(cat, 0) >= 10)
    return 1 if count >= 3 else 0

def analyze_prop(player_name: str, prop: str = "PTS", line: float = 20.5, last_n: int = 15):
    df, full_name = get_player_games(player_name, "Regular Season", last_n)
    
    if df.empty:
        raise ValueError(f"No se encontraron partidos para {player_name}")
    
    df = df.copy()
    
    if prop == "DD":
        df["DD"] = df.apply(is_double_double, axis=1)
        value_col = "DD"
    elif prop == "TD":
        df["TD"] = df.apply(is_triple_double, axis=1)
        value_col = "TD"
    elif prop == "MIN":
        value_col = "MIN"
    elif prop == "PRA":
        df["PRA"] = df["PTS"] + df["REB"] + df["AST"]
        value_col = "PRA"
    elif prop == "PR":
        df["PR"] = df["PTS"] + df["REB"]
        value_col = "PR"
    elif prop == "PA":
        df["PA"] = df["PTS"] + df["AST"]
        value_col = "PA"
    elif prop == "RA":
        df["RA"] = df["REB"] + df["AST"]
        value_col = "RA"
    else:
        if prop not in df.columns:
            raise ValueError(f"Prop '{prop}' no disponible")
        value_col = prop
    
    df["Over"] = df[value_col] > line
    
    stats = {
        "player": full_name,
        "avg": round(df[value_col].mean(), 1),
        "hit_rate": round(df["Over"].mean() * 100, 1),
        "games": len(df),
        "prop": prop,
        "line": line,
        "value_col": value_col
    }
    
    return df, stats
