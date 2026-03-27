import os
import argparse
from bs4 import BeautifulSoup

# ONTOLOGY_BASE = "http://airdata.org/ontology" (Hardcoded, pois é específico da ontologia)

def fix_html_links(html_file, ontology_base="http://airdata.org/ontology"):
    if not os.path.exists(html_file):
        print(f"Arquivo {html_file} não encontrado.")
        return

    print(f"Corrigindo links externos em {html_file}...")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Encontra todos os links que começam com a base da ontologia
    # e que NÃO são âncoras locais (não começam com #)
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Se o link aponta para o domínio fictício
        if href.startswith(ontology_base):
            # Opção A: Transformar em âncora local se tiver # (ex: ...ontology#Flight -> #Flight)
            if '#' in href:
                anchor = href.split('#')[1]
                a['href'] = '#' + anchor
                # Adiciona uma classe para podermos estilizar se quiser
                a['class'] = a.get('class', []) + ['fixed-local-link']
            else:
                # Opção B: Se for só a base, remove o link (transforma em span)
                new_tag = soup.new_tag("span")
                new_tag.string = a.text
                new_tag['class'] = "iri-text"
                a.replace_with(new_tag)

    # Salva o arquivo corrigido
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Links em {os.path.basename(html_file)} corrigidos com sucesso!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corrige links em documentação de ontologia gerada pelo WIDOCO.")
    parser.add_argument('--html-file', required=True, help='Caminho para o arquivo HTML a ser corrigido.')
    
    args = parser.parse_args()
    
    fix_html_links(args.html_file)
