#!/usr/bin/env python3
"""
Validação de LLM-Readability para Ontologias OWL
100% Automatizado - Sem Modificação da OWL

Analisa métricas específicas para uso da ontologia por LLMs em consultas SPARQL:
- Cobertura multilíngue (labels pt/en)
- Qualidade de definições (comprimento, exemplos, clareza)
- Alinhamentos externos (owl:sameAs para DBpedia, Wikidata, etc.)
- Query-friendliness (propriedades inversas, clareza de nomes)
- Ambiguidade de nomenclatura

IMPORTANTE: Este script NUNCA modifica a OWL. Apenas lê e reporta.

Uso:
    python validate_llm_readability.py <arquivo.owl> [--output llm_readability.html]
"""

import sys
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from collections import Counter

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal
except ImportError:
    print("ERRO: rdflib não instalado. Execute: pip install rdflib")
    sys.exit(1)


# Namespaces comuns
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
IAO = Namespace("http://purl.obolibrary.org/obo/IAO_")


class LLMReadabilityValidator:
    """Validador de usabilidade de ontologia para LLMs"""

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
        self.all_entities = self.all_classes | self.all_obj_props | self.all_data_props

        print(f"  Total de entidades: {len(self.all_entities)}")

    def analyze_all(self):
        """Executa todas as análises de LLM-readability"""
        print("\n" + "="*60)
        print("VALIDAÇÃO DE LLM-READABILITY")
        print("="*60 + "\n")

        self.results['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'owl_file': str(self.owl_file),
            'validation_type': 'LLM Readability'
        }

        print("1️⃣  Analisando cobertura multilíngue...")
        self.results['multilingual'] = self._analyze_multilingual_coverage()

        print("2️⃣  Analisando qualidade de definições...")
        self.results['definitions'] = self._analyze_definition_quality()

        print("3️⃣  Analisando alinhamentos externos...")
        self.results['alignments'] = self._analyze_external_alignments()

        print("4️⃣  Analisando query-friendliness...")
        self.results['query_friendliness'] = self._analyze_query_friendliness()

        print("5️⃣  Detectando ambiguidades de nomenclatura...")
        self.results['naming_ambiguity'] = self._analyze_naming_ambiguity()

        print("6️⃣  Calculando score de LLM-readability...")
        self.results['llm_readability_score'] = self._calculate_readability_score()

        print("\n✅ Validação de LLM-readability concluída!")
        return self.results

    def _analyze_multilingual_coverage(self):
        """Analisa cobertura de labels em múltiplos idiomas"""

        entities_with_pt = 0
        entities_with_en = 0
        entities_with_both = 0
        entities_without_any = 0

        for entity in self.all_entities:
            labels = list(self.graph.objects(entity, RDFS.label))

            has_pt = any(
                hasattr(label, 'language') and label.language in ['pt', 'pt-br', 'pt-BR']
                for label in labels
            )
            has_en = any(
                hasattr(label, 'language') and label.language == 'en'
                for label in labels
            )

            if has_pt:
                entities_with_pt += 1
            if has_en:
                entities_with_en += 1
            if has_pt and has_en:
                entities_with_both += 1
            if not labels:
                entities_without_any += 1

        total = len(self.all_entities)

        return {
            'entities_with_pt_label': entities_with_pt,
            'entities_with_en_label': entities_with_en,
            'entities_with_both_languages': entities_with_both,
            'entities_without_label': entities_without_any,
            'pt_coverage_pct': (entities_with_pt / total * 100) if total else 0,
            'en_coverage_pct': (entities_with_en / total * 100) if total else 0,
            'bilingual_coverage_pct': (entities_with_both / total * 100) if total else 0,
            'warning': 'Baixa cobertura bilíngue - LLMs podem não entender em inglês'
                      if entities_with_both < total * 0.5 else None
        }

    def _analyze_definition_quality(self):
        """Analisa qualidade de definições textuais"""

        # Propriedades de definição
        definition_properties = [
            RDFS.comment,
            IAO['0000115'],  # IAO definition
            SKOS.definition,
            DCTERMS.description
        ]

        entities_with_definition = 0
        short_definitions = 0  # < 20 palavras
        medium_definitions = 0  # 20-100 palavras
        long_definitions = 0  # > 100 palavras
        definitions_with_examples = 0

        definition_lengths = []

        for entity in self.all_entities:
            has_def = False

            for def_prop in definition_properties:
                definitions = list(self.graph.objects(entity, def_prop))

                for definition in definitions:
                    if isinstance(definition, Literal):
                        has_def = True
                        text = str(definition)
                        word_count = len(text.split())
                        definition_lengths.append(word_count)

                        if word_count < 20:
                            short_definitions += 1
                        elif word_count <= 100:
                            medium_definitions += 1
                        else:
                            long_definitions += 1

                        # Detecta exemplos (busca por "ex:", "exemplo", "e.g.", "for example")
                        if re.search(r'\b(ex:|exemplo|e\.g\.|for example|such as)\b', text.lower()):
                            definitions_with_examples += 1
                            break  # Conta apenas uma vez por entidade

            if has_def:
                entities_with_definition += 1

        total = len(self.all_entities)
        avg_length = sum(definition_lengths) / len(definition_lengths) if definition_lengths else 0

        return {
            'entities_with_definition': entities_with_definition,
            'definition_coverage_pct': (entities_with_definition / total * 100) if total else 0,
            'short_definitions': short_definitions,
            'medium_definitions': medium_definitions,
            'long_definitions': long_definitions,
            'avg_definition_length_words': round(avg_length, 1),
            'definitions_with_examples': definitions_with_examples,
            'examples_coverage_pct': (definitions_with_examples / total * 100) if total else 0,
            'warning': 'Poucas definições com exemplos - LLMs se beneficiam de exemplos concretos'
                      if definitions_with_examples < total * 0.2 else None
        }

    def _analyze_external_alignments(self):
        """Analisa alinhamentos com ontologias/bases externas"""

        # Links externos comuns
        sameas_links = list(self.graph.subject_objects(OWL.sameAs))

        # URIs externas conhecidas
        external_sources = {
            'DBpedia': 'dbpedia.org',
            'Wikidata': 'wikidata.org',
            'Schema.org': 'schema.org',
            'FOAF': 'xmlns.com/foaf',
            'Dublin Core': 'purl.org/dc'
        }

        alignments_by_source = {source: 0 for source in external_sources}
        total_alignments = len(sameas_links)

        for subj, obj in sameas_links:
            for source_name, source_uri in external_sources.items():
                if source_uri in str(obj):
                    alignments_by_source[source_name] += 1

        entities_with_sameas = len(set([subj for subj, obj in sameas_links]))

        return {
            'total_sameas_links': total_alignments,
            'entities_with_sameas': entities_with_sameas,
            'alignment_coverage_pct': (entities_with_sameas / len(self.all_entities) * 100)
                                      if self.all_entities else 0,
            'alignments_by_source': alignments_by_source,
            'warning': 'Sem alinhamentos externos - LLMs não podem conectar com conhecimento externo'
                      if total_alignments == 0 else None
        }

    def _analyze_query_friendliness(self):
        """Analisa facilidade de construir queries SPARQL"""

        # 1. Propriedades com inversas (facilita queries bidirecionais)
        inverse_pairs = list(self.graph.subject_objects(OWL.inverseOf))
        props_with_inverse = set()
        for subj, obj in inverse_pairs:
            props_with_inverse.add(subj)
            props_with_inverse.add(obj)

        # 2. Propriedades com domain/range claros
        props_with_domain = set(self.graph.subjects(RDFS.domain, None))
        props_with_range = set(self.graph.subjects(RDFS.range, None))
        props_with_both = props_with_domain & props_with_range

        # 3. Classes com labels curtos (< 30 caracteres, fáceis de lembrar)
        classes_with_short_labels = 0
        for cls in self.all_classes:
            labels = list(self.graph.objects(cls, RDFS.label))
            if any(len(str(label)) < 30 for label in labels):
                classes_with_short_labels += 1

        total_props = len(self.all_obj_props)
        total_classes = len(self.all_classes)

        return {
            'properties_with_inverse': len(props_with_inverse),
            'inverse_coverage_pct': (len(props_with_inverse) / total_props * 100) if total_props else 0,
            'properties_with_domain_and_range': len(props_with_both),
            'domain_range_coverage_pct': (len(props_with_both) / total_props * 100) if total_props else 0,
            'classes_with_short_labels': classes_with_short_labels,
            'short_label_pct': (classes_with_short_labels / total_classes * 100) if total_classes else 0,
            'warning': 'Poucas propriedades inversas - dificulta queries bidirecionais (ex: ?parent :hasChild ?x vs ?x :isChildOf ?parent)'
                      if len(props_with_inverse) < total_props * 0.3 else None
        }

    def _analyze_naming_ambiguity(self):
        """Detecta ambiguidades em nomes de entidades"""

        # 1. Nomes muito genéricos (podem causar confusão)
        generic_words = ['Thing', 'Entity', 'Object', 'Item', 'Data', 'Info', 'Value', 'Property']

        potentially_ambiguous = []
        for entity in self.all_entities:
            local_name = str(entity).split('#')[-1].split('/')[-1]

            for generic in generic_words:
                if generic.lower() in local_name.lower():
                    potentially_ambiguous.append(local_name)
                    break

        # 2. Nomes muito similares (diferem por 1-2 caracteres)
        all_names = [str(e).split('#')[-1].split('/')[-1] for e in self.all_entities]
        name_counter = Counter(all_names)
        duplicates = [name for name, count in name_counter.items() if count > 1]

        # 3. Nomes sem contexto (1 palavra apenas, sem prefixo)
        single_word_names = []
        for name in all_names:
            # Remove camelCase/PascalCase
            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', name)
            if len(words) == 1:
                single_word_names.append(name)

        return {
            'potentially_ambiguous_names': len(potentially_ambiguous),
            'ambiguous_examples': potentially_ambiguous[:10],
            'duplicate_names': len(duplicates),
            'duplicate_examples': duplicates[:10],
            'single_word_names': len(single_word_names),
            'single_word_pct': (len(single_word_names) / len(all_names) * 100) if all_names else 0,
            'warning': 'Muitos nomes de palavra única - podem ser ambíguos fora de contexto'
                      if len(single_word_names) > len(all_names) * 0.5 else None
        }

    def _calculate_readability_score(self):
        """Calcula score geral de LLM-readability (0-10)"""

        multilingual = self.results['multilingual']
        definitions = self.results['definitions']
        alignments = self.results['alignments']
        query_friendly = self.results['query_friendliness']
        naming = self.results['naming_ambiguity']

        # Pesos para cada categoria
        weights = {
            'multilingual': 0.25,       # Crítico para LLMs multilíngues
            'definitions': 0.30,        # Definições claras são essenciais
            'alignments': 0.15,         # Conectar com conhecimento externo
            'query_friendly': 0.20,     # Facilidade de queries
            'naming_clarity': 0.10      # Clareza de nomes
        }

        # Scores individuais (0-10)
        multilingual_score = min(10, multilingual['bilingual_coverage_pct'] / 8)  # 80% = 10pts

        # Definições: combina cobertura + qualidade (exemplos)
        def_coverage = definitions['definition_coverage_pct'] / 10  # 100% = 10pts
        def_quality = definitions['examples_coverage_pct'] / 5  # 50% com exemplos = 10pts
        definitions_score = min(10, (def_coverage + def_quality) / 2)

        alignments_score = min(10, alignments['alignment_coverage_pct'] / 3)  # 30% = 10pts

        # Query-friendliness: média de inversas + domain/range
        inverse_score = query_friendly['inverse_coverage_pct'] / 5  # 50% = 10pts
        domain_range_score = query_friendly['domain_range_coverage_pct'] / 8  # 80% = 10pts
        query_score = min(10, (inverse_score + domain_range_score) / 2)

        # Naming clarity: penaliza ambiguidades
        total_entities = len(self.all_entities)
        ambiguity_penalty = (naming['potentially_ambiguous_names'] / total_entities * 100) if total_entities else 0
        naming_score = max(0, 10 - ambiguity_penalty / 2)

        # Score total ponderado
        total_score = (
            multilingual_score * weights['multilingual'] +
            definitions_score * weights['definitions'] +
            alignments_score * weights['alignments'] +
            query_score * weights['query_friendly'] +
            naming_score * weights['naming_clarity']
        )

        # Classificação
        if total_score >= 8:
            level = "Excelente - Ontologia pronta para LLMs"
        elif total_score >= 6:
            level = "Bom - Usável por LLMs com ajustes menores"
        elif total_score >= 4:
            level = "Regular - Necessita melhorias para LLMs"
        else:
            level = "Precisa Melhorar - Difícil para LLMs interpretarem"

        return {
            'total_score': round(total_score, 2),
            'level': level,
            'breakdown': {
                'multilingual': round(multilingual_score, 2),
                'definitions': round(definitions_score, 2),
                'alignments': round(alignments_score, 2),
                'query_friendly': round(query_score, 2),
                'naming_clarity': round(naming_score, 2)
            },
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self):
        """Gera recomendações automáticas"""
        recommendations = []

        multilingual = self.results['multilingual']
        definitions = self.results['definitions']
        alignments = self.results['alignments']
        query_friendly = self.results['query_friendliness']

        if multilingual['bilingual_coverage_pct'] < 50:
            recommendations.append({
                'priority': 'ALTA',
                'category': 'Multilíngue',
                'issue': f'Apenas {multilingual["bilingual_coverage_pct"]:.1f}% das entidades têm labels pt+en',
                'suggestion': 'Adicionar rdfs:label@pt e rdfs:label@en para todas as classes e propriedades'
            })

        if definitions['examples_coverage_pct'] < 20:
            recommendations.append({
                'priority': 'ALTA',
                'category': 'Definições',
                'issue': f'Apenas {definitions["examples_coverage_pct"]:.1f}% das definições têm exemplos',
                'suggestion': 'Incluir exemplos concretos nas definições (rdfs:comment ou IAO:0000115): "Ex: Aeronave comercial como Boeing 737"'
            })

        if alignments['total_sameas_links'] == 0:
            recommendations.append({
                'priority': 'MÉDIA',
                'category': 'Alinhamentos',
                'issue': 'Nenhum alinhamento externo (owl:sameAs)',
                'suggestion': 'Adicionar owl:sameAs para DBpedia/Wikidata: ex: :Aircraft owl:sameAs <http://dbpedia.org/resource/Aircraft>'
            })

        if query_friendly['inverse_coverage_pct'] < 30:
            recommendations.append({
                'priority': 'ALTA',
                'category': 'Query-Friendliness',
                'issue': f'{query_friendly["inverse_coverage_pct"]:.1f}% de propriedades têm inversas',
                'suggestion': 'Criar propriedades inversas com owl:inverseOf: :hasParent owl:inverseOf :isParentOf'
            })

        if not recommendations:
            recommendations.append({
                'priority': 'INFO',
                'category': 'Geral',
                'issue': 'Ontologia bem preparada para LLMs',
                'suggestion': 'Manter qualidade nas próximas versões'
            })

        return recommendations

    def generate_html_report(self, output_file):
        """Gera relatório HTML"""

        score = self.results['llm_readability_score']
        multilingual = self.results['multilingual']
        definitions = self.results['definitions']
        alignments = self.results['alignments']
        query_friendly = self.results['query_friendliness']
        naming = self.results['naming_ambiguity']

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
    <title>Relatório de Usabilidade para LLMs - AirData</title>
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

        .warning {{ color: #cc0000; font-weight: 600; padding: 0.5rem; background: #ffe8e8; border: 1px solid #cc0000; margin-top: 0.5rem; }}
        .timestamp {{ color: #64748b; font-size: 0.95rem; }}
    </style>
</head>
<body>
<!-- AirData Header Start -->
<!-- AirData Header End -->
    <div class="container">
        <h1>Relatório de Usabilidade para LLMs</h1>

        <h2>Resumo Geral</h2>
        <table>
            <tr>
                <th style="width: 70%;">Métrica</th>
                <th style="width: 30%; text-align: center;">Valor</th>
            </tr>
            <tr>
                <td>Score Total de Usabilidade para LLMs</td>
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
                <td>Cobertura Multilíngue (pt/en)</td>
                <td style="text-align: center;">{score['breakdown']['multilingual']}/10</td>
            </tr>
            <tr>
                <td>Qualidade de Definições</td>
                <td style="text-align: center;">{score['breakdown']['definitions']}/10</td>
            </tr>
            <tr>
                <td>Alinhamentos Externos</td>
                <td style="text-align: center;">{score['breakdown']['alignments']}/10</td>
            </tr>
            <tr>
                <td>Query-Friendliness</td>
                <td style="text-align: center;">{score['breakdown']['query_friendly']}/10</td>
            </tr>
            <tr>
                <td>Clareza de Nomenclatura</td>
                <td style="text-align: center;">{score['breakdown']['naming_clarity']}/10</td>
            </tr>
        </table>

        <h2>Análise Detalhada</h2>

        <h3>Cobertura Multilíngue</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Entidades com label pt</td><td>{multilingual['entities_with_pt_label']}</td></tr>
            <tr><td>Entidades com label en</td><td>{multilingual['entities_with_en_label']}</td></tr>
            <tr><td>Entidades bilíngues (pt+en)</td><td>{multilingual['entities_with_both_languages']}</td></tr>
            <tr><td>Cobertura bilíngue</td><td>{multilingual['bilingual_coverage_pct']:.1f}%</td></tr>
        </table>
        {"<div class='warning'>⚠️ " + multilingual['warning'] + "</div>" if multilingual.get('warning') else ""}

        <h3>Qualidade de Definições</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Entidades com definição</td><td>{definitions['entities_with_definition']}</td></tr>
            <tr><td>Cobertura de definições</td><td>{definitions['definition_coverage_pct']:.1f}%</td></tr>
            <tr><td>Definições curtas (&lt;20 palavras)</td><td>{definitions['short_definitions']}</td></tr>
            <tr><td>Definições médias (20-100 palavras)</td><td>{definitions['medium_definitions']}</td></tr>
            <tr><td>Definições longas (&gt;100 palavras)</td><td>{definitions['long_definitions']}</td></tr>
            <tr><td>Tamanho médio</td><td>{definitions['avg_definition_length_words']} palavras</td></tr>
            <tr><td>Definições com exemplos</td><td>{definitions['definitions_with_examples']}</td></tr>
            <tr><td>Cobertura de exemplos</td><td>{definitions['examples_coverage_pct']:.1f}%</td></tr>
        </table>
        {"<div class='warning'>⚠️ " + definitions['warning'] + "</div>" if definitions.get('warning') else ""}

        <h3>Alinhamentos Externos</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Total de owl:sameAs links</td><td>{alignments['total_sameas_links']}</td></tr>
            <tr><td>Entidades com alinhamento</td><td>{alignments['entities_with_sameas']}</td></tr>
            <tr><td>Cobertura</td><td>{alignments['alignment_coverage_pct']:.1f}%</td></tr>
        </table>
        <h4>Por Fonte Externa:</h4>
        <table>
            <tr><th>Fonte</th><th>Links</th></tr>
            {"".join(f"<tr><td>{src}</td><td>{count}</td></tr>" for src, count in alignments['alignments_by_source'].items())}
        </table>
        {"<div class='warning'>⚠️ " + alignments['warning'] + "</div>" if alignments.get('warning') else ""}

        <h3>Query-Friendliness</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Propriedades com inversas</td><td>{query_friendly['properties_with_inverse']}</td></tr>
            <tr><td>Cobertura de inversas</td><td>{query_friendly['inverse_coverage_pct']:.1f}%</td></tr>
            <tr><td>Propriedades com domain+range</td><td>{query_friendly['properties_with_domain_and_range']}</td></tr>
            <tr><td>Cobertura domain+range</td><td>{query_friendly['domain_range_coverage_pct']:.1f}%</td></tr>
            <tr><td>Classes com labels curtos</td><td>{query_friendly['classes_with_short_labels']}</td></tr>
            <tr><td>Cobertura labels curtos</td><td>{query_friendly['short_label_pct']:.1f}%</td></tr>
        </table>
        {"<div class='warning'>⚠️ " + query_friendly['warning'] + "</div>" if query_friendly.get('warning') else ""}

        <h3>Ambiguidade de Nomenclatura</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Nomes potencialmente ambíguos</td><td>{naming['potentially_ambiguous_names']}</td></tr>
            <tr><td>Nomes duplicados</td><td>{naming['duplicate_names']}</td></tr>
            <tr><td>Nomes de palavra única</td><td>{naming['single_word_names']}</td></tr>
            <tr><td>Percentual palavra única</td><td>{naming['single_word_pct']:.1f}%</td></tr>
        </table>
        {"<div class='warning'>⚠️ " + naming['warning'] + "</div>" if naming.get('warning') else ""}

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
        description='Validação de LLM-readability para ontologias OWL (SEM modificar a ontologia)'
    )
    parser.add_argument('owl_file', help='Arquivo OWL a ser analisado')
    parser.add_argument('--output', default='llm_readability.html',
                       help='Arquivo HTML de saída (default: llm_readability.html)')
    parser.add_argument('--json', help='Salvar resultados também em JSON')

    args = parser.parse_args()

    if not Path(args.owl_file).exists():
        print(f"❌ ERRO: Arquivo não encontrado: {args.owl_file}")
        sys.exit(1)

    validator = LLMReadabilityValidator(args.owl_file)
    results = validator.analyze_all()

    validator.generate_html_report(args.output)

    if args.json:
        validator.save_json(args.json)

    print("\n" + "="*60)
    print("RESUMO DE LLM-READABILITY")
    print("="*60)
    score = results['llm_readability_score']
    print(f"\n🤖 SCORE GERAL: {score['total_score']}/10 ({score['level']})")
    print(f"\n   Multilíngue:     {score['breakdown']['multilingual']}/10")
    print(f"   Definições:      {score['breakdown']['definitions']}/10")
    print(f"   Alinhamentos:    {score['breakdown']['alignments']}/10")
    print(f"   Query-Friendly:  {score['breakdown']['query_friendly']}/10")
    print(f"   Clareza Nomes:   {score['breakdown']['naming_clarity']}/10")
    print(f"\n📋 {len(score['recommendations'])} recomendações geradas")
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
