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
    return {"message": "HBA NBA Backend activo"}

def get_upcoming_matchup(player_name: str):
    """Intenta obtener el próximo partido del jugador (simplificado)"""
    try:
        # Buscar partidos próximos de NBA
        response = requests.get(
            f"{BASE_URL}/matches",
            headers=HEADERS,
            params={"sport": "basketball", "league": "nba", "limit": 10}
        )
        if response.status_code != 200:
            return None
        
        matches = response.json().get("data", [])
        # Por ahora devolvemos el primer partido programado (puedes mejorar esto después)
        for match in matches:
            if match.get("status") == "scheduled":
                return match
        return matches[0] if matches else None
    except:
        return None

def generate_ai_analysis(player: str, prop: str, line: float, avg: float, hit_rate: float, games: int, matchup=None):
    hits = round((hit_rate / 100) * games)
    
    matchup_text = ""
    if matchup:
        home = matchup.get("home", {}).get("name", "Local")
        away = matchup.get("away", {}).get("name", "Visitante")
        matchup_text = f"\nPróximo partido: {away} vs {home}."

    prompt = f"""Eres un analista de apuestas deportivas experto. 
Analiza este prop de NBA de forma clara, natural y útil (máximo 5 líneas).

Datos del jugador:
- Jugador: {player}
- Prop: {prop}
- Línea: {line}
- Promedio reciente: {avg}
- Hit rate: {hit_rate}% ({hits} de {games} partidos)
{matchup_text}

Analiza:
1. Si el promedio está por encima o por debajo de la línea.
2. La consistencia (qué tan seguido supera la línea).
3. El nivel de riesgo del pick.
4. Menciona el próximo rival si tienes la información.
5. Una conclusión breve y realista.

No inventes estadísticas específicas de jugadores rivales si no las tienes."""

    try:
        response = client.chat.completions.create(
            model="grok-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=220,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"No se pudo generar análisis IA: {str(e)}"

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
        
        return {
            "stats": stats,
            "games": games,
            "ai_analysis": ai_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
