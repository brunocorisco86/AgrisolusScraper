import re
import json

file_path = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/listagem.html"

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Procura a variável JavaScript 'lotes'
pattern = r'var\s+lotes\s*=\s*([\[\{].*?[\]\}]);'
match = re.search(pattern, html_content, re.DOTALL)
if match:
    var_content = match.group(1)
    try:
        lotes_data = json.loads(var_content)
        print(f"✅ SUCESSO: Variável 'lotes' encontrada na listagem! Contém {len(lotes_data)} lotes.")
        # Imprime o primeiro lote como exemplo
        if lotes_data:
            print("\nExemplo do primeiro lote mapeado:")
            print(json.dumps(lotes_data[0], indent=2, ensure_ascii=False))
            
            # Salva o JSON estruturado para lotes_config.json conforme pedido em docs/GerarJson.md
            # Vamos estruturar conforme docs/GerarJson.md:
            # { "EMPRESA", "ESTABELECIMENTO", "AVIARIO", "LOTE", "LINHAGEM", "IDADE", "LINK" }
            lotes_formatados = []
            for lote in lotes_data:
                # Constrói o link de detalhes
                id_lote = lote.get("IdLote")
                link_detalhes = f"https://s2.agrisolus.com.br/Home/Detalhes?idLote={id_lote}"
                
                lotes_formatados.append({
                    "EMPRESA": lote.get("Empresa"),
                    "ESTABELECIMENTO": lote.get("Estabelecimento"),
                    "AVIARIO": lote.get("Aviario"),
                    "LOTE": int(lote.get("CodigoLote", 0)) if lote.get("CodigoLote") else None,
                    "LINHAGEM": lote.get("Linhagem"),
                    "IDADE": lote.get("Idade"),
                    "LINK": link_detalhes
                })
            
            config_file = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/lotes_config.json"
            with open(config_file, "w", encoding="utf-8") as out:
                json.dump(lotes_formatados, out, indent=4, ensure_ascii=False)
            print(f"\n✅ lotes_config.json gerado e salvo em: {config_file}")
            print(f"Primeiro item do config:")
            print(json.dumps(lotes_formatados[0], indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"❌ Erro ao decodificar JSON de lotes: {e}")
else:
    print("❌ Variável 'lotes' não encontrada na listagem.")
