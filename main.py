import streamlit as st
from nba_module import analyze_prop
from visualizations import plot_prop_chart

st.set_page_config(page_title="HBA NBA", page_icon="🏀", layout="wide")

st.title("🏀 HBA NBA - Analizador de Player Props")
st.markdown("**Temporada 2026-27**")

if "favorites" not in st.session_state:
    st.session_state.favorites = []

st.sidebar.header("⚙️ Configuración")

if st.session_state.favorites:
    fav_choice = st.sidebar.selectbox("Favoritos", ["-- Ninguno --"] + st.session_state.favorites)
    if fav_choice != "-- Ninguno --":
        player = st.sidebar.text_input("Nombre del Jugador", fav_choice)
    else:
        player = st.sidebar.text_input("Nombre del Jugador", "Jalen Brunson")
else:
    player = st.sidebar.text_input("Nombre del Jugador", "Jalen Brunson")

# Nombres claros para los mercados
market_options = {
    "Puntos": "PTS",
    "Rebotes": "REB",
    "Asistencias": "AST",
    "Puntos + Rebotes + Asistencias": "PRA",
    "Puntos + Rebotes": "PR",
    "Puntos + Asistencias": "PA",
    "Rebotes + Asistencias": "RA",
    "Triples Anotados": "FG3M",
    "Robos": "STL",
    "Tapones": "BLK",
    "Pérdidas": "TOV",
    "Tiros de Campo Anotados": "FGM",
    "Tiros de Campo Intentados": "FGA",
    "Minutos": "MIN",
    "Double-Double": "DD",
    "Triple-Double": "TD"
}

prop_display = st.sidebar.selectbox("Mercado", list(market_options.keys()))
prop = market_options[prop_display]

line = st.sidebar.selectbox(
    "Línea",
    options=[round(i + 0.5, 1) for i in range(0, 100)],
    index=20
)

last_n = st.sidebar.slider("Últimos partidos", 5, 25, 12)

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("⭐ Guardar Favorito"):
        if player and player not in st.session_state.favorites:
            st.session_state.favorites.append(player)
            st.success("Agregado a favoritos")
with col2:
    if st.button("🗑️ Limpiar Favoritos"):
        st.session_state.favorites = []

if st.sidebar.button("🔥 Analizar Jugador", type="primary"):
    try:
        df, stats = analyze_prop(player, prop, line, last_n)
        
        st.success(f"✅ {stats['player']} analizado correctamente")
        
        col1, col2 = st.columns([2.5, 1])
        
        with col1:
            plot_prop_chart(df, stats["value_col"], line, stats['player'])
        
        with col2:
            st.metric("Promedio", stats['avg'])
            st.metric("Hit Rate", f"{stats['hit_rate']}%")
            st.metric("Partidos analizados", stats['games'])
            
        st.subheader("Últimos Partidos")
        st.dataframe(
            df[['GAME_DATE', 'MATCHUP', stats["value_col"], 'Over']], 
            use_container_width=True
        )
        
    except Exception as e:
        st.error(str(e))

st.caption("HBA NBA | Temporada 2026-27")