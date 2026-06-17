from bs4 import BeautifulSoup
import re

file_path = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/batch_details.html"

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "lxml")

print("=== 1. TABELA 1: DADOS GERAIS DO PRODUTOR/LOTE ===")
table1 = soup.find("table", class_=lambda x: x and "col-lg-12" in x)
if table1:
    for idx, row in enumerate(table1.find_all("tr")):
        cells = [td.text.strip().replace("\xa0", " ") for td in row.find_all(["td", "th"])]
        print(f"Row {idx+1}: {cells}")
else:
    print("Tabela 1 não encontrada.")

print("\n=== 2. LOCALIZANDO SILOS E SALDO DE RAÇÃO ===")
# Os silos aparecem como H2 com "Silo-" no texto. Vamos encontrar esses elementos e seus valores
silo_headers = soup.find_all(lambda tag: tag.name == "h2" and tag.text and "Silo-" in tag.text)
for sh in silo_headers:
    # Ver o elemento pai e elementos próximos para entender como o saldo de ração está associado a ele
    print(f"\nSilo Header: '{sh.text.strip()}'")
    parent = sh.parent
    # Imprimir o texto de todo o container pai
    parent_text = parent.text.strip().replace("\n", " ").replace("  ", " ")
    print(f"  Container Text: {parent_text[:300]}")
    # Encontrar H2 vizinho ou elementos com o saldo de ração
    h2s = parent.find_all("h2")
    print(f"  H2s no container: {[h.text.strip() for h in h2s]}")

print("\n=== 3. ANÁLISE DOS SCRIPTS (AJAX / CARREGAMENTO DINÂMICO) ===")
# Procurar por URLs de requisições nos scripts
scripts = soup.find_all("script")
print(f"Total de tags <script>: {len(scripts)}")
for idx, script in enumerate(scripts):
    content = script.string if script.string else ""
    if not content:
        src = script.get("src")
        if src:
            print(f"  Script {idx+1} (External): src={src}")
        continue
    
    # Procurar palavras interessantes no conteúdo do script
    keywords = ["alerta", "calibrac", "ajax", "chart", "url", "post", "get", "json", "silo"]
    found_kws = [kw for kw in keywords if kw in content.lower()]
    if found_kws:
        print(f"  Script {idx+1} (Inline): contém palavras {found_kws}")
        # Se contiver termos de requisição para alertas ou calibrações, mostrar trechos do script
        if any(kw in content.lower() for kw in ["alerta", "calibrac", "ajax"]):
            lines = content.split("\n")
            matching_lines = [f"    L{i+1}: {line.strip()}" for i, line in enumerate(lines) if any(kw in line.lower() for kw in ["alerta", "calibrac", "ajax", "url", "data:"])]
            print("\n".join(matching_lines[:15])) # Limitar a 15 linhas
            print("  " + "-"*40)
