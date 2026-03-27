#!/usr/bin/env python3
"""
Validação de Queries SPARQL para Ontologias OWL
100% Automatizado - Sem Modificação da OWL

Testa queries SPARQL comuns que LLMs usariam para:
- Listar classes e propriedades
- Navegar hierarquias
- Descobrir domínios e ranges
- Buscar definições e labels
- Testar restrições e axiomas

IMPORTANTE: Este script NUNCA modifica a OWL. Apenas lê e testa queries.

Uso:
    python test_sparql_queries.py <arquivo.owl> [--output sparql_validation.html]
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


class SPARQLQueryTester:
    """Testa queries SPARQL em ontologias OWL"""

    def __init__(self, owl_file):
        self.owl_file = owl_file
        self.graph = Graph()
        self.results = {}
        self.query_results = []

        print(f"📖 Carregando ontologia: {owl_file}")
        try:
            self.graph.parse(owl_file, format="xml")
            print(f"✓ Ontologia carregada com sucesso")
        except Exception as e:
            print(f"✗ ERRO ao carregar ontologia: {e}")
            sys.exit(1)

        # Define queries SPARQL que LLMs tipicamente usariam
        self.test_queries = self._define_test_queries()

    def _define_test_queries(self):
        """Define conjunto de queries SPARQL representativas"""

        return {
            'basic_discovery': [
                {
                    'name': 'Listar todas as classes',
                    'query': '''
                        SELECT DISTINCT ?class WHERE {
                            ?class a owl:Class .
                        }
                    ''',
                    'min_expected_results': 1,
                    'importance': 'CRÍTICA'
                },
                {
                    'name': 'Listar object properties',
                    'query': '''
                        SELECT DISTINCT ?prop WHERE {
                            ?prop a owl:ObjectProperty .
                        }
                    ''',
                    'min_expected_results': 1,
                    'importance': 'CRÍTICA'
                },
                {
                    'name': 'Listar data properties',
                    'query': '''
                        SELECT DISTINCT ?prop WHERE {
                            ?prop a owl:DatatypeProperty .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                }
            ],

            'hierarchy_navigation': [
                {
                    'name': 'Buscar hierarquia de classes (subclasses)',
                    'query': '''
                        SELECT DISTINCT ?subclass ?superclass WHERE {
                            ?subclass rdfs:subClassOf ?superclass .
                            FILTER(isURI(?superclass))
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'ALTA'
                },
                {
                    'name': 'Buscar hierarquia de propriedades',
                    'query': '''
                        SELECT DISTINCT ?subprop ?superprop WHERE {
                            ?subprop rdfs:subPropertyOf ?superprop .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                }
            ],

            'domain_range': [
                {
                    'name': 'Listar propriedades com domain e range',
                    'query': '''
                        SELECT DISTINCT ?prop ?domain ?range WHERE {
                            ?prop rdfs:domain ?domain .
                            ?prop rdfs:range ?range .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'ALTA'
                },
                {
                    'name': 'Buscar properties sem domain declarado',
                    'query': '''
                        SELECT DISTINCT ?prop WHERE {
                            { ?prop a owl:ObjectProperty }
                            UNION
                            { ?prop a owl:DatatypeProperty }
                            FILTER NOT EXISTS { ?prop rdfs:domain ?domain }
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                }
            ],

            'annotations': [
                {
                    'name': 'Buscar classes com labels',
                    'query': '''
                        SELECT DISTINCT ?class ?label WHERE {
                            ?class a owl:Class .
                            ?class rdfs:label ?label .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'ALTA'
                },
                {
                    'name': 'Buscar definições (rdfs:comment)',
                    'query': '''
                        SELECT DISTINCT ?entity ?comment WHERE {
                            ?entity rdfs:comment ?comment .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                },
                {
                    'name': 'Buscar labels em português',
                    'query': '''
                        SELECT DISTINCT ?entity ?label WHERE {
                            ?entity rdfs:label ?label .
                            FILTER(lang(?label) = "pt" || lang(?label) = "pt-br" || lang(?label) = "pt-BR")
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'ALTA'
                }
            ],

            'restrictions': [
                {
                    'name': 'Listar restrições OWL',
                    'query': '''
                        SELECT DISTINCT ?restriction ?property WHERE {
                            ?restriction a owl:Restriction .
                            ?restriction owl:onProperty ?property .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                },
                {
                    'name': 'Buscar cardinalidades',
                    'query': '''
                        SELECT DISTINCT ?restriction ?property ?cardinality WHERE {
                            ?restriction a owl:Restriction .
                            ?restriction owl:onProperty ?property .
                            {
                                ?restriction owl:cardinality ?cardinality
                            } UNION {
                                ?restriction owl:minCardinality ?cardinality
                            } UNION {
                                ?restriction owl:maxCardinality ?cardinality
                            }
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                }
            ],

            'advanced': [
                {
                    'name': 'Buscar propriedades funcionais',
                    'query': '''
                        SELECT DISTINCT ?prop WHERE {
                            ?prop a owl:FunctionalProperty .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'BAIXA'
                },
                {
                    'name': 'Buscar propriedades inversas',
                    'query': '''
                        SELECT DISTINCT ?prop1 ?prop2 WHERE {
                            ?prop1 owl:inverseOf ?prop2 .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                },
                {
                    'name': 'Buscar classes disjuntas',
                    'query': '''
                        SELECT DISTINCT ?class1 ?class2 WHERE {
                            ?class1 owl:disjointWith ?class2 .
                        }
                    ''',
                    'min_expected_results': 0,
                    'importance': 'MÉDIA'
                }
            ]
        }

    def run_all_tests(self):
        """Executa todos os testes de queries"""
        print("\n" + "="*60)
        print("TESTE DE QUERIES SPARQL")
        print("="*60 + "\n")

        self.results['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'owl_file': str(self.owl_file),
            'validation_type': 'SPARQL Query Testing'
        }

        total_queries = sum(len(queries) for queries in self.test_queries.values())
        successful_queries = 0
        failed_queries = 0

        for category, queries in self.test_queries.items():
            print(f"\n📂 Categoria: {category.upper()}")
            print("-" * 60)

            for query_def in queries:
                result = self._execute_query(query_def)
                self.query_results.append(result)

                if result['success']:
                    successful_queries += 1
                    status = "✓"
                else:
                    failed_queries += 1
                    status = "✗"

                print(f"  {status} {query_def['name']} ({result['result_count']} resultados)")

        success_rate = (successful_queries / total_queries * 100) if total_queries else 0

        self.results['summary'] = {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': failed_queries,
            'success_rate_pct': round(success_rate, 2)
        }

        self.results['detailed_results'] = self._organize_results_by_category()
        self.results['score'] = self._calculate_score()

        print("\n" + "="*60)
        print(f"✅ Testes concluídos: {successful_queries}/{total_queries} queries bem-sucedidas")
        print(f"   Taxa de sucesso: {success_rate:.1f}%")
        print("="*60 + "\n")

        return self.results

    def _execute_query(self, query_def):
        """Executa uma query SPARQL e retorna resultado"""

        try:
            start_time = time.time()
            qres = self.graph.query(query_def['query'])
            execution_time = time.time() - start_time

            result_count = len(qres)

            # Verifica se atende expectativa mínima
            meets_expectation = result_count >= query_def['min_expected_results']

            return {
                'name': query_def['name'],
                'success': True,
                'result_count': result_count,
                'execution_time_ms': round(execution_time * 1000, 2),
                'meets_expectation': meets_expectation,
                'importance': query_def['importance'],
                'error': None
            }

        except Exception as e:
            return {
                'name': query_def['name'],
                'success': False,
                'result_count': 0,
                'execution_time_ms': 0,
                'meets_expectation': False,
                'importance': query_def['importance'],
                'error': str(e)
            }

    def _organize_results_by_category(self):
        """Organiza resultados por categoria"""

        organized = {}
        idx = 0

        for category, queries in self.test_queries.items():
            organized[category] = {
                'queries': [],
                'success_count': 0,
                'total_count': len(queries)
            }

            for _ in queries:
                result = self.query_results[idx]
                organized[category]['queries'].append(result)

                if result['success']:
                    organized[category]['success_count'] += 1

                idx += 1

            organized[category]['success_rate'] = (
                organized[category]['success_count'] / organized[category]['total_count'] * 100
                if organized[category]['total_count'] else 0
            )

        return organized

    def _calculate_score(self):
        """Calcula score baseado em queries críticas"""

        # Pesos por importância
        weights = {
            'CRÍTICA': 1.0,
            'ALTA': 0.7,
            'MÉDIA': 0.4,
            'BAIXA': 0.2
        }

        weighted_success = 0
        total_weight = 0

        for result in self.query_results:
            weight = weights.get(result['importance'], 0.5)
            total_weight += weight

            if result['success'] and result['meets_expectation']:
                weighted_success += weight

        score = (weighted_success / total_weight * 10) if total_weight else 0

        if score >= 9:
            level = "Excelente - Todas as queries essenciais funcionam"
        elif score >= 7:
            level = "Bom - Queries principais funcionam"
        elif score >= 5:
            level = "Regular - Algumas queries críticas falharam"
        else:
            level = "Precisa Melhorar - Muitas queries não funcionam"

        return {
            'total_score': round(score, 2),
            'level': level,
            'critical_queries_success': sum(
                1 for r in self.query_results
                if r['importance'] == 'CRÍTICA' and r['success']
            ),
            'critical_queries_total': sum(
                1 for r in self.query_results
                if r['importance'] == 'CRÍTICA'
            )
        }

    def generate_html_report(self, output_file):
        """Gera relatório HTML"""

        score = self.results['score']
        summary = self.results['summary']
        detailed = self.results['detailed_results']

        # Gera tabela por categoria
        categories_html = ""
        for category, data in detailed.items():
            queries_html = ""

            for query in data['queries']:
                status_icon = "✓" if query['success'] else "✗"
                status_class = "success" if query['success'] else "failed"
                importance_class = f"importance-{query['importance'].lower()}"

                error_html = ""
                if query['error']:
                    error_html = f"<div class='error-msg'>Erro: {query['error']}</div>"

                queries_html += f"""
                <tr class="{status_class}">
                    <td>{status_icon}</td>
                    <td>{query['name']}</td>
                    <td>{query['result_count']}</td>
                    <td>{query['execution_time_ms']} ms</td>
                    <td><span class="badge {importance_class}">{query['importance']}</span></td>
                </tr>
                """
                if error_html:
                    queries_html += f"<tr class='{status_class}'><td colspan='5'>{error_html}</td></tr>"

            categories_html += f"""
            <h3>{category.replace('_', ' ').title()}</h3>
            <p>Taxa de sucesso: {data['success_rate']:.1f}% ({data['success_count']}/{data['total_count']})</p>
            <table>
                <thead>
                    <tr>
                        <th width="5%">Status</th>
                        <th width="40%">Query</th>
                        <th width="15%">Resultados</th>
                        <th width="15%">Tempo</th>
                        <th width="15%">Importância</th>
                    </tr>
                </thead>
                <tbody>
                    {queries_html}
                </tbody>
            </table>
            """

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Validação SPARQL - AirData</title>
<!-- AirData Header Style Start -->
<!-- AirData Header Style End -->
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background: #f8fafc; color: #1f2933; margin: 0; padding: 2rem; }}
        .container {{ max-width: 980px; margin: 0 auto; background: #ffffff; border: 1px solid #e6e9ef; border-radius: 10px; padding: 2rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06); }}
        h1 {{ color: #003C7D; margin-top: 0; }}
        h2 {{ color: #003C7D; margin-top: 2rem; margin-bottom: 0.8rem; font-size: 1.3em; font-weight: 600; padding-bottom: 0.3rem; }}
        h3 {{ color: #003C7D; margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 1.1em; font-weight: 600; }}


        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ text-align: left; padding: 0.75rem; border-bottom: 1px solid #e6e9ef; }}
        th {{ width: 45%; color: #475569; font-weight: 600; }}

        tr.success {{ background: #f0f9f0; }}
        tr.failed {{ background: #fff0f0; }}

        .badge {{ display: inline-block; padding: 0.2rem 0.5rem; font-size: 0.85em; font-weight: 600; background: #e8e8e8; color: #000000; }}
        .badge.importance-crítica {{ background: #cc0000; color: white; }}
        .badge.importance-alta {{ background: #ff8800; color: white; }}
        .badge.importance-média {{ background: #0066cc; color: white; }}
        .badge.importance-baixa {{ background: #666666; color: white; }}

        .error-msg {{ color: #cc0000; font-size: 0.9em; padding: 0.5rem; background: #ffe8e8; border: 1px solid #cc0000; margin-top: 0.25rem; }}
        .timestamp {{ color: #64748b; font-size: 0.95rem; }}
    </style>
</head>
<body>
<!-- AirData Header Start -->
<!-- AirData Header End -->
    <div class="container">
        <h1>Relatório de Validação SPARQL</h1>

        <h2>Resumo Geral</h2>
        <table>
            <tr>
                <th style="width: 70%;">Métrica</th>
                <th style="width: 30%; text-align: center;">Valor</th>
            </tr>
            <tr>
                <td>Score Total de Query-ability</td>
                <td style="text-align: center;"><strong>{score['total_score']}/10</strong></td>
            </tr>
            <tr>
                <td>Classificação</td>
                <td style="text-align: center;">{score['level']}</td>
            </tr>
            <tr>
                <td>Total de Queries Testadas</td>
                <td style="text-align: center;">{summary['total_queries']}</td>
            </tr>
            <tr>
                <td>Queries Bem-sucedidas</td>
                <td style="text-align: center;">{summary['successful_queries']}</td>
            </tr>
            <tr>
                <td>Queries Falharam</td>
                <td style="text-align: center;">{summary['failed_queries']}</td>
            </tr>
            <tr>
                <td>Taxa de Sucesso</td>
                <td style="text-align: center;"><strong>{summary['success_rate_pct']}%</strong></td>
            </tr>
        </table>

        <h2>Queries Críticas</h2>
        <p>Queries críticas são essenciais para LLMs navegarem na ontologia.</p>
        <p><strong>{score['critical_queries_success']}/{score['critical_queries_total']}</strong> queries críticas bem-sucedidas</p>

        <h2>Resultados Detalhados por Categoria</h2>
        {categories_html}

        <div class="timestamp">
            Relatório gerado automaticamente em {self.results['metadata']['timestamp']}<br>
            Arquivo analisado: {self.results['metadata']['owl_file']}<br>
            <strong>IMPORTANTE:</strong> Este relatório apenas testa queries. Não modifica a ontologia.
        </div>
    </div>

<!-- AirData Footer Start -->
<!-- AirData Footer End -->

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
        description='Teste de queries SPARQL em ontologias OWL (SEM modificar a ontologia)'
    )
    parser.add_argument('owl_file', help='Arquivo OWL a ser testado')
    parser.add_argument('--output', default='sparql_validation.html',
                       help='Arquivo HTML de saída (default: sparql_validation.html)')
    parser.add_argument('--json', help='Salvar resultados também em JSON')

    args = parser.parse_args()

    if not Path(args.owl_file).exists():
        print(f"❌ ERRO: Arquivo não encontrado: {args.owl_file}")
        sys.exit(1)

    tester = SPARQLQueryTester(args.owl_file)
    results = tester.run_all_tests()

    tester.generate_html_report(args.output)

    if args.json:
        tester.save_json(args.json)

    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    score = results['score']
    print(f"\n🎯 SCORE: {score['total_score']}/10 ({score['level']})")
    print(f"\n   Queries críticas: {score['critical_queries_success']}/{score['critical_queries_total']}")
    print(f"   Taxa de sucesso geral: {results['summary']['success_rate_pct']}%")
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
