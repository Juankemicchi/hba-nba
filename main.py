from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nba_module import analyze_prop
from pydantic import BaseModel
import os
import requests
from openai import OpenAI

app = FastAPI(title="HBA NBA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)

BIGBALLS_KEY = os.getenv("BIGBALLS_API_KEY", "")
HEADERS = {"Authorization": f"Bearer {BIGBALLS_KEY}"}
BASE_URL = "https://api.bigballsdata.com/v1"

class PropRequest(BaseModel):
    player: str
    prop: str
    line: float
    last_n: int = 12

@app.get("/")
def root():
    return {"message": "HBA NBA Backend activo", "ai": bool(os.getenv("XAI_API_KEY"))}

def get_upcoming_matchup(player_name: str):
    try:
        response = requests.get(
            f"{BASE_URL}/matches",
            headers=HEADERS,
            params={"sport": "basketball", "league": "nba", "limit": 15}
        )
        if response.status_code != 200:
            return None
        
        matches = response.json().get("data", [])
        for match in matches:
            if match.get("status") == "scheduled":
                return match
        return matches[0] if matches else None
    except:
        return None

def generate_ai_analysis(player: str, prop: str, line: float, avg: float, hit_rate: float, games: int, matchup=None):
    hits = round((hit_rate / 100) * games)
    
    rival_info = ""
    if matchup:
        home = matchup.get("home", {}).get("name", "Local")
        away = matchup.get("away", {}).get("name", "Visitante")
        rival_info = f"\nPróximo partido: {away} vs {home}."

    prompt = f"""Eres un analista de apuestas deportivas profesional y experimentado. 
Habla de forma natural, como un tipster que analiza partidos.

Datos del jugador:
- Jugador: {player}
- Prop: {prop}
- Línea: {line}
- Promedio reciente: {avg}
- Hit rate: {hit_rate}% ({hits} de {games} partidos)
{rival_info}

Genera un análisis de 4 a 6 líneas que incluya:
1. Evaluación del promedio vs la línea.
2. Consistencia del jugador en los últimos partidos.
3. Nivel de riesgo del pick.
4. Menciona el próximo rival (si tienes la información) y cómo puede afectar.
5. Una conclusión clara (si el over o under tiene valor).

Sé directo, profesional y útil. No uses listas numeradas. Habla en un solo párrafo o dos."""

    try:
        response = client.chat.completions.create(
            model="grok-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.75
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error Grok:", str(e))
        return f"Error al generar análisis: {str(e)}"

@app.post("/analyze")
def analyze(request: PropRequest):
    try:
        df, stats = analyze_prop(
            player_name=request.player,
            prop=request.prop,
            line=request.line,
            last_n=request.last_n
        )
        
        matchup = get_upcoming_matchup(request.player)
        
        ai_analysis = generate_ai_analysis(
            player=stats["player"],
            prop=request.prop,
            line=request.line,
            avg=stats["avg"],
            hit_rate=stats["hit_rate"],
            games=stats["games"],
            matchup=matchup
        )
        
        games = df.to_dict(orient='records')
        
        for game in games:
            if 'opponent' not in game or not game['opponent']:
                matchup_str = game.get('MATCHUP', '')
                if isinstance(matchup_str, str) and matchup_str:
                    game['opponent'] = matchup_str.split()[-1]
                else:
                    game['opponent'] = "Rival"
        
        return {
            "stats": stats,
            "games": games,
            "ai_analysis": ai_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
