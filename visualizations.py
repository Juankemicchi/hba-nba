import matplotlib.pyplot as plt
import streamlit as st

def plot_prop_chart(df, prop, line, player_name):
    fig, ax = plt.subplots(figsize=(10, 5))
    
    colors = ['#00c853' if val > line else '#ff1744' for val in df[prop]]
    
    bars = ax.bar(range(len(df)), df[prop], color=colors)
    
    ax.axhline(y=line, color='blue', linestyle='--', linewidth=2, label=f'Línea: {line}')
    
    ax.set_title(f"{player_name} - {prop}", fontsize=14, fontweight='bold')
    ax.set_xlabel("Partidos (más reciente → más antiguo)")
    ax.set_ylabel(prop)
    ax.legend()
    
    # Etiquetas en las barras
    for bar, val in zip(bars, df[prop]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, 
                f'{val}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    st.pyplot(fig)