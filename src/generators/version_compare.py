#!/usr/bin/env python3
"""
Comparação Delta entre Versões de Ontologia
Gera relatório comparativo entre duas versões consecutivas

Este script compara os relatórios de qualidade de duas versões
da ontologia e destaca melhorias ou regressões.

Uso:
    python compare_versions_delta.py <versão_anterior.json> <versão_atual.json> [--output delta_report.html]
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path


def load_json_report(file_path):
    """Carrega um relatório JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_difference(current, previous, key, multiplier=1):
    """Calcula a diferença entre valores de duas versões"""
    current_val = current.get(key, 0)
    previous_val = previous.get(key, 0)
    
    if isinstance(current_val, (int, float)) and isinstance(previous_val, (int, float)):
        difference = current_val - previous_val
        percentage_change = (difference / abs(previous_val) * 100) if previous_val != 0 else 0
        
        return {
            'current': current_val,
            'previous': previous_val,
            'difference': difference,
            'percentage_change': round(percentage_change, 2),
            'improvement': difference > 0
        }
    else:
        return {
            'current': current_val,
            'previous': previous_val,
            'difference': 'N/A',
            'percentage_change': 'N/A',
            'improvement': current_val != previous_val
        }


def compare_logic_scores(current_report, previous_report):
    """Compara os scores de lógica entre versões"""
    current_score = current_report.get('logic_richness_score', {}).get('total_score', 0)
    previous_score = previous_report.get('logic_richness_score', {}).get('total_score', 0)
    
    difference = current_score - previous_score
    percentage_change = (difference / abs(previous_score) * 100) if previous_score != 0 else 0
    
    return {
        'current': current_score,
        'previous': previous_score,
        'difference': round(difference, 2),
        'percentage_change': round(percentage_change, 2),
        'improvement': difference > 0
    }


def compare_llm_readability_scores(current_report, previous_report):
    """Compara os scores de legibilidade por LLM entre versões"""
    current_score = current_report.get('llm_readability_score', {}).get('total_score', 0)
    previous_score = previous_report.get('llm_readability_score', {}).get('total_score', 0)
    
    difference = current_score - previous_score
    percentage_change = (difference / abs(previous_score) * 100) if previous_score != 0 else 0
    
    return {
        'current': current_score,
        'previous': previous_score,
        'difference': round(difference, 2),
        'percentage_change': round(percentage_change, 2),
        'improvement': difference > 0
    }


def compare_sparql_scores(current_report, previous_report):
    """Compara os scores de SPARQL entre versões"""
    current_score = current_report.get('score', {}).get('total_score', 0)
    previous_score = previous_report.get('score', {}).get('total_score', 0)
    
    difference = current_score - previous_score
    percentage_change = (difference / abs(previous_score) * 100) if previous_score != 0 else 0
    
    return {
        'current': current_score,
        'previous': previous_score,
        'difference': round(difference, 2),
        'percentage_change': round(percentage_change, 2),
        'improvement': difference > 0
    }


def compare_statistics(current_report, previous_report):
    """Compara as estatísticas estruturais entre versões"""
    comparisons = {}
    
    # Comparar estrutura básica
    structure_keys = [
        'classes', 'object_properties', 'data_properties', 
        'individuals', 'axioms'
    ]
    
    for key in structure_keys:
        comparisons[key] = calculate_difference(
            current_report.get('structure', {}), 
            previous_report.get('structure', {}), 
            key
        )
    
    # Comparar hierarquia
    hierarchy_keys = [
        'max_depth', 'avg_subclasses', 'leaf_classes', 
        'no_explicit_superclass'
    ]
    
    for key in hierarchy_keys:
        comparisons[f"hierarchy_{key}"] = calculate_difference(
            current_report.get('hierarchy', {}), 
            previous_report.get('hierarchy', {}), 
            key
        )
    
    # Comparar qualidade
    quality_keys = [
        'classes_no_label', 'classes_no_comment', 
        'properties_no_domain', 'properties_no_range'
    ]
    
    for key in quality_keys:
        comparisons[f"quality_{key}"] = calculate_difference(
            current_report.get('quality', {}), 
            previous_report.get('quality', {}), 
            key
        )
    
    # Comparar consistência
    comparisons['consistency'] = {
        'current': current_report.get('consistency_check', 'desconhecido'),
        'previous': previous_report.get('consistency_check', 'desconhecido'),
        'difference': 'N/A',
        'percentage_change': 'N/A',
        'improvement': current_report.get('consistency_check') == 'sim' and previous_report.get('consistency_check') != 'sim'
    }
    
    return comparisons


