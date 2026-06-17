from bs4 import BeautifulSoup
import re

file_path = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/listagem.html"

with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

print("=== 1. ESTRUTURA DE TABELAS ===")
tables = soup.find_all("table")
for i, table in enumerate(tables):
    print(f"Table {i+1}: ID={table.get('id')}, Class={table.get('class')}")
    # Ver se há tr, thead, tbody
    thead = table.find("thead")
    tbody = table.find("tbody")
    print(f"  - Has thead: {thead is not None}, Has tbody: {tbody is not None}")
    if thead:
        headers = [th.text.strip() for th in thead.find_all(["th", "td"])]
        print(f"  - Headers in thead: {headers}")

print("\n=== 2. ANÁLISE DE SCRIPTS INLINE (AJAX / URL) ===")
scripts = soup.find_all("script")
print(f"Total de scripts: {len(scripts)}")
for idx, s in enumerate(scripts):
    content = s.string if s.string else ""
    if not content:
        continue
    
    # Procurar por URLs ou chamadas ajax
    keywords = ["url", "ajax", "datatables", "post", "get", "lote", "listagem", "json"]
    found = [kw for kw in keywords if kw in content.lower()]
    if found:
        print(f"  Script {idx+1} (Inline): contém {found}")
        # Mostrar as linhas que contêm chamadas ou URLs
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ["url:", "ajax", "data:", "type:", "http", "api"]):
                print(f"    L{i+1}: {line.strip()}")
