# -*- coding: utf-8 -*-
"""
API REST para o monitoramento de silos e integração com o front-end / agente Hermes.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional
import sqlite3

from src.analysis.silo_analyzer import SiloAnalyzer
from src.database.connection import DatabaseConnection
from src.utils.logger import setup_logger

logger = setup_logger(name="api_server", log_file="test_run.log")

app = FastAPI(
    title="Agrisolus Silo Monitor API",
    description="API REST para monitoramento de volume de silos, consumo de ração e acurácia de sensores.",
    version="1.0.0"
)

# Habilita CORS para permitir comunicação com o front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvoiceCreate(BaseModel):
    data_nf: str = Field(..., description="Data da nota fiscal (YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD)", example="2026-07-14 12:00:00")
    numero_nf: str = Field(..., description="Número único da Nota Fiscal", example="123456")
    quantidade_kg: float = Field(..., description="Quantidade de ração entregue em kg", example=5000.0)

# Inicializa o analisador usando o banco padrão do .env
analyzer = SiloAnalyzer()

@app.get("/")
def read_root():
    return {"message": "Agrisolus Silo Monitor API está ativa e operando."}

@app.post("/api/invoices", status_code=201)
def add_invoice(invoice: InvoiceCreate):
    success = analyzer.insert_nota_fiscal(invoice.data_nf, invoice.numero_nf, invoice.quantidade_kg)
    if not success:
        raise HTTPException(status_code=400, detail="Erro ao inserir nota fiscal. Verifique se o número é único e a data é válida.")
    return {"status": "success", "message": f"Nota Fiscal {invoice.numero_nf} inserida com sucesso."}

@app.get("/api/invoices")
def list_invoices():
    return analyzer.get_invoices()

@app.get("/api/silos/{silo_id}/analysis")
def get_silo_analysis(
    silo_id: str,
    window: int = Query(3, description="Tamanho da janela de suavização"),
    threshold: float = Query(400.0, description="Limite em kg para detectar abastecimento")
):
    try:
        analysis = analyzer.analyze_silo(silo_id, smoothing_window=window, load_threshold=threshold)
        return analysis
    except Exception as e:
        logger.error(f"Erro na rota de análise do silo {silo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/silos/{silo_id}/accuracy")
def get_silo_accuracy(
    silo_id: str,
    hours: int = Query(24, description="Janela temporal de busca em horas"),
    window: int = Query(3, description="Tamanho da janela de suavização"),
    threshold: float = Query(400.0, description="Limite em kg para detectar abastecimento")
):
    try:
        accuracy_report = analyzer.evaluate_sensor_accuracy(
            silo_id,
            window_hours=hours,
            smoothing_window=window,
            load_threshold=threshold
        )
        return accuracy_report
    except Exception as e:
        logger.error(f"Erro na rota de acurácia do silo {silo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """
    Retorna o status geral de ocupação, taxas de esvaziamento, e forecasts para todos os silos.
    """
    db_conn = DatabaseConnection()
    conn = db_conn.get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        # Busca todas as informações de silos e seus lotes associados
        cursor.execute("""
            SELECT s.id_silo, s.capacidade_kg, l.empresa, l.estabelecimento, l.aviario
            FROM silos s
            JOIN lotes l ON s.lote_id = l.id_lote
        """)
        silos_rows = cursor.fetchall()
        
        silos_stats = []
        total_capacity = 0.0
        total_current_weight = 0.0
        
        for row in silos_rows:
            silo_id, capacity, empresa, estabelecimento, aviario = row
            total_capacity += capacity
            
            # Pega o último registro de leitura de peso para o silo
            cursor.execute("""
                SELECT valor_racao_kg, data_leitura
                FROM leituras
                WHERE silo_id = ?
                ORDER BY data_leitura DESC
                LIMIT 1
            """, (silo_id,))
            latest_read = cursor.fetchone()
            
            current_weight = latest_read[0] if latest_read else 0.0
            last_reading_date = latest_read[1] if latest_read else None
            total_current_weight += current_weight
            
            # Calcula ocupação
            occupancy_pct = (current_weight / capacity) * 100.0 if capacity > 0 else 0.0
            
            # Calcula consumo diário médio (últimos 7 dias) para fazer forecast
            analysis = analyzer.analyze_silo(silo_id, smoothing_window=3)
            daily_cons = analysis.get("daily_consumption", {})
            
            # Pega as chaves de consumo diário ordenadas por data
            days = sorted(daily_cons.keys())
            last_7_days = days[-7:] if len(days) >= 7 else days
            
            avg_daily_consumption = 0.0
            if last_7_days:
                total_cons_7_days = sum(daily_cons[d] for d in last_7_days)
                avg_daily_consumption = total_cons_7_days / len(last_7_days)
            else:
                # Fallback: Se não houver histórico de consumo mapeado, tenta inferir de leituras locais
                avg_daily_consumption = 0.0
                
            # Forecast (dias restantes)
            days_remaining = None
            forecast_depletion_date = None
            if avg_daily_consumption > 5.0 and current_weight > 0.0:  # Consumo mínimo de 5kg/dia para forecast
                days_remaining = current_weight / avg_daily_consumption
                # Calcula data estimada
                est_dt = datetime.now() + timedelta(days=days_remaining)
                forecast_depletion_date = est_dt.strftime("%Y-%m-%d")
            
            silos_stats.append({
                "silo_id": silo_id,
                "capacidade_kg": capacity,
                "peso_atual_kg": round(current_weight, 2),
                "porcentagem_ocupacao": round(occupancy_pct, 1),
                "data_ultima_leitura": last_reading_date,
                "empresa": empresa,
                "estabelecimento": estabelecimento,
                "aviario": aviario,
                "consumo_diario_medio_kg": round(avg_daily_consumption, 2),
                "dias_restantes": round(days_remaining, 1) if days_remaining is not None else None,
                "previsao_esvaziamento": forecast_depletion_date
            })
            
        total_occupancy_pct = (total_current_weight / total_capacity) * 100.0 if total_capacity > 0 else 0.0
        
        return {
            "silos": silos_stats,
            "total_capacidade_kg": round(total_capacity, 2),
            "total_peso_atual_kg": round(total_current_weight, 2),
            "total_ocupacao_pct": round(total_occupancy_pct, 1)
        }
    except Exception as e:
        logger.error(f"Erro ao carregar estatísticas do dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

from fastapi.staticfiles import StaticFiles

# Serve as imagens dos logotipos
app.mount("/images", StaticFiles(directory="images"), name="images")

# Serve o frontend estático HTML na raiz do servidor
app.mount("/", StaticFiles(directory="src/api/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
