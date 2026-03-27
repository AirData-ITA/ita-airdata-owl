#!/usr/bin/env python3
"""
Organizador de Arquivos JSON do Projeto AirData
Cria um diretório centralizado para armazenar arquivos JSON do projeto

Este script organiza os arquivos JSON do projeto em um diretório dedicado
para facilitar o gerenciamento e tratá-los como um "banco de dados JSON".
"""

import os
import shutil
from pathlib import Path
import argparse


def find_json_files(root_dir):
    """Encontra todos os arquivos JSON no projeto"""
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        # Ignorar diretórios de sistema
        dirs[:] = [d for d in dirs if d not in ['.git', '.vscode', 'airdata-venv']]
        
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    return json_files


def organize_json_files(project_root, target_dir):
    """Organiza arquivos JSON no diretório alvo"""
    json_files = find_json_files(project_root)

    # Criar diretório de destino se não existir
    os.makedirs(target_dir, exist_ok=True)

    print(f"Encontrados {len(json_files)} arquivos JSON no projeto:")
    for file in json_files:
        print(f"  - {file}")

    print(f"\nCopiando arquivos para {target_dir}/")

    for file_path in json_files:
        filename = os.path.basename(file_path)
        target_path = os.path.join(target_dir, filename)

        # Se já existir, adicionar sufixo com caminho original
        if os.path.exists(target_path):
            original_rel_path = os.path.relpath(file_path, project_root)
            # Substituir separadores de diretório por underscores
            safe_path = original_rel_path.replace(os.sep, '_').replace('/', '_')
            name, ext = os.path.splitext(filename)
            target_path = os.path.join(target_dir, f"{name}_{safe_path}{ext}")

        # Copiar arquivo
        shutil.copy2(file_path, target_path)
        print(f"  Copiado: {filename} -> {os.path.basename(target_path)}")

    print(f"\n✅ Organização concluída! {len(json_files)} arquivos copiados para {target_dir}/")

    # Remover cópias redundantes no diretório json_database
    cleanup_redundant_copies(target_dir)


def cleanup_redundant_copies(target_dir):
    """Remove cópias redundantes no diretório json_database"""
    import glob

    # Encontrar arquivos duplicados com sufixos de caminho
    pattern = os.path.join(target_dir, "*_*.*.json")
    duplicate_files = glob.glob(pattern)

    # Agrupar por nome base
    import collections
    groups = collections.defaultdict(list)

    for file_path in glob.glob(os.path.join(target_dir, "*.json")):
        filename = os.path.basename(file_path)
        if '_' in filename and '.' in filename.split('_')[-1]:
            # Tem formato nome_caminho_json
            base_name = filename.split('_')[0] + '.json'
            groups[base_name].append(file_path)
        else:
            groups[filename].append(file_path)

    # Para cada grupo com mais de um arquivo, manter o original e remover duplicatas
    removed_count = 0
    for base_name, file_list in groups.items():
        if len(file_list) > 1:
            # Manter o arquivo com nome mais simples (sem caminho embutido)
            file_list.sort(key=lambda x: len(os.path.basename(x)))  # Ordenar por comprimento do nome
            for file_path in file_list[1:]:  # Remover todos exceto o primeiro (menor nome)
                print(f"  Removendo cópia redundante: {os.path.basename(file_path)}")
                os.remove(file_path)
                removed_count += 1

    if removed_count > 0:
        print(f"  🧹 {removed_count} cópias redundantes removidas")


def main():
    parser = argparse.ArgumentParser(description='Organiza arquivos JSON do projeto em diretório dedicado')
    parser.add_argument('--project-root', default='.', help='Diretório raiz do projeto (default: .)')
    parser.add_argument('--target-dir', default='./json_database', help='Diretório de destino para os arquivos JSON (default: ./json_database)')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    target_dir = Path(args.target_dir).resolve()
    
    if not project_root.exists():
        print(f"ERRO: Diretório raiz não encontrado: {project_root}")
        return 1
    
    organize_json_files(project_root, target_dir)
    
    print(f"\n💡 DICAS:")
    print(f"  - Os arquivos originais permanecem inalterados")
    print(f"  - O diretório {target_dir} agora serve como 'banco de dados JSON' do projeto")
    print(f"  - Considere adicionar {target_dir} ao .gitignore se conter dados temporários")
    
    return 0


if __name__ == '__main__':
    exit(main())