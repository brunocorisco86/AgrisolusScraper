from bs4 import BeautifulSoup

import os
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch_details.html")

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "lxml")

print("=== INFORMAÇÕES GERAIS ===")
print(f"Título da página: {soup.title.text.strip() if soup.title else 'Sem título'}")

print("\n=== CABEÇALHOS (Headers) ===")
for h in ["h1", "h2", "h3", "h4", "h5", "h6"]:
    elements = soup.find_all(h)
    if elements:
        print(f"\n{h.upper()}:")
        for el in elements[:10]: # mostrar os primeiros 10
            print(f"  - {el.text.strip()}")

print("\n=== TABELAS ENCONTRADAS ===")
tables = soup.find_all("table")
print(f"Total de tabelas: {len(tables)}")
for i, table in enumerate(tables):
    print(f"\nTabela {i+1}:")
    # Mostrar id, class e headers (th) da tabela
    print(f"  ID: {table.get('id')}, Class: {table.get('class')}")
    headers = [th.text.strip() for th in table.find_all("th")]
    print(f"  Headers: {headers}")
    
    # Mostrar primeiras duas linhas da tabela
    rows = table.find_all("tr")
    print(f"  Número de linhas: {len(rows)}")
    for r_idx, row in enumerate(rows[1:3]): # tr[0] geralmente é o header, pegamos tr[1] e tr[2]
        cells = [td.text.strip() for td in row.find_all("td")]
        print(f"    Linha {r_idx+1}: {cells}")

print("\n=== CARD OU LABELS COM TEXTO CHAVE ===")
# Procurar divs ou labels que contenham palavras como "Lote", "Silo", "Ração", "Saldo", "Consumo"
for word in ["Lote", "Silo", "Ração", "Saldo", "Consumo", "Idade", "Linhagem", "Produtor"]:
    elements = soup.find_all(lambda tag: tag.name in ["div", "span", "label", "p", "td", "th"] and word.lower() in tag.text.lower())
    print(f"Palavra '{word}': {len(elements)} ocorrências")
    # Mostrar as 3 primeiras ocorrências com conteúdo curto
    count = 0
    for el in elements:
        text = el.text.strip().replace("\n", " ").replace("  ", " ")
        if len(text) < 150 and len(text) > 0:
            print(f"  - [{el.name}]: {text[:100]}")
            count += 1
            if count >= 3:
                break
