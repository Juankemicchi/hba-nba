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

class PropRequest(BaseModel):
    player: str
    prop: str
    line: float
    last_n: int = 12

@app.get("/")
def root():
    return {"message": "HBA NBA Backend activo", "ai": bool(os.getenv("XAI_API_KEY"))}

def generate_ai_analysis(player: str, prop: str, line: float, avg: float, hit_rate: float, games: int):
    hits = round((hit_rate / 100) * games)
    
    prompt = f"""Eres un analista de apuestas deportivas profesional. 
Genera un análisis natural y útil (3 a 5 líneas) para este prop de NBA.

Datos:
- Jugador: {player}
- Prop: {prop}
- Línea: {line}
- Promedio reciente: {avg}
- Hit rate: {hit_rate}% ({hits} de {games} partidos)

Analiza:
- Si el promedio está por encima o por debajo de la línea
- La consistencia del jugador
- El nivel de riesgo
- Una conclusión clara

Habla de forma natural, como un tipster. No uses listas."""

    try:
        response = client.chat.completions.create(
            model="grok-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.8
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
        
        ai_analysis = generate_ai_analysis(
            player=stats["player"],
            prop=request.prop,
            line=request.line,
            avg=stats["avg"],
            hit_rate=stats["hit_rate"],
            games=stats["games"]
        )
        
        games = df.to_dict(orient='records')
        
        return {
            "stats": stats,
            "games": games,
            "ai_analysis": ai_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
