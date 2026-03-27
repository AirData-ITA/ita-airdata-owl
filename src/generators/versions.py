import os
import json
import datetime
import re
import argparse

def extract_version(filename):
    """Extrai versão semântica do nome do arquivo (ex: airdata_owl_v1.2.3.owl -> (1, 2, 3))"""
    match = re.search(r'v(\d+)\.(\d+)\.(\d+)', filename)
    if match:
        return tuple(map(int, match.groups()))
    return (0, 0, 0)  # Fallback para arquivos sem versão

def generate_versions_json(owl_dir, output_file):
    versions = []
    
    # Verifica se o diretório existe
    if not os.path.exists(owl_dir):
        print(f"Diretório {owl_dir} não encontrado.")
        return

    # Lista arquivos .owl
    for filename in os.listdir(owl_dir):
        if filename.endswith(".owl") and not filename.startswith('.'):
            filepath = os.path.join(owl_dir, filename)
            
            # Obtém metadados do arquivo
            stats = os.stat(filepath)
            modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            size_kb = round(stats.st_size / 1024, 2)
            
            # Extrai versão semântica
            version_tuple = extract_version(filename)
            version_str = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"
            
            # Adiciona à lista
            versions.append({
                "filename": filename,
                "path": f"docs/{filename}",
                "date": modified_time,
                "size": f"{size_kb} KB",
                "version": version_str
            })

    # Ordena por versão semântica (mais recente primeiro)
    versions.sort(key=lambda x: extract_version(x['filename']), reverse=True)

    # Cria o diretório de saída se ele não existir
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Salva o JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(versions, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Arquivo {output_file} gerado com {len(versions)} versões.")
    for v in versions:
        print(f"   - {v['filename']} (v{v['version']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera um JSON com as versões da ontologia.")
    parser.add_argument('--owl-dir', required=True, help='Diretório contendo os arquivos .owl.')
    parser.add_argument('--output-file', required=True, help='Caminho para o arquivo JSON de saída.')
    
    args = parser.parse_args()
    
    generate_versions_json(args.owl_dir, args.output_file)
