# 🤖 Instruções de Tool Calling para o Agente Hermes (VPS)

Este documento descreve como o agente autônomo **Hermes** estabelecido na VPS pode interagir com o monitor de silos via chamadas de ferramentas (*tool calling*), seja por meio de scripts CLI ou chamadas de API HTTP.

---

## 🔌 Modos de Integração (CLI vs REST API)

O Hermes pode interagir com o sistema de duas formas:
1. **Via CLI (Recomendado na VPS):** Executando o script wrapper `./scripts/analyze_silos.sh`.
2. **Via REST API (HTTP):** Enviando requisições JSON para a porta `8000` (FastAPI).

---

## 📋 Cenários de Tool Calling & Fluxos de Automação

### 1. Monitoramento Periódico de Abastecimento (Carregamentos)
* **Objetivo:** O Hermes deve buscar periodicamente (ex: a cada 1 hora) se houve novos carregamentos de ração no silo e notificar o usuário.
* **Ação do Agente:**
  * O agente executa a chamada:
    ```bash
    ./scripts/analyze_silos.sh analyze --silo Silo-819-01 --window 3 --threshold 400
    ```
    *Ou via API:* `GET /api/silos/Silo-819-01/analysis?window=3&threshold=400`
  * **Tratamento:** O agente armazena o timestamp do último carregamento visto. Se o JSON retornar um novo item no array `"loadings"`, ele formata um alerta: *"🚨 Novo carregamento detectado no Silo 1! Quantidade registrada pelo sensor: +X.X kg em YYYY-MM-DD HH:MM."*

---

### 2. Registro de Nota Fiscal & Auditoria Imediata de Acurácia
* **Objetivo:** Registrar as Notas Fiscais de Entrada enviadas pelo usuário e auditar imediatamente a acurácia do sensor físico.
* **Fluxo Conversacional:**
  1. O usuário diz: *"Hermes, chegou uma entrega de 5000 kg de ração hoje, nota fiscal número 8493."*
  2. O Hermes executa a ferramenta de inserção da NF:
     ```bash
     ./scripts/analyze_silos.sh add-invoice --numero "8493" --qtd 5000.0 --data "2026-07-14 12:00:00"
     ```
     *Ou via API:* `POST /api/invoices` com JSON `{"data_nf": "2026-07-14 12:00:00", "numero_nf": "8493", "quantidade_kg": 5000.0}`
  3. Imediatamente após registrar a NF, o Hermes executa a auditoria de acurácia:
     ```bash
     ./scripts/analyze_silos.sh accuracy --silo Silo-819-01 --hours 24
     ```
     *Ou via API:* `GET /api/silos/Silo-819-01/accuracy?hours=24`
  4. **Resposta do Agente:** O Hermes extrai o resultado do relatório e responde:
     > *"Perfeito! Registrei a Nota Fiscal nº 8493 (5.000 kg). O sensor do Silo 1 registrou um carregamento correspondente de **4.950 kg** às 11:30 (janela de ±24h). A acurácia calculada para este abastecimento é de **99.0%** (desvio de apenas -50 kg)."*

---

## 🛠️ Definição das Ferramentas (Schemas para JSON Schema Tool Calling)

Se o seu Hermes Agent utiliza definições estruturadas de ferramentas (como OpenAI Functions ou LangChain Tools), configure as seguintes definições:

```json
[
  {
    "name": "add_feed_invoice",
    "description": "Registra uma Nota Fiscal de Entrada de ração no banco do silo.",
    "parameters": {
      "type": "object",
      "properties": {
        "numero_nf": {
          "type": "string",
          "description": "O número único identificador da Nota Fiscal de Entrada."
        },
        "quantidade_kg": {
          "type": "number",
          "description": "Quantidade de ração entregue em quilogramas (kg)."
        },
        "data_nf": {
          "type": "string",
          "description": "Data e hora aproximada da entrega da ração no formato YYYY-MM-DD HH:MM:SS."
        }
      },
      "required": ["numero_nf", "quantidade_kg", "data_nf"]
    }
  },
  {
    "name": "check_silo_accuracy",
    "description": "Avalia o nível de acurácia do sensor de peso do silo comparando as cargas físicas reais registradas em nota com as detectadas pelo sensor.",
    "parameters": {
      "type": "object",
      "properties": {
        "silo_id": {
          "type": "string",
          "description": "ID do silo para verificação de acurácia (ex: 'Silo-819-01' ou 'Silo-819-02')."
        },
        "window_hours": {
          "type": "integer",
          "description": "Janela em horas ao redor da data da nota fiscal para procurar o evento de carga correspondente no sensor. Padrão: 24."
        }
      },
      "required": ["silo_id"]
    }
  }
]
```
