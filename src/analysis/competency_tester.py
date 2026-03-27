#!/usr/bin/env python3
"""
Teste de Perguntas de Competência para Ontologias OWL
100% Automatizado - Sem Modificação da OWL

Executa perguntas de competência definidas em competency_questions.json
para verificar se a ontologia pode responder às consultas pretendidas.

IMPORTANTE: Este script NUNCA modifica a OWL. Apenas lê e testa queries.

Uso:
    python test_competency_questions.py <arquivo.owl> <competency_questions.json> [--output competency_report.html]
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
import time

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL
except ImportError:
    print("ERRO: rdflib não instalado. Execute: pip install rdflib")
    sys.exit(1)


class CompetencyQuestionTester:
    """Testa perguntas de competência em ontologias OWL"""

    def __init__(self, owl_file, questions_file):
        self.owl_file = owl_file
        self.questions_file = questions_file
        self.graph = Graph()
        self.questions = []
        self.results = {}
        self.question_results = []

        print(f"📖 Carregando ontologia: {owl_file}")
        try:
            self.graph.parse(owl_file, format="xml")
            print(f"✓ Ontologia carregada com sucesso")
        except Exception as e:
            print(f"✗ ERRO ao carregar ontologia: {e}")
            sys.exit(1)

        print(f"📚 Carregando perguntas de competência: {questions_file}")
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.questions = data.get('questions', [])
            print(f"✓ {len(self.questions)} perguntas de competência carregadas")
        except Exception as e:
            print(f"✗ ERRO ao carregar perguntas de competência: {e}")
            sys.exit(1)

    def run_all_tests(self):
        """Executa todos os testes de perguntas de competência"""
        print("\n" + "="*60)
        print("TESTE DE PERGUNTAS DE COMPETÊNCIA")
        print("="*60 + "\n")

        self.results['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'owl_file': str(self.owl_file),
            'questions_file': str(self.questions_file),
            'validation_type': 'Competency Questions Testing'
        }

        total_questions = len(self.questions)
        successful_questions = 0
        failed_questions = 0

        for i, question in enumerate(self.questions):
            print(f"\n{i+1:2d}. {question['question']}")
            result = self._execute_question(question)
            self.question_results.append(result)

            if result['success']:
                successful_questions += 1
                status = "✓"
            else:
                failed_questions += 1
                status = "✗"

            print(f"    {status} Resultados: {result['result_count']} | Tempo: {result['execution_time_ms']}ms")

        success_rate = (successful_questions / total_questions * 100) if total_questions else 0

        self.results['summary'] = {
            'total_questions': total_questions,
            'successful_questions': successful_questions,
            'failed_questions': failed_questions,
            'success_rate_pct': round(success_rate, 2)
        }

        self.results['detailed_results'] = self._organize_results_by_category()
        self.results['score'] = self._calculate_score()

        print("\n" + "="*60)
        print(f"✅ Testes concluídos: {successful_questions}/{total_questions} perguntas bem-sucedidas")
        print(f"   Taxa de sucesso: {success_rate:.1f}%")
        print("="*60 + "\n")

        return self.results

    def _execute_question(self, question):
        """Executa uma pergunta de competência e retorna resultado"""

        try:
            start_time = time.time()
            qres = self.graph.query(question['sparql'])
            execution_time = time.time() - start_time

            result_count = len(qres)

            # Verifica se atende expectativa mínima
            meets_expectation = result_count >= question['min_expected_results']

            # Em alguns casos especiais, um resultado vazio é desejável (como em CQ003)
            if 'interpretation' in question and 'vazio' in question['interpretation'].lower():
                meets_expectation = result_count == question['min_expected_results']

            return {
                'id': question['id'],
                'question': question['question'],
                'category': question['category'],
                'success': True,
                'result_count': result_count,
                'execution_time_ms': round(execution_time * 1000, 2),
                'meets_expectation': meets_expectation,
                'importance': question['importance'],
                'error': None,
                'sparql': question['sparql']
            }

        except Exception as e:
            return {
                'id': question['id'],
                'question': question['question'],
                'category': question['category'],
                'success': False,
                'result_count': 0,
                'execution_time_ms': 0,
                'meets_expectation': False,
                'importance': question['importance'],
                'error': str(e),
                'sparql': question.get('sparql', 'N/A')
            }

    def _organize_results_by_category(self):
        """Organiza resultados por categoria"""

        categories = {}
        for result in self.question_results:
            category = result['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        organized = {}
        for category, results in categories.items():
            organized[category] = {
                'questions': results,
                'success_count': sum(1 for r in results if r['success']),
                'total_count': len(results)
            }
            organized[category]['success_rate'] = (
                organized[category]['success_count'] / organized[category]['total_count'] * 100
                if organized[category]['total_count'] else 0
            )

        return organized

    def _calculate_score(self):
        """Calcula score baseado na importância das perguntas"""

        # Pesos por importância
        weights = {
            'CRÍTICA': 1.0,
            'ALTA': 0.8,
            'MÉDIA': 0.5,
            'BAIXA': 0.2
        }

        weighted_success = 0
        total_weight = 0

        for result in self.question_results:
            weight = weights.get(result['importance'], 0.5)
            total_weight += weight

            if result['success'] and result['meets_expectation']:
                weighted_success += weight

        score = (weighted_success / total_weight * 10) if total_weight else 0

        if score >= 9:
            level = "Excelente - A ontologia responde bem às perguntas críticas"
        elif score >= 7:
            level = "Bom - A maioria das perguntas importantes é respondida"
        elif score >= 5:
            level = "Regular - Algumas perguntas críticas não são respondidas"
        else:
            level = "Precisa Melhorar - Muitas perguntas importantes não são respondidas"

        return {
            'total_score': round(score, 2),
            'level': level,
            'critical_questions_success': sum(
                1 for r in self.question_results
                if r['importance'] == 'CRÍTICA' and r['success']
            ),
            'critical_questions_total': sum(
                1 for r in self.question_results
                if r['importance'] == 'CRÍTICA'
            )
        }

    def generate_html_report(self, output_file):
        """Gera relatório HTML no estilo de statistics.html"""

        score = self.results['score']
        summary = self.results['summary']
        detailed = self.results['detailed_results']

        # Gera tabela por categoria
        categories_html = ""
        for category, data in detailed.items():
            questions_html = ""

            for question in data['questions']:
                status_icon = "✓" if question['success'] else "✗"
                status_class = "success" if question['success'] else "failed"
                importance_class = f"importance-{question['importance'].lower()}"

                error_html = ""
                if question['error']:
                    error_html = f"<div class='error-msg'>Erro: {question['error']}</div>"

                questions_html += f"""
                <tr class="{status_class}">
                    <td>{status_icon}</td>
                    <td>{question['id']}</td>
                    <td>{question['question']}</td>
                    <td>{question['result_count']}</td>
                    <td>{question['execution_time_ms']} ms</td>
                    <td><span class="badge {importance_class}">{question['importance']}</span></td>
                </tr>
                """
                if error_html:
                    questions_html += f"<tr class='{status_class}'><td colspan='6'>{error_html}</td></tr>"

            categories_html += f"""
            <h3>{category}</h3>
            <p>Taxa de sucesso: {data['success_rate']:.1f}% ({data['success_count']}/{data['total_count']})</p>
            <table>
                <thead>
                    <tr>
                        <th width="5%">Status</th>
                        <th width="8%">ID</th>
                        <th width="35%">Pergunta</th>
                        <th width="12%">Resultados</th>
                        <th width="15%">Tempo</th>
                        <th width="15%">Importância</th>
                    </tr>
                </thead>
                <tbody>
                    {questions_html}
                </tbody>
            </table>
            """

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Relatório de Perguntas de Competência - AirData</title>
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
    tr.success {{
      background: #f0f9f0;
    }}
    tr.failed {{
      background: #fff0f0;
    }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.5rem;
      font-size: 0.85em;
      font-weight: 600;
      background: #e8e8e8;
      color: #000000;
    }}
    .badge.importance-crítica {{
      background: #cc0000;
      color: white;
    }}
    .badge.importance-alta {{
      background: #ff8800;
      color: white;
    }}
    .badge.importance-média {{
      background: #0066cc;
      color: white;
    }}
    .badge.importance-baixa {{
      background: #666666;
      color: white;
    }}
    .error-msg {{
      color: #cc0000;
      font-size: 0.9em;
      padding: 0.5rem;
      background: #ffe8e8;
      border: 1px solid #cc0000;
      margin-top: 0.25rem;
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
    <h1>Relatório de Perguntas de Competência</h1>
    <p class="meta">Gerado automaticamente em {self.results['metadata']['timestamp']}</p>
    <p class="meta">Arquivo OWL: {self.results['metadata']['owl_file']}</p>

    <div class="summary-card">
      <h3>Resumo Geral</h3>
      <table>
        <tr>
          <th width="70%">Métrica</th>
          <th width="30%" style="text-align: center;">Valor</th>
        </tr>
        <tr>
          <td>Score Total de Competência</td>
          <td style="text-align: center;"><strong>{score['total_score']}/10</strong></td>
        </tr>
        <tr>
          <td>Classificação</td>
          <td style="text-align: center;">{score['level']}</td>
        </tr>
        <tr>
          <td>Total de Perguntas Testadas</td>
          <td style="text-align: center;">{summary['total_questions']}</td>
        </tr>
        <tr>
          <td>Perguntas Bem-sucedidas</td>
          <td style="text-align: center;">{summary['successful_questions']}</td>
        </tr>
        <tr>
          <td>Perguntas Falharam</td>
          <td style="text-align: center;">{summary['failed_questions']}</td>
        </tr>
        <tr>
          <td>Taxa de Sucesso</td>
          <td style="text-align: center;"><strong>{summary['success_rate_pct']}%</strong></td>
        </tr>
      </table>
    </div>

    <h3>Perguntas Críticas</h3>
    <p>Perguntas críticas são essenciais para a funcionalidade da ontologia.</p>
    <p><strong>{score['critical_questions_success']}/{score['critical_questions_total']}</strong> perguntas críticas bem-sucedidas</p>

    <h3>Resultados Detalhados por Categoria</h3>
    {categories_html}

    <div class="summary-card">
      <h3>Resumo Executivo</h3>
      <p>
        {'✓ A ontologia demonstra alta capacidade de responder perguntas de competência!' if score['total_score'] >= 7 else '→ A ontologia precisa de melhorias para responder perguntas de competência.'}
      </p>
    </div>
  </div>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ Relatório HTML gerado: {output_file}")

    def save_json(self, output_file):
        """Salva resultados em JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"✅ Dados JSON salvos: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Teste de perguntas de competência em ontologias OWL (SEM modificar a ontologia)'
    )
    parser.add_argument('owl_file', help='Arquivo OWL a ser testado')
    parser.add_argument('questions_file', help='Arquivo JSON com perguntas de competência')
    parser.add_argument('--output', default='competency_report.html',
                       help='Arquivo HTML de saída (default: competency_report.html)')
    parser.add_argument('--json', help='Salvar resultados também em JSON')

    args = parser.parse_args()

    if not Path(args.owl_file).exists():
        print(f"❌ ERRO: Arquivo não encontrado: {args.owl_file}")
        sys.exit(1)

    if not Path(args.questions_file).exists():
        print(f"❌ ERRO: Arquivo não encontrado: {args.questions_file}")
        sys.exit(1)

    tester = CompetencyQuestionTester(args.owl_file, args.questions_file)
    results = tester.run_all_tests()

    tester.generate_html_report(args.output)

    if args.json:
        tester.save_json(args.json)

    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    score = results['score']
    print(f"\n🎯 SCORE: {score['total_score']}/10 ({score['level']})")
    print(f"\n   Perguntas críticas: {score['critical_questions_success']}/{score['critical_questions_total']}")
    print(f"   Taxa de sucesso geral: {results['summary']['success_rate_pct']}%")
    print("\n" + "="*60)


if __name__ == '__main__':
    main()