def generate_delta_report(previous_report, current_report, previous_version, current_version):
    """Gera o relatório delta completo"""
    return {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'comparison': f"{previous_version} -> {current_version}",
            'previous_file': previous_report.get('metadata', {}).get('owl_file', 'desconhecido'),
            'current_file': current_report.get('metadata', {}).get('owl_file', 'desconhecido')
        },
        'logic_comparison': compare_logic_scores(current_report, previous_report),
        'llm_readability_comparison': compare_llm_readability_scores(current_report, previous_report),
        'sparql_comparison': compare_sparql_scores(current_report, previous_report),
        'statistics_comparison': compare_statistics(current_report, previous_report)
    }


def extract_version_from_filename(filename):
    """Extrai o número de versão do nome do arquivo OWL"""
    import re
    match = re.search(r'v(\d+\.\d+\.\d+)', filename)
    return f"v{match.group(1)}" if match else filename


def generate_html_report(delta_report, output_file):
    """Gera relatório HTML no mesmo estilo que statistics.html"""

    # Pegar os dados para o relatório
    meta = delta_report['metadata']
    logic_comp = delta_report['logic_comparison']
    llm_comp = delta_report['llm_readability_comparison']
    sparql_comp = delta_report['sparql_comparison']
    stats_comp = delta_report['statistics_comparison']

    # Extrair versões dos nomes de arquivo
    prev_version = extract_version_from_filename(meta['previous_file'])
    curr_version = extract_version_from_filename(meta['current_file'])

    # Função auxiliar para determinar ícone e cor
    def get_indicator(improvement, difference):
        if difference == 'N/A':
            return '-', ''
        elif improvement:
            return '↑', '#28a745'  # verde
        else:
            return '↓', '#d73a49'  # vermelho

    # Gerar linhas para estrutura
    structure_html = ""
    for key, data in stats_comp.items():
        if key.startswith('hierarchy_') or key.startswith('quality_'):
            continue  # Pular para seções separadas

        indicator, color = get_indicator(data['improvement'], data['difference'])

        structure_html += f"""
          <tr>
            <th>{key.replace('_', ' ').title()}</th>
            <td>{data['previous']}</td>
            <td>{data['current']}</td>
            <td style="color: {color}; font-weight: bold;">{indicator} {data['difference']} ({data['percentage_change']}%)</td>
          </tr>
        """

    # Gerar linhas para hierarquia
    hierarchy_html = ""
    for key, data in stats_comp.items():
        if key.startswith('hierarchy_'):
            clean_key = key.replace('hierarchy_', '').replace('_', ' ').title()
            indicator, color = get_indicator(data['improvement'], data['difference'])

            hierarchy_html += f"""
              <tr>
                <th>{clean_key}</th>
                <td>{data['previous']}</td>
                <td>{data['current']}</td>
                <td style="color: {color}; font-weight: bold;">{indicator} {data['difference']} ({data['percentage_change']}%)</td>
              </tr>
            """

    # Gerar linhas para qualidade
    quality_html = ""
    for key, data in stats_comp.items():
        if key.startswith('quality_'):
            clean_key = key.replace('quality_', '').replace('_', ' ').title()
            indicator, color = get_indicator(data['improvement'], data['difference'])

            quality_html += f"""
              <tr>
                <th>{clean_key}</th>
                <td>{data['previous']}</td>
                <td>{data['current']}</td>
                <td style="color: {color}; font-weight: bold;">{indicator} {data['difference']} ({data['percentage_change']}%)</td>
              </tr>
            """

    # Gerar linhas para scores
    scores_html = f"""
      <tr>
        <th>Score de Riqueza Lógica</th>
        <td>{logic_comp['previous']}/10</td>
        <td>{logic_comp['current']}/10</td>
        <td style="color: {'#28a745' if logic_comp['improvement'] else '#d73a49'}; font-weight: bold;">
          {'↑' if logic_comp['improvement'] else '↓'} {logic_comp['difference']} ({logic_comp['percentage_change']}%)
        </td>
      </tr>
      <tr>
        <th>Score de Legibilidade por LLM</th>
        <td>{llm_comp['previous']}/10</td>
        <td>{llm_comp['current']}/10</td>
        <td style="color: {'#28a745' if llm_comp['improvement'] else '#d73a49'}; font-weight: bold;">
          {'↑' if llm_comp['improvement'] else '↓'} {llm_comp['difference']} ({llm_comp['percentage_change']}%)
        </td>
      </tr>
      <tr>
        <th>Score de Consultas SPARQL</th>
        <td>{sparql_comp['previous']}/10</td>
        <td>{sparql_comp['current']}/10</td>
        <td style="color: {'#28a745' if sparql_comp['improvement'] else '#d73a49'}; font-weight: bold;">
          {'↑' if sparql_comp['improvement'] else '↓'} {sparql_comp['difference']} ({sparql_comp['percentage_change']}%)
        </td>
      </tr>
    """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Relatório Delta de Qualidade - AirData</title>
  <style>
    body {{
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background: #f8fafc;
      color: #1f2933;
      margin: 0;
      padding: 2rem;
    }}
    .container {{
      max-width: 980px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #e6e9ef;
      border-radius: 10px;
      padding: 2rem;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }}
    h1 {{
      color: #003C7D;
      margin-top: 0;
    }}
    h3 {{
      color: #003C7D;
      margin-top: 2rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }}
    th, td {{
      text-align: left;
      padding: 0.75rem;
      border-bottom: 1px solid #e6e9ef;
    }}
    th {{
      width: 45%;
      color: #475569;
      font-weight: 600;
    }}
    ul {{
      padding-left: 1.25rem;
    }}
    .meta {{
      color: #64748b;
      font-size: 0.95rem;
    }}
    .summary-card {{
      background: #f1f5f9;
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 1.5rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Relatório Delta de Qualidade</h1>
    <p class="meta">Comparação entre versões: {prev_version} → {curr_version}</p>
    <p class="meta">Gerado automaticamente em {meta['timestamp']}</p>

    <div class="summary-card">
      <h3>Resumo da Comparação</h3>
      <p>Comparando <strong>{prev_version}</strong> → <strong>{curr_version}</strong></p>
    </div>

    <h3>Scores de Qualidade</h3>
    <table>
      <tr>
        <th>Métrica</th>
        <th>Versão Anterior</th>
        <th>Versão Atual</th>
        <th>Variação</th>
      </tr>
      {scores_html}
    </table>

    <h3>Estrutura</h3>
    <table>
      <tr>
        <th>Componente</th>
        <th>Versão Anterior</th>
        <th>Versão Atual</th>
        <th>Variação</th>
      </tr>
      {structure_html}
    </table>

    <h3>Hierarquia</h3>
    <table>
      <tr>
        <th>Aspecto</th>
        <th>Versão Anterior</th>
        <th>Versão Atual</th>
        <th>Variação</th>
      </tr>
      {hierarchy_html}
    </table>

    <h3>Qualidade Objetiva</h3>
    <table>
      <tr>
        <th>Aspecto</th>
        <th>Versão Anterior</th>
        <th>Versão Atual</th>
        <th>Variação</th>
      </tr>
      {quality_html}
    </table>

    <div class="summary-card">
      <h3>Resumo Executivo</h3>
      <p>
        {'✓ Melhorias significativas detectadas!' if any([
          logic_comp['improvement'], llm_comp['improvement'], sparql_comp['improvement'],
          *[data['improvement'] for data in stats_comp.values() if isinstance(data.get('improvement'), bool)]
        ]) else '→ Nenhuma melhoria significativa detectada.'}
      </p>
    </div>
  </div>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Relatório delta gerado: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Comparação delta entre relatórios de qualidade de ontologias'
    )
    parser.add_argument('previous_report', help='Relatório JSON da versão anterior')
    parser.add_argument('current_report', help='Relatório JSON da versão atual')
    parser.add_argument('--output', default='delta_report.html',
                       help='Arquivo HTML de saída (default: delta_report.html)')
    parser.add_argument('--json', help='Salvar resultados também em JSON')

    args = parser.parse_args()

    # Verificar se os arquivos existem
    if not Path(args.previous_report).exists():
        print(f"ERRO: Arquivo não encontrado: {args.previous_report}")
        sys.exit(1)
        
    if not Path(args.current_report).exists():
        print(f"ERRO: Arquivo não encontrado: {args.current_report}")
        sys.exit(1)

    # Carregar os relatórios
    previous_report = load_json_report(args.previous_report)
    current_report = load_json_report(args.current_report)

    # Extrair informações de versão
    prev_version = previous_report.get('metadata', {}).get('owl_file', 'versão desconhecida')
    curr_version = current_report.get('metadata', {}).get('owl_file', 'versão desconhecida')

    # Gerar relatório delta
    delta_report = generate_delta_report(previous_report, current_report, prev_version, curr_version)

    # Gerar relatório HTML
    generate_html_report(delta_report, args.output)

    # Salvar JSON se solicitado
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(delta_report, f, indent=2, ensure_ascii=False)
        print(f"Dados JSON salvos: {args.json}")

    # Resumo no terminal
    print("\n" + "="*60)
    print("RESUMO DA COMPARAÇÃO DELTA")
    print("="*60)
    print(f"\nComparando: {prev_version} → {curr_version}")
    print(f"\nScores:")
    print(f"  Riqueza Lógica: {delta_report['logic_comparison']['previous']} → {delta_report['logic_comparison']['current']} ({delta_report['logic_comparison']['difference']:+.2f})")
    print(f"  Legibilidade LLM: {delta_report['llm_readability_comparison']['previous']} → {delta_report['llm_readability_comparison']['current']} ({delta_report['llm_readability_comparison']['difference']:+.2f})")
    print(f"  SPARQL: {delta_report['sparql_comparison']['previous']} → {delta_report['sparql_comparison']['current']} ({delta_report['sparql_comparison']['difference']:+.2f})")


if __name__ == '__main__':
    main()