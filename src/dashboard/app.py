# -*- coding: utf-8 -*-
"""
Dashboard Interativo Streamlit para Monitoramento dos Silos.
Focado exclusivamente no 'Aviário 819'.
Exibe nível de ração em tempo real, curva de consumo, SLA de conectividade e histórico de alertas.
Suporta fallback automático para SQLite se o Supabase estiver indisponível.
"""
import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.connection import DatabaseConnection
from src.utils.datetime_parser import parse_iso_datetime

# CSS Customizado para visual premium (Dark Mode/Neon)
THEME_CSS = """
<style>
    /* Estilo geral */
    .stApp {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    /* Cards personalizados */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-title {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-sub {
        font-size: 12px;
        color: #64748b;
        margin-top: 4px;
    }
</style>
"""

@st.cache_data(ttl=60)
def load_dashboard_data():
    """
    Carrega todos os dados do banco de dados (Supabase principal, fallback SQLite).
    Retorna dataframes formatados.
    """
    db_conn = DatabaseConnection()
    client = db_conn.get_supabase_client()
    
    lotes_list = []
    silos_list = []
    readings_list = []
    alertas_list = []
    calibracoes_list = []
    
    using_supabase = False
    
    if client:
        try:
            # 1. Carrega lotes do Aviário 819
            lotes_res = client.table("lotes").select("*").ilike("aviario", "%Aviário 819%").execute()
            lotes_list = lotes_res.data
            
            if lotes_list:
                lote_ids = [l["id_lote"] for l in lotes_list]
                
                # 2. Carrega silos
                silos_res = client.table("silos").select("*").in_("lote_id", lote_ids).execute()
                silos_list = silos_res.data
                silo_ids = [s["id_silo"] for s in silos_list]
                
                if silo_ids:
                    # 3. Carrega leituras
                    # Limitamos para as últimas 1000 leituras para não sobrecarregar
                    readings_res = client.table("leituras") \
                        .select("*") \
                        .in_("silo_id", silo_ids) \
                        .order("data_leitura", desc=True) \
                        .limit(1000) \
                        .execute()
                    readings_list = readings_res.data
                    
                # 4. Carrega alertas e calibrações
                alertas_res = client.table("alertas").select("*").in_("lote_id", lote_ids).order("data_alerta", desc=True).limit(200).execute()
                alertas_list = alertas_res.data
                
                calibracoes_res = client.table("calibracoes").select("*").in_("lote_id", lote_ids).order("data_calibracao", desc=True).limit(100).execute()
                calibracoes_list = calibracoes_res.data
                
            using_supabase = True
        except Exception as e:
            st.sidebar.error(f"Erro ao conectar ao Supabase: {e}. Carregando do SQLite local...")
            client = None

    if not client:
        try:
            conn = db_conn.get_sqlite_connection()
            # 1. Carrega lotes
            df_lotes = pd.read_sql_query("SELECT * FROM lotes WHERE aviario LIKE '%Aviário 819%'", conn)
            lotes_list = df_lotes.to_dict(orient="records")
            
            if lotes_list:
                lote_ids = [l["id_lote"] for l in lotes_list]
                placeholders = ",".join("?" for _ in lote_ids)
                
                # 2. Carrega silos
                df_silos = pd.read_sql_query(f"SELECT * FROM silos WHERE lote_id IN ({placeholders})", conn, params=lote_ids)
                silos_list = df_silos.to_dict(orient="records")
                silo_ids = [s["id_silo"] for s in silos_list]
                
                if silo_ids:
                    silo_placeholders = ",".join("?" for _ in silo_ids)
                    # 3. Carrega leituras
                    df_readings = pd.read_sql_query(
                        f"SELECT * FROM leituras WHERE silo_id IN ({silo_placeholders}) ORDER BY data_leitura DESC LIMIT 1000",
                        conn, params=silo_ids
                    )
                    readings_list = df_readings.to_dict(orient="records")
                    
                # 4. Carrega alertas e calibrações
                df_alertas = pd.read_sql_query(f"SELECT * FROM alertas WHERE lote_id IN ({placeholders}) ORDER BY data_alerta DESC LIMIT 200", conn, params=lote_ids)
                alertas_list = df_alertas.to_dict(orient="records")
                
                df_calibracoes = pd.read_sql_query(f"SELECT * FROM calibracoes WHERE lote_id IN ({placeholders}) ORDER BY data_calibracao DESC LIMIT 100", conn, params=lote_ids)
                calibracoes_list = df_calibracoes.to_dict(orient="records")
                
            conn.close()
        except Exception as e:
            st.error(f"Erro ao carregar dados do SQLite local: {e}")
            
    # Converte listas para DataFrames
    df_lotes = pd.DataFrame(lotes_list)
    df_silos = pd.DataFrame(silos_list)
    df_readings = pd.DataFrame(readings_list)
    df_alertas = pd.DataFrame(alertas_list)
    df_calibracoes = pd.DataFrame(calibracoes_list)
    
    # Formata datas
    for df in [df_readings, df_alertas, df_calibracoes]:
        if not df.empty:
            date_col = "data_leitura" if "data_leitura" in df.columns else ("data_alerta" if "data_alerta" in df.columns else "data_calibracao")
            df["data_leitura_dt"] = df[date_col].apply(parse_iso_datetime)
            
    return df_lotes, df_silos, df_readings, df_alertas, df_calibracoes, using_supabase

