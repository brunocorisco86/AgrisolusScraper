from bs4 import BeautifulSoup
import re
import json

file_path = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/batch_details.html"

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "lxml")

print("=== TENTANDO EXTRAIR TABELA 1 INTEIRA ===")
table1 = soup.find("table", class_=lambda x: x and "col-lg-12" in x)
if table1:
    for r_idx, row in enumerate(table1.find_all("tr")):
        cells = [td.text.strip().replace("\xa0", " ").replace("\n", " ").replace("  ", " ") for td in row.find_all(["td", "th"])]
        print(f"Row {r_idx+1}: {cells}")

print("\n=== PROCURANDO VARIÁVEIS JAVASCRIPT IMPORTANTES ===")
scripts = soup.find_all("script")
for idx, script in enumerate(scripts):
    content = script.string if script.string else ""
    if not content:
        continue
    
    # Encontrar declarações de variáveis interessantes
    # Padrão: var nome_variavel = [ ... ]; ou var nome_variavel = { ... };
    pattern = r'var\s+([a-zA-Z0-9_]+)\s*=\s*([\[\{].*?[\]\}]);'
    matches = re.finditer(pattern, content, re.DOTALL)
    for match in matches:
        var_name = match.group(1)
        var_value = match.group(2)
        # Limitar a exibição do valor
        val_clean = var_value.replace("\n", " ").replace("  ", " ")
        if len(val_clean) > 150:
            val_clean = val_clean[:150] + "..."
        print(f"Encontrada var '{var_name}': {val_clean}")
        
        # Se for alertas, calibracoes ou outras séries interessantes, tentar imprimir o JSON estruturado completo ou os primeiros elementos
        if var_name in ["alertas", "calibracoes", "serieRacao", "serieSilo", "pesos", "serieConsumoRacao", "silos"]:
            try:
                # Tentar fazer o parse do JSON para ver se é válido
                parsed = json.loads(var_value)
                print(f"  -> Contém {len(parsed)} elementos. Exemplo do primeiro elemento:")
                if len(parsed) > 0:
                    print(f"     {parsed[0]}")
            except Exception as e:
                # Se não for JSON estrito (por exemplo, pode conter datas ou funções JS), apenas extrair uma amostra
                print(f"  -> Não é JSON puro ou falhou ao analisar: {e}")
                print(f"     Amostra: {var_value[:300]}...")
