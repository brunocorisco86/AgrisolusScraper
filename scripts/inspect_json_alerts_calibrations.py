import re
import json

file_path = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/batch_details.html"

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

def extract_js_var(var_name, html):
    pattern = r'var\s+' + re.escape(var_name) + r'\s*=\s*([\[\{].*?[\]\}]);'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        var_content = match.group(1)
        try:
            return json.loads(var_content)
        except Exception as e:
            print(f"Erro ao decodificar JSON para {var_name}: {e}")
            return var_content
    return None

alertas_data = extract_js_var("alertas", html_content)
calibracoes_data = extract_js_var("calibracoes", html_content)

print("=== DETALHES DE 'alertas' (Primeiros 3 elementos) ===")
if alertas_data:
    print(f"Total de alertas encontrados: {len(alertas_data)}")
    print(json.dumps(alertas_data[:3], indent=2, ensure_ascii=False))
else:
    print("Variável 'alertas' não encontrada.")

print("\n=== DETALHES DE 'calibracoes' (Primeiros 3 elementos) ===")
if calibracoes_data:
    print(f"Total de calibrações encontradas: {len(calibracoes_data)}")
    print(json.dumps(calibracoes_data[:3], indent=2, ensure_ascii=False))
else:
    print("Variável 'calibracoes' não encontrada.")
