"""
Aplicação Streamlit para visualização dos dados dos silos e histórico de alertas.
"""

import streamlit as st

def main():
    st.set_page_config(page_title="Monitoramento de Silos - Agrisolus", layout="wide")
    st.title("📊 Monitoramento de Silos Agrisolus")
    st.write("Bem-vindo ao painel de controle do silo.")

if __name__ == "__main__":
    main()
