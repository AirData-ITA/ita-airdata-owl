import os
import argparse
from bs4 import BeautifulSoup

def process_widoco_html(html_file):
    if not os.path.exists(html_file):
        print(f"Arquivo {html_file} não encontrado.")
        return

    print(f"Processando HTML do WIDOCO: {html_file}...")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # 1. Remover Iframe e Div de Visualização
    iframe = soup.find('iframe', src=lambda x: x and 'webvowl' in x)
    if iframe:
        iframe.decompose()
        print("Iframe removido.")

    div_viz = soup.find('div', id='visualization')
    if div_viz:
        div_viz.decompose()
        print("Div visualization removida.")

    link_viz = soup.find('a', href='#visualization')
    if link_viz:
        parent = link_viz.find_parent('li')
        if parent: parent.decompose()
        else: link_viz.decompose()

    # 2. Forçar target="_blank" em links para o WebVOWL (Badges, etc)
    # Procura qualquer link que contenha "webvowl" no href
    for a in soup.find_all('a', href=True):
        if 'webvowl' in a['href']:
            a['target'] = '_blank'
            print(f"Adicionado target='_blank' ao link: {a['href']}")

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Processamento de {os.path.basename(html_file)} concluído.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove o iframe do WebVOWL e ajusta links em documentação WIDOCO.")
    parser.add_argument('--html-file', required=True, help='Caminho para o arquivo HTML a ser processado.')
    
    args = parser.parse_args()
    
    process_widoco_html(args.html_file)
