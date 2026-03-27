#!/usr/bin/env python3
"""
Validação de Axiomas Lógicos OWL
100% Automatizado - Sem Modificação da OWL

Analisa restrições lógicas essenciais para LLMs fazerem inferências:
- Restrições de cardinalidade (owl:cardinality, min/max)
- Classes disjuntas (owl:disjointWith)
- Propriedades funcionais/inversas funcionais
- Características de propriedades (simetria, transitividade, reflexividade)
- Restrições complexas (owl:allValuesFrom, owl:someValuesFrom)

IMPORTANTE: Este script NUNCA modifica a OWL. Apenas lê e reporta.

Uso:
    python validate_owl_logic.py <arquivo.owl> [--output logic_report.html]
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
except ImportError:
    print("ERRO: rdflib não instalado. Execute: pip install rdflib")
    sys.exit(1)


class OWLLogicValidator:
    """Validador automático de axiomas lógicos em ontologias OWL"""

    def __init__(self, owl_file):
        self.owl_file = owl_file
        self.graph = Graph()
        self.results = {}

        print(f"📖 Carregando ontologia: {owl_file}")
        try:
            self.graph.parse(owl_file, format="xml")
            print(f"✓ Ontologia carregada com sucesso")
        except Exception as e:
            print(f"✗ ERRO ao carregar ontologia: {e}")
            sys.exit(1)

        self.all_classes = set(self.graph.subjects(RDF.type, OWL.Class))
        self.all_obj_props = set(self.graph.subjects(RDF.type, OWL.ObjectProperty))
        self.all_data_props = set(self.graph.subjects(RDF.type, OWL.DatatypeProperty))

        print(f"  Classes: {len(self.all_classes)}")
        print(f"  Object Properties: {len(self.all_obj_props)}")
        print(f"  Data Properties: {len(self.all_data_props)}")

    def analyze_all(self):
        """Executa todas as análises de lógica OWL"""
        print("\n" + "="*60)
        print("VALIDAÇÃO DE AXIOMAS LÓGICOS OWL")
        print("="*60 + "\n")

        self.results['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'owl_file': str(self.owl_file),
            'validation_type': 'OWL Logic Axioms'
        }

        print("1️⃣  Analisando restrições de cardinalidade...")
        self.results['cardinality'] = self._analyze_cardinality()

        print("2️⃣  Analisando classes disjuntas...")
        self.results['disjoint_classes'] = self._analyze_disjoint_classes()

        print("3️⃣  Analisando características de propriedades...")
        self.results['property_characteristics'] = self._analyze_property_characteristics()

        print("4️⃣  Analisando restrições complexas...")
        self.results['complex_restrictions'] = self._analyze_complex_restrictions()

        print("5️⃣  Analisando propriedades inversas...")
        self.results['inverse_properties'] = self._analyze_inverse_properties()

        print("6️⃣  Calculando score de riqueza lógica...")
        self.results['logic_richness_score'] = self._calculate_logic_score()

        print("\n✅ Validação de lógica concluída!")
        return self.results

    def _analyze_cardinality(self):
        """Analisa restrições de cardinalidade"""

        restrictions = list(self.graph.subjects(RDF.type, OWL.Restriction))

        cardinality_exact = []
        cardinality_min = []
        cardinality_max = []

        for restriction in restrictions:
            # owl:cardinality (exatamente N)
            for card in self.graph.objects(restriction, OWL.cardinality):
                on_property = list(self.graph.objects(restriction, OWL.onProperty))
                if on_property:
                    cardinality_exact.append({
                        'property': str(on_property[0]).split('#')[-1],
                        'value': str(card)
                    })

            # owl:minCardinality
            for card in self.graph.objects(restriction, OWL.minCardinality):
                on_property = list(self.graph.objects(restriction, OWL.onProperty))
                if on_property:
                    cardinality_min.append({
                        'property': str(on_property[0]).split('#')[-1],
                        'value': str(card)
                    })

            # owl:maxCardinality
            for card in self.graph.objects(restriction, OWL.maxCardinality):
                on_property = list(self.graph.objects(restriction, OWL.onProperty))
                if on_property:
                    cardinality_max.append({
                        'property': str(on_property[0]).split('#')[-1],
                        'value': str(card)
                    })

        total_cardinality = len(cardinality_exact) + len(cardinality_min) + len(cardinality_max)

        return {
            'total_restrictions': len(restrictions),
            'exact_cardinality_count': len(cardinality_exact),
            'min_cardinality_count': len(cardinality_min),
            'max_cardinality_count': len(cardinality_max),
            'total_cardinality_constraints': total_cardinality,
            'coverage_percentage': (total_cardinality / len(self.all_obj_props) * 100)
                                   if self.all_obj_props else 0,
            'examples': cardinality_exact[:5]  # Primeiros 5 exemplos
        }

    def _analyze_disjoint_classes(self):
        """Analisa declarações de classes disjuntas"""

        disjoint_pairs = list(self.graph.subject_objects(OWL.disjointWith))

        # Também verifica owl:AllDisjointClasses
        disjoint_sets = list(self.graph.subjects(RDF.type, OWL.AllDisjointClasses))

        classes_with_disjoint = set()
        for subj, obj in disjoint_pairs:
            if subj in self.all_classes:
                classes_with_disjoint.add(subj)
            if obj in self.all_classes:
                classes_with_disjoint.add(obj)

        return {
            'disjoint_pairs_count': len(disjoint_pairs),
            'disjoint_sets_count': len(disjoint_sets),
            'classes_with_disjoint': len(classes_with_disjoint),
            'coverage_percentage': (len(classes_with_disjoint) / len(self.all_classes) * 100)
                                   if self.all_classes else 0,
            'warning': 'Baixa cobertura de disjunção' if len(classes_with_disjoint) < len(self.all_classes) * 0.2 else None
        }

    def _analyze_property_characteristics(self):
        """Analisa características de propriedades (funcional, simétrica, etc.)"""

        functional = set(self.graph.subjects(RDF.type, OWL.FunctionalProperty))
        inverse_functional = set(self.graph.subjects(RDF.type, OWL.InverseFunctionalProperty))
        symmetric = set(self.graph.subjects(RDF.type, OWL.SymmetricProperty))
        transitive = set(self.graph.subjects(RDF.type, OWL.TransitiveProperty))
        reflexive = set(self.graph.subjects(RDF.type, OWL.ReflexiveProperty))
        irreflexive = set(self.graph.subjects(RDF.type, OWL.IrreflexiveProperty))

        total_props = len(self.all_obj_props)
        properties_with_characteristics = functional | inverse_functional | symmetric | transitive | reflexive | irreflexive

        return {
            'functional_properties': len(functional),
            'inverse_functional_properties': len(inverse_functional),
            'symmetric_properties': len(symmetric),
            'transitive_properties': len(transitive),
            'reflexive_properties': len(reflexive),
            'irreflexive_properties': len(irreflexive),
            'total_with_characteristics': len(properties_with_characteristics),
            'coverage_percentage': (len(properties_with_characteristics) / total_props * 100)
                                   if total_props else 0,
            'examples': {
                'functional': [str(p).split('#')[-1] for p in list(functional)[:3]],
                'symmetric': [str(p).split('#')[-1] for p in list(symmetric)[:3]]
            }
        }

    def _analyze_complex_restrictions(self):
        """Analisa restrições complexas (allValuesFrom, someValuesFrom)"""

        restrictions = list(self.graph.subjects(RDF.type, OWL.Restriction))

        all_values_from = []
        some_values_from = []
        has_value = []

        for restriction in restrictions:
            # owl:allValuesFrom (∀)
            for value in self.graph.objects(restriction, OWL.allValuesFrom):
                on_property = list(self.graph.objects(restriction, OWL.onProperty))
                if on_property:
                    all_values_from.append({
                        'property': str(on_property[0]).split('#')[-1],
                        'value_class': str(value).split('#')[-1]
                    })

            # owl:someValuesFrom (∃)
            for value in self.graph.objects(restriction, OWL.someValuesFrom):
                on_property = list(self.graph.objects(restriction, OWL.onProperty))
                if on_property:
                    some_values_from.append({
                        'property': str(on_property[0]).split('#')[-1],
                        'value_class': str(value).split('#')[-1]
                    })

            # owl:hasValue
            for value in self.graph.objects(restriction, OWL.hasValue):
                on_property = list(self.graph.objects(restriction, OWL.onProperty))
                if on_property:
                    has_value.append({
                        'property': str(on_property[0]).split('#')[-1],
                        'value': str(value)
                    })

        total_complex = len(all_values_from) + len(some_values_from) + len(has_value)

        return {
            'all_values_from_count': len(all_values_from),
            'some_values_from_count': len(some_values_from),
            'has_value_count': len(has_value),
            'total_complex_restrictions': total_complex,
            'examples': {
                'all_values_from': all_values_from[:3],
                'some_values_from': some_values_from[:3]
            }
        }

    def _analyze_inverse_properties(self):
        """Analisa propriedades inversas (owl:inverseOf)"""

        inverse_pairs = list(self.graph.subject_objects(OWL.inverseOf))

        properties_with_inverse = set()
        for subj, obj in inverse_pairs:
            properties_with_inverse.add(subj)
            properties_with_inverse.add(obj)

        return {
            'inverse_pairs_count': len(inverse_pairs),
            'properties_with_inverse': len(properties_with_inverse),
            'coverage_percentage': (len(properties_with_inverse) / len(self.all_obj_props) * 100)
                                   if self.all_obj_props else 0,
            'examples': [
                {
                    'property': str(subj).split('#')[-1],
                    'inverse': str(obj).split('#')[-1]
                }
                for subj, obj in list(inverse_pairs)[:5]
            ],
            'warning': 'Baixa cobertura de inversas - dificulta queries bidirecionais'
                      if len(properties_with_inverse) < len(self.all_obj_props) * 0.3 else None
        }

    def _calculate_logic_score(self):
        """Calcula score de riqueza lógica (0-10)"""

        cardinality = self.results['cardinality']
        disjoint = self.results['disjoint_classes']
        characteristics = self.results['property_characteristics']
        restrictions = self.results['complex_restrictions']
        inverses = self.results['inverse_properties']

        # Pesos para cada categoria
        weights = {
            'cardinality': 0.25,        # Cardinalidades são críticas
            'disjoint': 0.20,           # Disjunções evitam ambiguidades
            'characteristics': 0.25,    # Características definem semântica
            'restrictions': 0.20,       # Restrições complexas para inferências
            'inverses': 0.10            # Inversas facilitam queries
        }

        # Scores individuais (0-10)
        cardinality_score = min(10, cardinality['coverage_percentage'] / 5)  # 50% coverage = 10 pontos
        disjoint_score = min(10, disjoint['coverage_percentage'] / 3)       # 30% coverage = 10 pontos
        characteristics_score = min(10, characteristics['coverage_percentage'] / 4)  # 40% coverage = 10 pontos

        # Restrições complexas (considerar se tem pelo menos algumas)
        restrictions_score = min(10, restrictions['total_complex_restrictions'] / 5)  # 50 restrições = 10 pontos

        # Inversas
        inverses_score = min(10, inverses['coverage_percentage'] / 4)  # 40% coverage = 10 pontos

        # Score total ponderado
        total_score = (
            cardinality_score * weights['cardinality'] +
            disjoint_score * weights['disjoint'] +
            characteristics_score * weights['characteristics'] +
            restrictions_score * weights['restrictions'] +
            inverses_score * weights['inverses']
        )

        # Classificação
        if total_score >= 8:
            level = "Excelente - Ontologia rica em axiomas lógicos"
        elif total_score >= 6:
            level = "Bom - Boa cobertura de axiomas"
        elif total_score >= 4:
            level = "Regular - Axiomas básicos presentes"
        else:
            level = "Precisa Melhorar - Poucos axiomas lógicos"

        return {
            'total_score': round(total_score, 2),
            'level': level,
            'breakdown': {
                'cardinality': round(cardinality_score, 2),
                'disjoint': round(disjoint_score, 2),
                'characteristics': round(characteristics_score, 2),
                'restrictions': round(restrictions_score, 2),
                'inverses': round(inverses_score, 2)
            },
            'recommendations': self._generate_recommendations(total_score)
        }

    def _generate_recommendations(self, score):
        """Gera recomendações automáticas baseadas no score"""
        recommendations = []

        cardinality = self.results['cardinality']
        disjoint = self.results['disjoint_classes']
        characteristics = self.results['property_characteristics']
        inverses = self.results['inverse_properties']

        if cardinality['coverage_percentage'] < 20:
            recommendations.append({
                'priority': 'ALTA',
                'category': 'Cardinalidade',
                'issue': f'Apenas {cardinality["total_cardinality_constraints"]} restrições de cardinalidade',
                'suggestion': 'Adicionar owl:minCardinality, owl:maxCardinality ou owl:cardinality em propriedades críticas'
            })

        if disjoint['coverage_percentage'] < 10:
            recommendations.append({
                'priority': 'ALTA',
                'category': 'Disjunção',
                'issue': f'Apenas {disjoint["classes_with_disjoint"]} classes têm owl:disjointWith',
                'suggestion': 'Declarar classes mutuamente exclusivas como disjuntas (ex: Aircraft e Airport)'
            })

        if characteristics['coverage_percentage'] < 20:
            recommendations.append({
                'priority': 'MÉDIA',
                'category': 'Características',
                'issue': f'{characteristics["total_with_characteristics"]} propriedades com características',
                'suggestion': 'Marcar propriedades como Functional, Symmetric, Transitive conforme semântica'
            })

        if inverses['coverage_percentage'] < 30:
            recommendations.append({
                'priority': 'MÉDIA',
                'category': 'Inversas',
                'issue': f'{inverses["properties_with_inverse"]} propriedades têm owl:inverseOf',
                'suggestion': 'Criar propriedades inversas (ex: hasParent ↔ isParentOf) para facilitar queries SPARQL bidirecionais'
            })

        if not recommendations:
            recommendations.append({
                'priority': 'INFO',
                'category': 'Geral',
                'issue': 'Ontologia bem axiomatizada',
                'suggestion': 'Continue mantendo a riqueza lógica nas próximas versões'
            })

        return recommendations

    def generate_html_report(self, output_file):
        """Gera relatório HTML"""

        score = self.results['logic_richness_score']
        cardinality = self.results['cardinality']
        disjoint = self.results['disjoint_classes']
        characteristics = self.results['property_characteristics']
        restrictions = self.results['complex_restrictions']
        inverses = self.results['inverse_properties']

        recommendations_html = ""
        for rec in score['recommendations']:
            priority_class = {
                'ALTA': 'priority-high',
                'MÉDIA': 'priority-medium',
                'BAIXA': 'priority-low',
                'INFO': 'priority-info'
            }.get(rec['priority'], 'priority-info')

            recommendations_html += f"""
            <div class="recommendation {priority_class}">
                <div class="rec-header">
                    <span class="priority-badge">{rec['priority']}</span>
                    <span class="category">{rec['category']}</span>
                </div>
                <div class="rec-issue">{rec['issue']}</div>
                <div class="rec-suggestion">💡 {rec['suggestion']}</div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Axiomas Lógicos OWL - AirData</title>
