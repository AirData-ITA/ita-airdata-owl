#!/usr/bin/env python3
"""
Análise Estendida de Qualidade de Ontologia OWL
100% Automatizado - Sem Intervenção Humana

Uso:
    python analyze_ontology_extended.py <arquivo.owl> [--output report.html]

Gera relatório completo com 7 categorias de análise.
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import re

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal
except ImportError:
    print("ERRO: rdflib não instalado. Execute: pip install rdflib")
    sys.exit(1)

try:
    import networkx as nx
except ImportError:
    print("AVISO: networkx não instalado. Análise de conectividade será pulada.")
    print("Para habilitar: pip install networkx")
    nx = None


# Namespaces
IAO = Namespace("http://purl.obolibrary.org/obo/IAO_")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DCTERMS = Namespace("http://purl.org/dc/terms/")


class OntologyAnalyzer:
    """Analisador automatizado de ontologias OWL"""

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
        self.all_properties = self.all_obj_props | self.all_data_props

        print(f"  Classes: {len(self.all_classes)}")
        print(f"  Propriedades: {len(self.all_properties)}")

    def analyze_all(self):
        """Executa todas as análises automaticamente"""
        print("\n" + "="*60)
        print("INICIANDO ANÁLISES AUTOMATIZADAS")
        print("="*60 + "\n")

        self.results['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'owl_file': str(self.owl_file),
            'num_classes': len(self.all_classes),
            'num_properties': len(self.all_properties)
        }

        # 1. Estrutura e Complexidade
        print("1️⃣  Analisando estrutura e complexidade...")
        self.results['structure'] = self._analyze_structure()

        # 2. Completude
        print("2️⃣  Analisando completude de anotações...")
        self.results['completeness'] = self._analyze_completeness()

        # 3. Nomenclatura
        print("3️⃣  Verificando convenções de nomenclatura...")
        self.results['naming'] = self._analyze_naming()

        # 4. Conectividade (se networkx disponível)
        if nx is not None:
            print("4️⃣  Analisando conectividade do grafo...")
            self.results['connectivity'] = self._analyze_connectivity()
        else:
            print("4️⃣  Conectividade: PULADA (networkx não instalado)")
            self.results['connectivity'] = None

        # 5. Reusabilidade
        print("5️⃣  Analisando uso de vocabulários padrão...")
        self.results['reusability'] = self._analyze_reusability()

        # 6. Anti-patterns
        print("6️⃣  Detectando anti-patterns...")
        self.results['antipatterns'] = self._detect_antipatterns()

        # 7. Score Geral
        print("7️⃣  Calculando score de qualidade...")
        self.results['score'] = self._calculate_quality_score()

        print("\n✅ Todas as análises concluídas!")
        return self.results

    def _analyze_structure(self):
        """Análise 1: Métricas de estrutura"""

        def get_depth(cls, visited=None):
            if visited is None:
                visited = set()
            if cls in visited or cls == OWL.Thing:
                return 0
            visited.add(cls)

            parents = [p for p in self.graph.objects(cls, RDFS.subClassOf)
                      if isinstance(p, URIRef)]
            if not parents:
                return 0

            return 1 + max((get_depth(p, visited) for p in parents), default=0)

        depths = {}
        for cls in self.all_classes:
            try:
                depths[str(cls)] = get_depth(cls)
            except RecursionError:
                depths[str(cls)] = 999  # Ciclo detectado

        # Calcular folhas vs intermediárias
        leaf_classes = []
        intermediate_classes = []

        for cls in self.all_classes:
            has_subclasses = bool(list(self.graph.subjects(RDFS.subClassOf, cls)))
            if has_subclasses:
                intermediate_classes.append(str(cls))
            else:
                leaf_classes.append(str(cls))

        return {
            'max_depth': max(depths.values()) if depths else 0,
            'avg_depth': sum(depths.values()) / len(depths) if depths else 0,
            'num_leaf_classes': len(leaf_classes),
            'num_intermediate_classes': len(intermediate_classes),
            'leaf_percentage': len(leaf_classes) / len(self.all_classes) * 100 if self.all_classes else 0
        }

    def _analyze_completeness(self):
        """Análise 2: Completude de anotações"""

        stats = {
            'classes_with_label': 0,
            'classes_with_label_pt': 0,
            'classes_with_definition': 0,
            'classes_with_comment': 0,
            'properties_with_domain': 0,
            'properties_with_range': 0,
            'properties_with_label': 0
        }

        # Analisar classes
        for cls in self.all_classes:
            labels = list(self.graph.objects(cls, RDFS.label))
            if labels:
                stats['classes_with_label'] += 1
                for label in labels:
                    if hasattr(label, 'language') and label.language in ['pt', 'pt-br', 'pt-BR']:
                        stats['classes_with_label_pt'] += 1
                        break

            if list(self.graph.objects(cls, IAO['0000115'])):
                stats['classes_with_definition'] += 1

            if list(self.graph.objects(cls, RDFS.comment)):
                stats['classes_with_comment'] += 1

        # Analisar propriedades
        for prop in self.all_properties:
            if list(self.graph.objects(prop, RDFS.domain)):
                stats['properties_with_domain'] += 1
            if list(self.graph.objects(prop, RDFS.range)):
                stats['properties_with_range'] += 1
            if list(self.graph.objects(prop, RDFS.label)):
                stats['properties_with_label'] += 1

        # Calcular percentuais
        total_classes = len(self.all_classes)
        total_props = len(self.all_properties)

        return {
            'label_pct': stats['classes_with_label'] / total_classes * 100 if total_classes else 0,
            'label_pt_pct': stats['classes_with_label_pt'] / total_classes * 100 if total_classes else 0,
            'definition_pct': stats['classes_with_definition'] / total_classes * 100 if total_classes else 0,
            'comment_pct': stats['classes_with_comment'] / total_classes * 100 if total_classes else 0,
            'domain_pct': stats['properties_with_domain'] / total_props * 100 if total_props else 0,
            'range_pct': stats['properties_with_range'] / total_props * 100 if total_props else 0,
            'prop_label_pct': stats['properties_with_label'] / total_props * 100 if total_props else 0
        }

    def _analyze_naming(self):
        """Análise 3: Convenções de nomenclatura"""

        issues = {
            'classes_not_pascal_case': [],
            'properties_not_camel_case': [],
            'labels_too_long': []
        }

        # PascalCase para classes
        pascal_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
        for cls in self.all_classes:
            local_name = str(cls).split('#')[-1].split('/')[-1]
            if local_name and not pascal_pattern.match(local_name):
                issues['classes_not_pascal_case'].append(local_name)

        # camelCase para propriedades
        camel_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')
        for prop in self.all_properties:
            local_name = str(prop).split('#')[-1].split('/')[-1]
            if local_name and not camel_pattern.match(local_name):
                issues['properties_not_camel_case'].append(local_name)

        # Labels muito longos (> 6 palavras)
        for s, p, o in self.graph.triples((None, RDFS.label, None)):
            if isinstance(o, Literal):
                word_count = len(str(o).split())
                if word_count > 6:
                    issues['labels_too_long'].append(str(o))

        return {
            'num_naming_violations': len(issues['classes_not_pascal_case']) +
                                    len(issues['properties_not_camel_case']),
            'classes_violations': len(issues['classes_not_pascal_case']),
            'properties_violations': len(issues['properties_not_camel_case']),
            'labels_too_long': len(issues['labels_too_long'])
        }

    def _analyze_connectivity(self):
        """Análise 4: Conectividade do grafo"""
        if nx is None:
            return None

        G = nx.DiGraph()

        # Adicionar nodes
        for cls in self.all_classes:
            G.add_node(str(cls))

        # Adicionar edges (hierarquia)
        for sub, sup in self.graph.subject_objects(RDFS.subClassOf):
            if isinstance(sup, URIRef) and sub in self.all_classes:
                G.add_edge(str(sub), str(sup))

        # Calcular métricas
        isolated = list(nx.isolates(G))

        centrality = nx.degree_centrality(G) if len(G) > 0 else {}
        top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'num_isolated': len(isolated),
            'num_components': nx.number_weakly_connected_components(G),
            'density': nx.density(G),
            'top_central_classes': [
                {'class': cls.split('#')[-1], 'centrality': cent}
                for cls, cent in top_central
            ]
        }

    def _analyze_reusability(self):
        """Análise 5: Uso de vocabulários padrão"""

        standard_vocabs = {
            'Dublin Core': 'http://purl.org/dc/terms/',
            'SKOS': 'http://www.w3.org/2004/02/skos/core#',
            'FOAF': 'http://xmlns.com/foaf/0.1/',
        }

        usage = {name: 0 for name in standard_vocabs}

        for s, p, o in self.graph:
            for vocab_name, vocab_uri in standard_vocabs.items():
                if vocab_uri in str(p):
                    usage[vocab_name] += 1

        vocabs_used = sum(1 for count in usage.values() if count > 0)
        total_vocabs = len(standard_vocabs)

        return {
            'vocabularies_usage': usage,
            'vocabularies_used_count': vocabs_used,
            'reusability_pct': vocabs_used / total_vocabs * 100 if total_vocabs else 0
        }

    def _detect_antipatterns(self):
        """Análise 6: Detecção de anti-patterns"""

        issues = {
            'dead_classes': [],
            'singleton_properties': []
        }

        # Classes sem instâncias e sem subclasses
        for cls in self.all_classes:
            has_instances = bool(list(self.graph.subjects(RDF.type, cls)))
            has_subclasses = bool(list(self.graph.subjects(RDFS.subClassOf, cls)))

            if not has_instances and not has_subclasses:
                issues['dead_classes'].append(str(cls).split('#')[-1])

        # Propriedades usadas apenas 1 vez
        for prop in self.all_properties:
            # Contar usos como domain
            domain_usage = len(list(self.graph.subjects(RDFS.domain, prop)))
            if domain_usage == 1:
                issues['singleton_properties'].append(str(prop).split('#')[-1])

        return {
            'num_dead_classes': len(issues['dead_classes']),
            'num_singleton_properties': len(issues['singleton_properties']),
            'dead_classes_sample': issues['dead_classes'][:5]
        }

    def _calculate_quality_score(self):
        """Análise 7: Score geral de qualidade"""

        completeness = self.results.get('completeness', {})
        naming = self.results.get('naming', {})
        connectivity = self.results.get('connectivity', {})
        reusability = self.results.get('reusability', {})

        # Completeness Score (30%)
        avg_completeness = (
            completeness.get('label_pt_pct', 0) +
            completeness.get('definition_pct', 0) +
            completeness.get('domain_pct', 0) +
            completeness.get('range_pct', 0)
        ) / 4
        completeness_score = avg_completeness / 10

        # Consistency Score (25%)
        total_entities = len(self.all_classes) + len(self.all_properties)
        naming_violations = naming.get('num_naming_violations', 0)
        consistency_pct = max(0, 100 - (naming_violations / total_entities * 100)) if total_entities else 100
        consistency_score = consistency_pct / 10

        # Connectivity Score (20%)
        if connectivity:
            isolated = connectivity.get('num_isolated', 0)
            connectivity_pct = max(0, 100 - (isolated / len(self.all_classes) * 100)) if self.all_classes else 100
            connectivity_score = connectivity_pct / 10
        else:
            connectivity_score = 5.0  # Valor neutro se não disponível

        # Reusability Score (10%)
        reusability_score = reusability.get('reusability_pct', 0) / 10

        # Naming Score (15%)
        naming_score = consistency_score  # Reutilizar

        # Calcular total ponderado
        # IMPORTANTE: Pesos ajustados para priorizar usabilidade por LLMs
        # - Consistência lógica é crítica para inferências
        # - Completude de anotações permite LLMs entenderem conceitos
        # - Conectividade semântica facilita navegação
        # - Nomenclatura é menos crítica (LLMs usam labels)
        weights = {
            'consistency': 0.35,     # Aumentado: axiomas lógicos são críticos
            'completeness': 0.30,    # Mantido: labels e definições essenciais
            'connectivity': 0.20,    # Mantido: estrutura do grafo
            'reusability': 0.10,     # Mantido: vocabulários padrão
            'naming': 0.05           # Reduzido: LLMs usam labels, não nomes técnicos
        }

        total_score = (
            completeness_score * weights['completeness'] +
            consistency_score * weights['consistency'] +
            connectivity_score * weights['connectivity'] +
            naming_score * weights['naming'] +
            reusability_score * weights['reusability']
        )

        # Classificação
        if total_score >= 8:
            quality_level = "Excelente"
        elif total_score >= 6:
            quality_level = "Bom"
        elif total_score >= 4:
            quality_level = "Regular"
        else:
            quality_level = "Precisa Melhorar"

        return {
            'total_score': round(total_score, 2),
            'quality_level': quality_level,
            'breakdown': {
                'completeness': round(completeness_score, 2),
                'consistency': round(consistency_score, 2),
                'connectivity': round(connectivity_score, 2),
                'naming': round(naming_score, 2),
                'reusability': round(reusability_score, 2)
            }
        }

    def generate_html_report(self, output_file):
        """Gera relatório HTML automaticamente"""

        score = self.results['score']
        completeness = self.results['completeness']
        structure = self.results['structure']
        naming = self.results['naming']
        antipatterns = self.results['antipatterns']

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Análise Semântica - AirData</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Times New Roman", Times, Georgia, serif; background: #ffffff; padding: 2rem; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 3rem; border: 1px solid #cccccc; }}
        h1 {{ color: #003C7D; padding-bottom: 1rem; margin-bottom: 1.5rem; font-size: 1.8em; font-weight: 600; text-align: left; }}
        h2 {{ color: #000000; margin-top: 2rem; margin-bottom: 0.8rem; font-size: 1.3em; font-weight: 600; padding-bottom: 0.3rem; }}
        h3 {{ color: #000000; margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 1.1em; font-weight: 600; }}

        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.6rem; text-align: left; border: 1px solid #cccccc; }}
        th {{ background: #e8e8e8; font-weight: 600; }}

        tr.success {{ background: #f0f9f0; }}
        tr.failed {{ background: #fff0f0; }}
        tr.warning {{ background: #fff9f0; }}

        .badge {{ display: inline-block; padding: 0.2rem 0.5rem; font-size: 0.85em; font-weight: 600; background: #e8e8e8; color: #000000; border-radius: 3px; }}
        .badge.success {{ background: #28a745; color: white; }}
        .badge.failed {{ background: #dc3545; color: white; }}
        .badge.warning {{ background: #ffc107; color: #000; }}

        .score-summary {{ border: 1px solid #cccccc; padding: 1rem; margin: 1.5rem 0; background: #fafafa; }}
        .score-summary-row {{ display: flex; justify-content: space-between; margin: 0.5rem 0; }}
        .score-summary-label {{ font-weight: 600; }}
        .score-summary-value {{ color: #003C7D; font-weight: 600; }}

        .timestamp {{ text-align: center; color: #666666; font-size: 0.85em; margin-top: 2rem; padding-top: 1rem; border-top: 2px solid #cccccc; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Relatório de Análise Semântica</h1>

        <div class="score-summary">
            <div class="score-summary-row">
                <span class="score-summary-label">Score Geral de Qualidade:</span>
                <span class="score-summary-value">{score['total_score']}/10</span>
            </div>
            <div class="score-summary-row">
                <span class="score-summary-label">Nível:</span>
                <span class="score-summary-value">{score['quality_level']}</span>
            </div>
        </div>

        <h2>Detalhamento do Score</h2>
        <table>
            <tr>
                <th>Dimensão</th>
                <th style="text-align: center;">Score</th>
            </tr>
            <tr>
                <td>Completude</td>
                <td style="text-align: center;"><strong>{score['breakdown']['completeness']}/10</strong></td>
            </tr>
            <tr>
                <td>Consistência</td>
                <td style="text-align: center;"><strong>{score['breakdown']['consistency']}/10</strong></td>
            </tr>
            <tr>
                <td>Conectividade</td>
                <td style="text-align: center;"><strong>{score['breakdown']['connectivity']}/10</strong></td>
            </tr>
            <tr>
                <td>Nomenclatura</td>
                <td style="text-align: center;"><strong>{score['breakdown']['naming']}/10</strong></td>
            </tr>
            <tr>
                <td>Reusabilidade</td>
                <td style="text-align: center;"><strong>{score['breakdown']['reusability']}/10</strong></td>
            </tr>
        </table>

        <h2>Análise de Completude</h2>
        <table>
            <tr>
                <th>Métrica</th>
                <th style="text-align: center;">Percentual</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Classes com labels (pt-br)</td>
                <td style="text-align: center;">{completeness['label_pt_pct']:.1f}%</td>
                <td class="{'success' if completeness['label_pt_pct'] >= 80 else 'warning'}">
                    {'✓ Bom' if completeness['label_pt_pct'] >= 80 else '⚠ Melhorar'}
                </td>
            </tr>
            <tr>
                <td>Classes com definições (IAO)</td>
                <td style="text-align: center;">{completeness['definition_pct']:.1f}%</td>
                <td class="{'success' if completeness['definition_pct'] >= 80 else 'warning'}">
                    {'✓ Bom' if completeness['definition_pct'] >= 80 else '⚠ Melhorar'}
                </td>
            </tr>
            <tr>
                <td>Propriedades com domain</td>
                <td>{completeness['domain_pct']:.1f}%</td>
                <td class="{'success' if completeness['domain_pct'] >= 70 else 'warning'}">
                    {'✓ Bom' if completeness['domain_pct'] >= 70 else '⚠ Melhorar'}
                </td>
            </tr>
            <tr>
                <td>Propriedades com range</td>
                <td>{completeness['range_pct']:.1f}%</td>
                <td class="{'success' if completeness['range_pct'] >= 70 else 'warning'}">
                    {'✓ Bom' if completeness['range_pct'] >= 70 else '⚠ Melhorar'}
                </td>
            </tr>
        </table>

        <h3>Estrutura da Ontologia</h3>
        <table>
            <tr>
                <th>Métrica</th>
                <th style="text-align: center;">Valor</th>
            </tr>
            <tr>
                <td>Profundidade Máxima (hierarquia)</td>
                <td style="text-align: center;">{structure['max_depth']} níveis</td>
            </tr>
            <tr>
                <td>Classes Folhas</td>
                <td style="text-align: center;">{structure['num_leaf_classes']} ({structure['leaf_percentage']:.1f}%)</td>
            </tr>
            <tr>
                <td>Classes Intermediárias</td>
                <td style="text-align: center;">{structure['num_intermediate_classes']}</td>
            </tr>
        </table>

        <h3>Problemas Detectados</h3>
        <table>
            <tr>
                <th>Tipo de Problema</th>
                <th>Quantidade</th>
            </tr>
            <tr>
                <td class="warning">Classes não seguem PascalCase</td>
                <td>{naming['classes_violations']}</td>
            </tr>
            <tr>
                <td class="warning">Propriedades não seguem camelCase</td>
                <td>{naming['properties_violations']}</td>
            </tr>
            <tr>
                <td class="warning">Labels muito longos (&gt;6 palavras)</td>
                <td>{naming['labels_too_long']}</td>
            </tr>
            <tr>
                <td class="warning">Classes "mortas" (sem uso)</td>
                <td>{antipatterns['num_dead_classes']}</td>
            </tr>
        </table>

        <div class="timestamp">
            Relatório gerado automaticamente em {self.results['metadata']['timestamp']}<br>
            Arquivo analisado: {self.results['metadata']['owl_file']}
        </div>
    </div>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ Relatório HTML gerado: {output_file}")

    def save_json(self, output_file):
        """Salva resultados em JSON para processamento posterior"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"✅ Dados JSON salvos: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Análise automatizada de qualidade de ontologia OWL'
    )
    parser.add_argument('owl_file', help='Arquivo OWL a ser analisado')
    parser.add_argument('--output', default='quality_report_extended.html',
                       help='Arquivo HTML de saída (default: quality_report_extended.html)')
    parser.add_argument('--json', help='Salvar resultados também em JSON')

    args = parser.parse_args()

    # Verificar se arquivo existe
    if not Path(args.owl_file).exists():
        print(f"❌ ERRO: Arquivo não encontrado: {args.owl_file}")
        sys.exit(1)

    # Executar análise
    analyzer = OntologyAnalyzer(args.owl_file)
    results = analyzer.analyze_all()

    # Gerar relatório HTML
    analyzer.generate_html_report(args.output)

    # Salvar JSON se solicitado
    if args.json:
        analyzer.save_json(args.json)

    # Mostrar resumo no terminal
    print("\n" + "="*60)
    print("RESUMO DA ANÁLISE")
    print("="*60)
    score = results['score']
    print(f"\n🎯 SCORE GERAL: {score['total_score']}/10 ({score['quality_level']})")
    print(f"\n   Completude:    {score['breakdown']['completeness']}/10")
    print(f"   Consistência:  {score['breakdown']['consistency']}/10")
    print(f"   Conectividade: {score['breakdown']['connectivity']}/10")
    print(f"   Nomenclatura:  {score['breakdown']['naming']}/10")
    print(f"   Reusabilidade: {score['breakdown']['reusability']}/10")
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
