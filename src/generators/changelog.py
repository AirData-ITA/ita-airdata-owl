import os
import glob
from owlready2 import *
import datetime
import argparse

# Configuração
# OWL_DIR = "../OntoOwl" (removido)
# OUTPUT_FILE = "../OntoSite/changelog.html" (removido)

HTML_TEMPLATE_START = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changelog - AirData Ontology</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; color: #333; min-height: 100vh; display: flex; flex-direction: column; }
        
        /* Navbar (Reusing existing style) */
        .navbar { background: white; padding: 1rem 2rem; border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 1000; }
        .navbar-content { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
        .logo { color: #003C7D; text-decoration: none; display: flex; align-items: center; gap: 0.5rem; }
        .nav-links { display: flex; gap: 2rem; list-style: none; }
        .nav-links a { color: #003C7D; text-decoration: none; font-weight: 500; }

        /* Content */
        .container { max-width: 900px; margin: 3rem auto; padding: 0 1rem; flex: 1; width: 100%; }
        h1 { color: #003C7D; margin-bottom: 2rem; border-bottom: 2px solid #e9ecef; padding-bottom: 1rem; }
        
        .version-card { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 2rem; overflow: hidden; }
        .version-header { background: #003C7D; color: white; padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
        .version-title { font-size: 1.2rem; font-weight: bold; }
        .version-date { font-size: 0.9rem; opacity: 0.9; }
        
        .change-group { padding: 1.5rem; border-bottom: 1px solid #f0f0f0; }
        .change-group:last-child { border-bottom: none; }
        .change-title { font-weight: bold; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        
        .badge { padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
        .badge-added { background: #e6f4ea; color: #1e7e34; }
        .badge-removed { background: #fbe9e7; color: #c62828; }
        .badge-changed { background: #fff3e0; color: #ef6c00; }
        
        .item-list { list-style: none; padding-left: 0.5rem; }
        .item-list li { margin-bottom: 0.5rem; font-family: monospace; font-size: 0.95rem; }
        .item-iri { color: #666; font-size: 0.8rem; margin-left: 0.5rem; }

        .empty-state { padding: 2rem; text-align: center; color: #666; font-style: italic; }
        
        .footer { background: white; padding: 2rem; text-align: center; border-top: 1px solid #eee; margin-top: auto; }
    </style>
</head>
<body>

    <main class="container">
        <h1>Histórico de Mudanças</h1>
"""

HTML_END = """
    </main>
    <footer class="footer">
        <p>© 2026 Projeto AirData - ITA</p>
    </footer>
</body>
</html>
"""

def get_owl_files(owl_dir):
    # Retorna lista de arquivos ordenada por data (mais recente primeiro)
    files = glob.glob(f'{owl_dir}/*.owl')
    files.sort(key=os.path.getctime, reverse=True)
    return files

def get_entities(onto):
    # Retorna um dicionário mapeando IRI para um "fingerprint" da entidade (IRI, label, comment)
    entities = {}

    def add_entity_fingerprint(entity):
        iri = str(entity.iri)
        label = str(entity.label) if hasattr(entity, 'label') else None
        comment = str(entity.comment) if hasattr(entity, 'comment') else None
        
        # Considera a primeira label/comment se houver múltiplos
        if isinstance(label, list):
            label = label[0] if label else None
        if isinstance(comment, list):
            comment = comment[0] if comment else None

        entities[iri] = {
            'iri': iri,
            'label': label,
            'comment': comment
        }

    for cls in onto.classes():
        add_entity_fingerprint(cls)
    for prop in onto.properties():
        add_entity_fingerprint(prop)
    return entities

def compare_versions(new_file, old_file):
    print(f"Comparando: {os.path.basename(new_file)} vs {os.path.basename(old_file)}")
    
    # Carrega as ontologias isoladamente e obtém os fingerprints
    world_new = World()
    onto_new = world_new.get_ontology(new_file).load()
    entities_new_map = get_entities(onto_new)
    
    world_old = World()
    onto_old = world_old.get_ontology(old_file).load()
    entities_old_map = get_entities(onto_old)
    
    # Conjuntos de IRIs para facilitar a comparação
    iris_new = set(entities_new_map.keys())
    iris_old = set(entities_old_map.keys())
    
    # Calcula diferenças
    added_iris = iris_new - iris_old
    removed_iris = iris_old - iris_new
    common_iris = iris_new.intersection(iris_old)
    
    added_entities = [entities_new_map[iri] for iri in added_iris]
    removed_entities = [entities_old_map[iri] for iri in removed_iris]
    changed_entities = []
    
    for iri in common_iris:
        fingerprint_new = entities_new_map[iri]
        fingerprint_old = entities_old_map[iri]
        
        changes = {}
        if fingerprint_new['label'] != fingerprint_old['label']:
            changes['label'] = {
                'old': fingerprint_old['label'],
                'new': fingerprint_new['label']
            }
        if fingerprint_new['comment'] != fingerprint_old['comment']:
            changes['comment'] = {
                'old': fingerprint_old['comment'],
                'new': fingerprint_new['comment']
            }
            
        if changes:
            changed_entities.append({
                'entity': fingerprint_new,
                'changes': changes
            })
            
    return {
        'new_file': os.path.basename(new_file),
        'old_file': os.path.basename(old_file),
        'date': datetime.datetime.fromtimestamp(os.path.getctime(new_file)).strftime('%d/%m/%Y'),
        'added': sorted(added_entities, key=lambda x: x['iri']),
        'removed': sorted(removed_entities, key=lambda x: x['iri']),
        'changed': sorted(changed_entities, key=lambda x: x['entity']['iri'])
    }

def generate_html_card(diff_data):
    html = f"""
        <div class="version-card">
            <div class="version-header">
                <div class="version-title">{diff_data['new_file']}</div>
                <div class="version-date">Comparado com {diff_data['old_file']} • {diff_data['date']}</div>
            </div>
    """
    
    has_changes = False
    
    # Added Section
    if diff_data['added']:
        has_changes = True
        html += """
            <div class="change-group">
                <div class="change-title"><span class="badge badge-added">ADICIONADO</span> Novas Entidades</div>
                <ul class="item-list">
        """
        for entity_data in diff_data['added']:
            name = entity_data['iri'].split('#')[-1]
            html += f'<li>{name} <span class="item-iri">({entity_data["iri"]})</span></li>'
        html += "</ul></div>"

    # Removed Section
    if diff_data['removed']:
        has_changes = True
        html += """
            <div class="change-group">
                <div class="change-title"><span class="badge badge-removed">REMOVIDO</span> Entidades Excluídas</div>
                <ul class="item-list">
        """
        for entity_data in diff_data['removed']:
            name = entity_data['iri'].split('#')[-1]
            html += f'<li>{name} <span class="item-iri">({entity_data["iri"]})</span></li>'
        html += "</ul></div>"
        
    # Changed Section
    if diff_data['changed']:
        has_changes = True
        html += """
            <div class="change-group">
                <div class="change-title"><span class="badge badge-changed">ALTERADO</span> Entidades Modificadas</div>
                <ul class="item-list">
        """
        for change_data in diff_data['changed']:
            entity = change_data['entity']
            changes = change_data['changes']
            name = entity['iri'].split('#')[-1]
            html += f'<li>{name} <span class="item-iri">({entity["iri"]})</span>'
            html += '<ul>'
            if 'label' in changes:
                old_label = changes['label']['old'] if changes['label']['old'] is not None else "N/A"
                new_label = changes['label']['new'] if changes['label']['new'] is not None else "N/A"
                html += f'<li>Label: <span style="text-decoration: line-through;">{old_label}</span> &#8594; <strong>{new_label}</strong></li>'
            if 'comment' in changes:
                old_comment = changes['comment']['old'] if changes['comment']['old'] is not None else "N/A"
                new_comment = changes['comment']['new'] if changes['comment']['new'] is not None else "N/A"
                html += f'<li>Comment: <span style="text-decoration: line-through;">{old_comment}</span> &#8594; <strong>{new_comment}</strong></li>'
            html += '</ul></li>'
        html += "</ul></div>"
        
    if not has_changes:
        html += '<div class="empty-state">Nenhuma mudança estrutural (classes/propriedades) detectada.</div>'
        
    html += "</div>"
    return html

def main(owl_dir, output_file):
    files = get_owl_files(owl_dir)
    
    if len(files) < 2:
        print("Preciso de pelo menos 2 arquivos .owl para comparar.")
        # Gera HTML vazio ou com mensagem
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(HTML_TEMPLATE_START + '<div class="empty-state">Aguardando mais versões para gerar histórico.</div>' + HTML_END)
        return

    content_html = ""
    
    # Compara o mais recente com o anterior (apenas o par mais recente por enquanto)
    # Poderíamos fazer um loop para gerar histórico completo: for i in range(len(files)-1):
    
    # Vamos gerar histórico de todos os pares
    for i in range(len(files) - 1):
        try:
            diff = compare_versions(files[i], files[i+1])
            content_html += generate_html_card(diff)
        except Exception as e:
            print(f"Erro ao comparar {files[i]} e {files[i+1]}: {e}")

    full_html = HTML_TEMPLATE_START + content_html + HTML_END
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"Changelog gerado em {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera um changelog HTML comparando versões de ontologias.")
    parser.add_argument('--owl-dir', required=True, help='Diretório contendo os arquivos .owl.')
    parser.add_argument('--output-file', required=True, help='Caminho para o arquivo HTML de saída.')
    
    args = parser.parse_args()
    
    main(args.owl_dir, args.output_file)
