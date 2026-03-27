#!/usr/bin/env python3
"""
Pipeline de Comparação Delta Automática
Integra a comparação delta no fluxo de build

Este script verifica se há múltiplas versões da ontologia
e gera automaticamente um relatório delta comparando as versões.
"""

import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


def get_owl_versions(owl_dir):
    """Obtém todas as versões OWL ordenadas por data de modificação"""
    owl_files = []
    for name in os.listdir(owl_dir):
        if name.endswith(".owl"):
            path = os.path.join(owl_dir, name)
            mtime = os.path.getmtime(path)
            owl_files.append((mtime, path, name))
    
    # Ordenar por data de modificação (mais recente primeiro)
    owl_files.sort(key=lambda x: x[0], reverse=True)
    return owl_files


def generate_delta_report_if_possible(owl_dir, site_dir, onto_doc_dir):
    """Gera relatório delta se houver múltiplas versões"""
    owl_versions = get_owl_versions(owl_dir)
    
    if len(owl_versions) < 2:
        print("ℹ️  Aviso: Número insuficiente de versões para comparação delta (necessário ≥ 2)")
        print("   Encontradas:", len(owl_versions), "versão(ões)")
        return False
    
    # Pegar as duas versões mais recentes
    _, latest_path, latest_name = owl_versions[0]
    _, previous_path, previous_name = owl_versions[1]
    
    print(f"📊 Comparando versões:")
    print(f"   Atual:   {latest_name}")
    print(f"   Anterior: {previous_name}")
    
    # Encontrar os arquivos JSON correspondentes
    latest_json = None
    previous_json = None
    
    for root, dirs, files in os.walk(site_dir):
        for file in files:
            if file.endswith('.json') and not file.startswith('delta_'):
                full_path = os.path.join(root, file)
                
                # Tentar identificar a qual versão pertence o JSON
                if latest_name.replace('.owl', '') in file:
                    latest_json = full_path
                elif previous_name.replace('.owl', '') in file:
                    previous_json = full_path
    
    # Se não encontrarmos os JSONs específicos, tentar encontrar os mais recentes
    if not latest_json or not previous_json:
        json_files = []
        for root, dirs, files in os.walk(site_dir):
            for file in files:
                if file.endswith('.json') and not file.startswith('delta_'):
                    json_files.append((os.path.getmtime(os.path.join(root, file)), os.path.join(root, file)))
        
        json_files.sort(key=lambda x: x[0], reverse=True)
        
        if len(json_files) >= 2:
            _, latest_json = json_files[0]
            _, previous_json = json_files[1]
    
    if not latest_json or not previous_json:
        print("⚠️  Não foi possível encontrar arquivos JSON de relatórios anteriores para comparação")
        print("   Será necessário executar os testes de qualidade primeiro")
        return False
    
    print(f"🔍 Usando relatórios JSON:")
    print(f"   Atual:   {latest_json}")
    print(f"   Anterior: {previous_json}")
    
    # Executar o script de comparação delta
    delta_script = os.path.join(onto_doc_dir, 'compare_versions_delta.py')
    delta_output = os.path.join(site_dir, 'delta_report.html')
    delta_json = os.path.join(site_dir, 'delta_report.json')
    
    cmd = [
        'python3', delta_script,
        previous_json,
        latest_json,
        '--output', delta_output,
        '--json', delta_json
    ]
    
    print(f"🚀 Executando comparação delta...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=onto_doc_dir)
        
        if result.returncode == 0:
            print(f"✅ Relatório delta gerado com sucesso!")
            print(f"   HTML: {delta_output}")
            print(f"   JSON: {delta_json}")
            
            # Aplicar cabeçalhos e rodapés aos novos relatórios
            normalize_header_script = os.path.join(onto_doc_dir, 'normalize_header.py')
            normalize_footer_script = os.path.join(onto_doc_dir, 'normalize_footer.py')
            
            subprocess.run(['python3', normalize_header_script, '--site-dir', site_dir], 
                          capture_output=True, text=True, cwd=onto_doc_dir)
            subprocess.run(['python3', normalize_footer_script, '--site-dir', site_dir], 
                          capture_output=True, text=True, cwd=onto_doc_dir)
            
            return True
        else:
            print(f"❌ Erro ao executar comparação delta:")
            print(f"   Comando: {' '.join(cmd)}")
            print(f"   Erro: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar comparação delta: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Pipeline de comparação delta automática')
    parser.add_argument('--owl-dir', required=True, help='Diretório contendo os arquivos .owl')
    parser.add_argument('--site-dir', required=True, help='Diretório de saída do site')
    parser.add_argument('--onto-doc-dir', required=True, help='Diretório OntoDoc')
    
    args = parser.parse_args()
    
    success = generate_delta_report_if_possible(args.owl_dir, args.site_dir, args.onto_doc_dir)
    
    if success:
        print("\n🎉 Pipeline de comparação delta concluído com sucesso!")
    else:
        print("\n⚠️  Pipeline de comparação delta concluído com avisos.")


if __name__ == '__main__':
    main()