def main():
    st.set_page_config(page_title="Monitoramento de Silos - Agrisolus", layout="wide", initial_sidebar_state="expanded")
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    
    # Título do Header principal
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #334155; padding-bottom: 10px; margin-bottom: 25px;">
            <div>
                <h1 style="color: #38bdf8; margin: 0; font-size: 32px;">📊 Agrisolus Scraper</h1>
                <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 14px;">Pilares: Comunicação Eficiente, Processos Otimizados & Tecnologia Habilitadora</p>
            </div>
            <div style="text-align: right;">
                <span style="background-color: #1e293b; border: 1px solid #334155; color: #38bdf8; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    Aviário 819
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Carregamento dos dados
    df_lotes, df_silos, df_readings, df_alertas, df_calibracoes, using_supabase = load_dashboard_data()
    
    # Sidebar
    st.sidebar.markdown("### ⚙️ Configurações & Filtros")
    status_db = "Online (Supabase) 🟢" if using_supabase else "Offline (SQLite Fallback) 🟡"
    st.sidebar.info(f"**Banco de Dados:**\n{status_db}")
    
    if df_lotes.empty:
        st.warning("⚠️ Nenhum dado encontrado. Por favor, execute o scraper pelo menos uma vez para popular o banco de dados.")
        st.info("Execute: `scripts/run_cron.sh` para buscar dados do portal Agrisolus.")
        return
        
    # Exibe informações do Lote na Sidebar
    lote_info = df_lotes.iloc[0]
    st.sidebar.markdown(f"""
    **Informações do Lote:**
    - **Lote:** {lote_info.get('codigo_lote', 'N/A')}
    - **Aviário:** {lote_info.get('aviario', 'N/A')}
    - **Empresa:** {lote_info.get('empresa', 'N/A')}
    - **Linhagem:** {lote_info.get('linhagem', 'N/A')}
    - **Alojamento:** {int(lote_info.get('qtd_alojamento', 0)):,} aves
    - **Saldo:** {int(lote_info.get('saldo_frangos', 0)):,} aves
    """)
    
    # Seleção de silos
    silos_disponiveis = ["Todos"] + list(df_silos["id_silo"].unique())
    selected_silo = st.sidebar.selectbox("Filtrar por Silo", silos_disponiveis)
    
    # Filtro de Leituras
    df_filtered_readings = df_readings.copy()
    if selected_silo != "Todos":
        df_filtered_readings = df_filtered_readings[df_filtered_readings["silo_id"] == selected_silo]
        
    if df_filtered_readings.empty:
        st.warning(f"Sem leituras registradas para o filtro selecionado.")
        return
        
    # KPIs do Dashboard
    st.markdown("### 📈 Indicadores Chave (Últimas 24 horas)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Silo Selecionado / Status
    with col1:
        # Pega a última leitura
        latest_r = df_filtered_readings.iloc[0]
        latest_time = latest_r["data_leitura_dt"]
        diff_hours = (datetime.now() - latest_time).total_seconds() / 3600.0
        
        status_text = "Online 🟢" if diff_hours <= 2.0 else "Offline 🔴"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Status de Envio</div>
            <div class="metric-value" style="color: {'#10b981' if diff_hours <= 2.0 else '#ef4444'}">{status_text}</div>
            <div class="metric-sub">Última leitura: {latest_time.strftime('%d/%m %H:%M')} ({diff_hours:.1f}h atrás)</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. Saldo de Ração Atual
    with col2:
        if selected_silo == "Todos":
            # Soma do saldo mais recente de cada silo
            silo_latest = df_readings.groupby("silo_id").first().reset_index()
            saldo_atual_kg = silo_latest["valor_racao_kg"].sum()
        else:
            saldo_atual_kg = latest_r["valor_racao_kg"]
            
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Saldo Total de Ração</div>
            <div class="metric-value">{saldo_atual_kg:,.2f} kg</div>
            <div class="metric-sub">{(saldo_atual_kg / 1000.0):.2f} toneladas</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 3. Consumo 24h
    with col3:
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        readings_24h = df_filtered_readings[df_filtered_readings["data_leitura_dt"] >= yesterday]
        consumo_24h = readings_24h["consumo_kg"].sum()
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Consumo (Últimas 24h)</div>
            <div class="metric-value">{consumo_24h:,.2f} kg</div>
            <div class="metric-sub">Soma de quedas de nível registradas</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 4. SLA de Conectividade 24h
    with col4:
        # SLA = (leituras recebidas nas últimas 24h / 24h esperadas) * 100
        # Se for "Todos", tiramos a média de leituras por silo
        num_silos = len(df_silos) if selected_silo == "Todos" else 1
        expected_readings = 24 * num_silos
        actual_readings = len(readings_24h["data_leitura"].unique())
        sla_perc = min(100.0, (actual_readings / expected_readings) * 100.0) if expected_readings > 0 else 0.0
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">SLA Conectividade (24h)</div>
            <div class="metric-value">{sla_perc:.1f}%</div>
            <div class="metric-sub">Meta recomendada: 95.0%</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Gráficos
    st.markdown("### 📊 Gráficos de Comportamento")
    
    # 1. Curva de Nível de Ração (Plotly)
    # Filtra para os últimos 7 dias para melhor visualização
    seven_days_ago = datetime.now() - timedelta(days=7)
    df_chart = df_filtered_readings[df_filtered_readings["data_leitura_dt"] >= seven_days_ago].copy()
    
    fig_line = px.line(
        df_chart,
        x="data_leitura_dt",
        y="valor_racao_kg",
        color="silo_id",
        title="Curva de Saldo de Ração (kg) - Últimos 7 dias",
        labels={"data_leitura_dt": "Data/Hora", "valor_racao_kg": "Quantidade (kg)", "silo_id": "Silo"},
        template="plotly_dark",
        color_discrete_sequence=["#38bdf8", "#fbbf24"]
    )
    fig_line.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8")
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    # 2. Consumo Diário
    df_chart["data_dia"] = df_chart["data_leitura_dt"].dt.date
    df_cons_daily = df_chart.groupby(["data_dia", "silo_id"])["consumo_kg"].sum().reset_index()
    
    fig_bar = px.bar(
        df_cons_daily,
        x="data_dia",
        y="consumo_kg",
        color="silo_id",
        barmode="group",
        title="Consumo Diário de Ração (kg) - Últimos 7 dias",
        labels={"data_dia": "Data", "consumo_kg": "Consumo (kg)", "silo_id": "Silo"},
        template="plotly_dark",
        color_discrete_sequence=["#06b6d4", "#fb923c"]
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8")
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Seções de Alertas e Calibrações
    st.markdown("---")
    c_alert, c_cal = st.columns(2)
    
    with c_alert:
        st.markdown("### 🚨 Histórico de Alertas Recentes")
        if df_alertas.empty:
            st.info("Nenhum alerta registrado no lote.")
        else:
            df_alert_view = df_alertas[["data_leitura_dt", "tipo_alerta_str", "mensagem"]].copy()
            df_alert_view.columns = ["Data/Hora", "Tipo", "Mensagem"]
            st.dataframe(df_alert_view, use_container_width=True, height=250)
            
    with c_cal:
        st.markdown("### 🔧 Últimas Calibrações Realizadas")
        if df_calibracoes.empty:
            st.info("Nenhuma calibração registrada no lote.")
        else:
            df_cal_view = df_calibracoes[["data_leitura_dt", "numero_serial", "zona_str", "idade"]].copy()
            df_cal_view.columns = ["Data/Hora", "Nº Serial", "Zona", "Idade (Dias)"]
            st.dataframe(df_cal_view, use_container_width=True, height=250)

if __name__ == "__main__":
    main()
