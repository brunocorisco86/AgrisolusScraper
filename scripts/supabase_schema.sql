-- Script de Criação das Tabelas no Supabase (PostgreSQL)
-- Copie todo este código e cole no SQL Editor do painel do seu Supabase para criar a estrutura do banco.

-- 1. Tabela de Lotes
CREATE TABLE IF NOT EXISTS lotes (
    id_lote BIGINT PRIMARY KEY,
    codigo_lote VARCHAR(50),
    empresa VARCHAR(255),
    estabelecimento VARCHAR(255),
    aviario VARCHAR(255),
    linhagem VARCHAR(100),
    qtd_alojamento INTEGER,
    data_alojamento TIMESTAMP WITH TIME ZONE,
    saldo_frangos INTEGER,
    aviario_lote VARCHAR(255) UNIQUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabela de Silos
CREATE TABLE IF NOT EXISTS silos (
    id_silo VARCHAR(100) PRIMARY KEY,
    lote_id BIGINT REFERENCES lotes(id_lote) ON DELETE CASCADE,
    capacidade_kg NUMERIC(10, 2)
);

-- 3. Tabela de Leituras (Registra o histórico de saldo de ração e consumo)
CREATE TABLE IF NOT EXISTS leituras (
    id SERIAL PRIMARY KEY,
    silo_id VARCHAR(100) REFERENCES silos(id_silo) ON DELETE CASCADE,
    data_leitura TIMESTAMP WITH TIME ZONE NOT NULL,
    valor_racao_g NUMERIC(15, 4),
    valor_racao_kg NUMERIC(12, 4),
    consumo_kg NUMERIC(12, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Impede inserções de leituras duplicadas para o mesmo silo no mesmo instante de tempo
    CONSTRAINT unique_silo_leitura UNIQUE (silo_id, data_leitura)
);

-- 4. Tabela de Alertas (Histórico de alertas extraídos ou gerados)
CREATE TABLE IF NOT EXISTS alertas (
    id SERIAL PRIMARY KEY,
    lote_id BIGINT REFERENCES lotes(id_lote) ON DELETE CASCADE,
    tipo_alerta INTEGER,
    tipo_alerta_str VARCHAR(100),
    data_alerta TIMESTAMP WITH TIME ZONE NOT NULL,
    mensagem TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Impede alertas duplicados no mesmo instante para o mesmo lote
    CONSTRAINT unique_lote_alerta UNIQUE (lote_id, data_alerta)
);

-- 5. Tabela de Calibrações (Registro de calibrações de balança/silo)
CREATE TABLE IF NOT EXISTS calibracoes (
    id SERIAL PRIMARY KEY,
    lote_id BIGINT REFERENCES lotes(id_lote) ON DELETE CASCADE,
    numero_serial VARCHAR(100),
    zona INTEGER,
    zona_str VARCHAR(100),
    data_calibracao TIMESTAMP WITH TIME ZONE NOT NULL,
    idade INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Impede calibrações duplicadas para o mesmo lote no mesmo instante
    CONSTRAINT unique_lote_calibracao UNIQUE (lote_id, data_calibracao)
);