<!-- AirData Header Style Start -->
<!-- AirData Header Style End -->
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background: #f8fafc; color: #1f2933; margin: 0; padding: 2rem; }}
        .container {{ max-width: 980px; margin: 0 auto; background: #ffffff; border: 1px solid #e6e9ef; border-radius: 10px; padding: 2rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06); }}
        h1 {{ color: #003C7D; margin-top: 0; }}
        h2 {{ color: #003C7D; margin-top: 2rem; margin-bottom: 0.8rem; font-size: 1.3em; font-weight: 600; padding-bottom: 0.3rem; }}
        h3 {{ color: #003C7D; margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 1.1em; font-weight: 600; }}


        .recommendation {{ border: 1px solid #cccccc; padding: 1rem; margin: 1rem 0; background: #fafafa; }}
        .recommendation.priority-high {{ border-left: 4px solid #cc0000; }}
        .recommendation.priority-medium {{ border-left: 4px solid #ff8800; }}
        .recommendation.priority-info {{ border-left: 4px solid #006600; }}

        .rec-header {{ margin-bottom: 0.5rem; }}
        .priority-badge {{ display: inline-block; background: #333333; color: white; padding: 0.2rem 0.5rem; font-size: 0.85em; font-weight: 600; margin-right: 0.5rem; }}
        .category {{ color: #000000; font-weight: 600; }}
        .rec-issue {{ margin: 0.5rem 0; color: #000000; }}
        .rec-suggestion {{ margin-top: 0.5rem; padding: 0.5rem; background: white; border: 1px solid #cccccc; }}

        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ text-align: left; padding: 0.75rem; border-bottom: 1px solid #e6e9ef; }}
        th {{ width: 45%; color: #475569; font-weight: 600; }}

        .timestamp {{ color: #64748b; font-size: 0.95rem; }}
    </style>
</head>
<body>
<!-- AirData Header Start -->
<!-- AirData Header End -->
    <div class="container">
        <h1>Relatório de Axiomas Lógicos OWL</h1>

        <h2>Resumo Geral</h2>
        <table>
            <tr>
                <th style="width: 70%;">Métrica</th>
                <th style="width: 30%; text-align: center;">Valor</th>
            </tr>
            <tr>
                <td>Score Total de Riqueza Lógica</td>
                <td style="text-align: center;"><strong>{score['total_score']}/10</strong></td>
            </tr>
            <tr>
                <td>Classificação</td>
                <td style="text-align: center;">{score['level']}</td>
            </tr>
        </table>

        <h2>Detalhamento por Categoria</h2>
        <table>
            <tr>
                <th>Categoria</th>
                <th style="text-align: center;">Score</th>
            </tr>
            <tr>
                <td>Cardinalidade</td>
                <td style="text-align: center;">{score['breakdown']['cardinality']}/10</td>
            </tr>
            <tr>
                <td>Disjunção</td>
                <td style="text-align: center;">{score['breakdown']['disjoint']}/10</td>
            </tr>
            <tr>
                <td>Características de Propriedades</td>
                <td style="text-align: center;">{score['breakdown']['characteristics']}/10</td>
            </tr>
            <tr>
                <td>Restrições Complexas</td>
                <td style="text-align: center;">{score['breakdown']['restrictions']}/10</td>
            </tr>
            <tr>
                <td>Propriedades Inversas</td>
                <td style="text-align: center;">{score['breakdown']['inverses']}/10</td>
            </tr>
        </table>

        <h2>Análise Detalhada</h2>

        <h3>Restrições de Cardinalidade</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Total de restrições OWL</td><td>{cardinality['total_restrictions']}</td></tr>
            <tr><td>owl:cardinality (exata)</td><td>{cardinality['exact_cardinality_count']}</td></tr>
            <tr><td>owl:minCardinality</td><td>{cardinality['min_cardinality_count']}</td></tr>
            <tr><td>owl:maxCardinality</td><td>{cardinality['max_cardinality_count']}</td></tr>
            <tr><td>Cobertura (% propriedades)</td><td>{cardinality['coverage_percentage']:.1f}%</td></tr>
        </table>

        <h3>Classes Disjuntas</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Pares disjuntos (owl:disjointWith)</td><td>{disjoint['disjoint_pairs_count']}</td></tr>
            <tr><td>Conjuntos disjuntos (owl:AllDisjointClasses)</td><td>{disjoint['disjoint_sets_count']}</td></tr>
            <tr><td>Classes com disjunção</td><td>{disjoint['classes_with_disjoint']}</td></tr>
            <tr><td>Cobertura (% classes)</td><td>{disjoint['coverage_percentage']:.1f}%</td></tr>
        </table>

        <h3>Características de Propriedades</h3>
        <table>
            <tr><th>Tipo</th><th>Quantidade</th></tr>
            <tr><td>Functional</td><td>{characteristics['functional_properties']}</td></tr>
            <tr><td>Inverse Functional</td><td>{characteristics['inverse_functional_properties']}</td></tr>
            <tr><td>Symmetric</td><td>{characteristics['symmetric_properties']}</td></tr>
            <tr><td>Transitive</td><td>{characteristics['transitive_properties']}</td></tr>
            <tr><td>Reflexive</td><td>{characteristics['reflexive_properties']}</td></tr>
            <tr><td>Irreflexive</td><td>{characteristics['irreflexive_properties']}</td></tr>
            <tr><td><strong>Total com características</strong></td><td><strong>{characteristics['total_with_characteristics']}</strong></td></tr>
        </table>

        <h3>Restrições Complexas</h3>
        <table>
            <tr><th>Tipo</th><th>Quantidade</th></tr>
            <tr><td>owl:allValuesFrom (∀)</td><td>{restrictions['all_values_from_count']}</td></tr>
            <tr><td>owl:someValuesFrom (∃)</td><td>{restrictions['some_values_from_count']}</td></tr>
            <tr><td>owl:hasValue</td><td>{restrictions['has_value_count']}</td></tr>
            <tr><td><strong>Total</strong></td><td><strong>{restrictions['total_complex_restrictions']}</strong></td></tr>
        </table>

        <h3>Propriedades Inversas</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Pares de inversas (owl:inverseOf)</td><td>{inverses['inverse_pairs_count']}</td></tr>
            <tr><td>Propriedades com inversa</td><td>{inverses['properties_with_inverse']}</td></tr>
            <tr><td>Cobertura (% propriedades)</td><td>{inverses['coverage_percentage']:.1f}%</td></tr>
        </table>

        <h2>💡 Recomendações para Próxima Versão</h2>
        {recommendations_html}

        <div class="timestamp">
            Relatório gerado automaticamente em {self.results['metadata']['timestamp']}<br>
            Arquivo analisado: {self.results['metadata']['owl_file']}<br>
            <strong>IMPORTANTE:</strong> Este relatório apenas diagnostica. Edições devem ser feitas manualmente no Protégé.
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
        description='Validação automatizada de axiomas lógicos OWL (SEM modificar a ontologia)'
    )
    parser.add_argument('owl_file', help='Arquivo OWL a ser analisado')
    parser.add_argument('--output', default='logic_report.html',
                       help='Arquivo HTML de saída (default: logic_report.html)')
    parser.add_argument('--json', help='Salvar resultados também em JSON')

    args = parser.parse_args()

    # Verificar se arquivo existe
    if not Path(args.owl_file).exists():
        print(f"❌ ERRO: Arquivo não encontrado: {args.owl_file}")
        sys.exit(1)

    # Executar validação
    validator = OWLLogicValidator(args.owl_file)
    results = validator.analyze_all()

    # Gerar relatório HTML
    validator.generate_html_report(args.output)

    # Salvar JSON se solicitado
    if args.json:
        validator.save_json(args.json)

    # Mostrar resumo no terminal
    print("\n" + "="*60)
    print("RESUMO DA VALIDAÇÃO LÓGICA")
    print("="*60)
    score = results['logic_richness_score']
    print(f"\n🎯 SCORE GERAL: {score['total_score']}/10 ({score['level']})")
    print(f"\n   Cardinalidade:  {score['breakdown']['cardinality']}/10")
    print(f"   Disjunção:      {score['breakdown']['disjoint']}/10")
    print(f"   Características:{score['breakdown']['characteristics']}/10")
    print(f"   Restrições:     {score['breakdown']['restrictions']}/10")
    print(f"   Inversas:       {score['breakdown']['inverses']}/10")

    print(f"\n📋 {len(score['recommendations'])} recomendações geradas")
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
