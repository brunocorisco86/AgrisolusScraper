import re
import json

file_path = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/batch_details.html"

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Função auxiliar para extrair e fazer parse de variáveis Javascript que contêm JSON
def extract_js_var(var_name, html):
    # Regex para capturar a atribuição da variável
    pattern = r'var\s+' + re.escape(var_name) + r'\s*=\s*([\[\{].*?[\]\}]);'

    match = re.search(pattern, html, re.DOTALL)
    if match:
        var_content = match.group(1)
        try:
            return json.loads(var_content)
        except Exception as e:
            # Se falhar, tenta limpar comentários ou pontuação extra (caso haja)
            # Para o nosso teste, as variáveis parecem ser JSON puro
            print(f"Erro ao decodificar JSON para {var_name}: {e}")
            return var_content
    return None

lotes_data = extract_js_var("lotes", html_content)
saldo_racao_data = extract_js_var("saldoRacao", html_content)

print("=== DETALHES DE 'lotes' ===")
if lotes_data:
    print(json.dumps(lotes_data, indent=2, ensure_ascii=False))
else:
    print("Variável 'lotes' não encontrada.")

print("\n=== DETALHES DE 'saldoRacao' ===")
if saldo_racao_data:
    print(json.dumps(saldo_racao_data, indent=2, ensure_ascii=False))
else:
    print("Variável 'saldoRacao' não encontrada.")
