#!/usr/bin/env python3
import json
import os
import re
import subprocess
import tempfile
import argparse
from datetime import datetime, timezone

from rdflib import Graph, RDF, RDFS, OWL, URIRef


def list_owl_files(directory):
    files = []
    for name in os.listdir(directory):
        if name.endswith(".owl"):
            path = os.path.join(directory, name)
            files.append((os.path.getmtime(path), path))
    files.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in files]


def version_from_filename(path):
    name = os.path.basename(path)
    match = re.search(r"airdata_owl_v(\\d+\\.\\d+\\.\\d+)\\.owl", name)
    if match:
        return match.group(1)
    return "desconhecida"


def load_graph(path):
    graph = Graph()
    graph.parse(path)
    return graph


def ontology_iri(graph):
    for subj in graph.subjects(RDF.type, OWL.Ontology):
        return str(subj)
    return ""


def get_entities(graph):
    classes = set(graph.subjects(RDF.type, OWL.Class))
    classes.update(graph.subjects(RDF.type, RDFS.Class))
    object_props = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    data_props = set(graph.subjects(RDF.type, OWL.DatatypeProperty))
    individuals = set(graph.subjects(RDF.type, OWL.NamedIndividual))
    return classes, object_props, data_props, individuals


def hierarchy_metrics(graph, classes):
    class_set = set(classes)
    subclasses = {cls: set() for cls in class_set}
    superclasses = {cls: set() for cls in class_set}
    for cls in class_set:
        for sup in graph.objects(cls, RDFS.subClassOf):
            if isinstance(sup, URIRef):
                superclasses[cls].add(sup)
                if sup in class_set:
                    subclasses[sup].add(cls)

    total_subclasses = sum(len(children) for children in subclasses.values())
    avg_subclasses = (total_subclasses / len(class_set)) if class_set else 0

    leaf_classes = [cls for cls, children in subclasses.items() if not children]
    no_superclass = [
        cls for cls, supers in superclasses.items()
        if cls != OWL.Thing and not supers
    ]

    memo = {}

    def depth(cls, visiting):
        if cls in memo:
            return memo[cls]
        if cls in visiting:
            return 1
        visiting.add(cls)
        supers = list(superclasses.get(cls, []))
        if not supers:
            result = 1
        else:
            sup_depths = []
            for sup in supers:
                if sup == OWL.Thing:
                    sup_depths.append(1)
                elif sup in class_set:
                    sup_depths.append(depth(sup, visiting))
                else:
                    sup_depths.append(1)
            result = 1 + max(sup_depths)
        visiting.remove(cls)
        memo[cls] = result
        return result

    max_depth = max((depth(cls, set()) for cls in class_set), default=0)

    return {
        "max_depth": max_depth,
        "avg_subclasses": avg_subclasses,
        "leaf_classes": len(leaf_classes),
        "no_explicit_superclass": len(no_superclass),
    }


def quality_metrics(graph, classes, object_props, data_props):
    classes_no_label = []
    classes_no_comment = []
    for cls in classes:
        if not list(graph.objects(cls, RDFS.label)):
            classes_no_label.append(cls)
        if not list(graph.objects(cls, RDFS.comment)):
            classes_no_comment.append(cls)

    props_no_domain = []
    props_no_range = []
    for prop in set(object_props) | set(data_props):
        if not list(graph.objects(prop, RDFS.domain)):
            props_no_domain.append(prop)
        if not list(graph.objects(prop, RDFS.range)):
            props_no_range.append(prop)

    return {
        "classes_no_label": len(classes_no_label),
        "classes_no_comment": len(classes_no_comment),
        "properties_no_domain": len(props_no_domain),
        "properties_no_range": len(props_no_range),
    }


def compare_versions(latest_graph, previous_graph):
    latest_classes, latest_obj, latest_data, _ = get_entities(latest_graph)
    prev_classes, prev_obj, prev_data, _ = get_entities(previous_graph)

    return {
        "classes_added": len(latest_classes - prev_classes),
        "classes_removed": len(prev_classes - latest_classes),
        "object_properties_added": len(latest_obj - prev_obj),
        "object_properties_removed": len(prev_obj - latest_obj),
        "data_properties_added": len(latest_data - prev_data),
        "data_properties_removed": len(prev_data - latest_data),
    }


def check_consistency(owl_path, robot_jar):
    """
    Verifica consistência com múltiplos reasoners e captura warnings.
    Retorna dicionário com resultados detalhados.
    """
    if not os.path.isfile(robot_jar):
        return {
            "status": "nao verificada",
            "reasoners": {},
            "warnings": []
        }

    # Lista de reasoners para testar
    reasoners = ["HermiT", "ELK", "structural"]

    results = {
        "status": "nao verificada",
        "reasoners": {},
        "warnings": [],
        "profile": "unknown"
    }

    tmp_handle = tempfile.NamedTemporaryFile(suffix=".owl", delete=False)
    tmp_path = tmp_handle.name
    tmp_handle.close()

    # Testa cada reasoner
    for reasoner_name in reasoners:
        try:
            result = subprocess.run(
                [
                    "java",
                    "-jar",
                    robot_jar,
                    "reason",
                    "--input",
                    owl_path,
                    "--reasoner",
                    reasoner_name,
                    "--output",
                    tmp_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )

            is_consistent = result.returncode == 0

            # Parse warnings from stderr
            warnings = []
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if 'WARN' in line.upper() or 'WARNING' in line.upper():
                        warnings.append(line.strip())

            results["reasoners"][reasoner_name] = {
                "consistent": is_consistent,
                "warnings": warnings,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            results["reasoners"][reasoner_name] = {
                "consistent": False,
                "warnings": ["Timeout após 120 segundos"],
                "return_code": -1
            }
        except Exception as e:
            results["reasoners"][reasoner_name] = {
                "consistent": False,
                "warnings": [str(e)],
                "return_code": -2
            }

    # Determina status geral (se pelo menos um reasoner passou)
    any_consistent = any(
        r.get("consistent", False)
        for r in results["reasoners"].values()
    )

    results["status"] = "sim" if any_consistent else "nao"

    # Coleta todos os warnings únicos
    all_warnings = set()
    for reasoner_data in results["reasoners"].values():
        all_warnings.update(reasoner_data.get("warnings", []))
    results["warnings"] = list(all_warnings)

    # Limpa arquivo temporário
    try:
        os.remove(tmp_path)
    except OSError:
        pass

    return results


def main(owl_dir, site_dir, robot_jar):
    owl_files = list_owl_files(owl_dir)
    if not owl_files:
        raise SystemExit(f"Nenhum arquivo .owl encontrado em {owl_dir}.")

    latest_path = owl_files[0]
    previous_path = owl_files[1] if len(owl_files) > 1 else None

    latest_graph = load_graph(latest_path)
    latest_classes, latest_obj, latest_data, latest_ind = get_entities(latest_graph)

    # Verifica consistência (retorna dicionário agora)
    consistency_result = check_consistency(latest_path, robot_jar)

    stats = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
        "owl_file": os.path.basename(latest_path),
        "version": version_from_filename(latest_path),
        "modified_at": datetime.fromtimestamp(os.path.getmtime(latest_path)).strftime("%Y-%m-%d"),
        "ontology_iri": ontology_iri(latest_graph),
        "consistency_check": consistency_result["status"],  # Mantém compatibilidade
        "consistency_extended": consistency_result,  # Nova seção detalhada
        "owl_profile": "nao detectado",
        "structure": {
            "classes": len(latest_classes),
            "object_properties": len(latest_obj),
            "data_properties": len(latest_data),
            "individuals": len(latest_ind),
            "axioms": len(latest_graph),
            "imports": sorted({str(o) for o in latest_graph.objects(None, OWL.imports)}),
        },
        "hierarchy": hierarchy_metrics(latest_graph, latest_classes),
        "quality": quality_metrics(latest_graph, latest_classes, latest_obj, latest_data),
        "evolution": None,
    }

    if previous_path:
        prev_graph = load_graph(previous_path)
        stats["evolution"] = compare_versions(latest_graph, prev_graph)
        stats["previous_version"] = version_from_filename(previous_path)
    else:
        stats["previous_version"] = "nao disponivel"

    os.makedirs(site_dir, exist_ok=True)
    json_path = os.path.join(site_dir, "statistics.json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2, ensure_ascii=True)

    html_path = os.path.join(site_dir, "statistics.html")
    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write(render_html(stats))

    print(f"Estatisticas geradas em {html_path}")


def render_html(stats):
    imports = stats["structure"]["imports"]
    imports_html = "<li>Nenhuma importação declarada.</li>" if not imports else "".join(
        f"<li>{imp}</li>" for imp in imports
    )

    # Gera HTML para consistência estendida
    consistency_ext = stats.get("consistency_extended", {})
    reasoners_html = ""
    if consistency_ext and "reasoners" in consistency_ext:
        for reasoner, data in consistency_ext["reasoners"].items():
            status_icon = "✓" if data.get("consistent", False) else "✗"
            status_color = "#28a745" if data.get("consistent", False) else "#d73a49"
            warnings_html = ""
            if data.get("warnings"):
                warnings_html = "<ul>" + "".join(f"<li>{w}</li>" for w in data["warnings"][:3]) + "</ul>"

            status_text = "Consistente" if data.get("consistent") else "Inconsistente"
            reasoners_html += f"""
              <tr>
                <th style="color: {status_color}">{status_icon} {reasoner}</th>
                <td>{status_text}{warnings_html}</td>
              </tr>
            """
    else:
        reasoners_html = '<tr><th>Status</th><td>Verificação não realizada</td></tr>'

    evolution = stats["evolution"]
    if evolution:
        evolution_html = f"""
          <tr><th>Versão anterior</th><td>{stats.get("previous_version")}</td></tr>
          <tr><th>Classes adicionadas</th><td>{evolution['classes_added']}</td></tr>
          <tr><th>Classes removidas</th><td>{evolution['classes_removed']}</td></tr>
          <tr><th>ObjectProperties adicionadas</th><td>{evolution['object_properties_added']}</td></tr>
          <tr><th>ObjectProperties removidas</th><td>{evolution['object_properties_removed']}</td></tr>
          <tr><th>DataProperties adicionadas</th><td>{evolution['data_properties_added']}</td></tr>
          <tr><th>DataProperties removidas</th><td>{evolution['data_properties_removed']}</td></tr>
        """
    else:
        evolution_html = "<tr><th>Versão anterior</th><td>não disponível</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Estatísticas da Ontologia</title>
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
  </style>
</head>
<body>
  <div class="container">
    <h1>Estatísticas da Ontologia</h1>
    <p class="meta">Gerado automaticamente em {stats['generated_at']}</p>

    <h3>Visão geral</h3>
    <table>
      <tr><th>Arquivo OWL</th><td>{stats['owl_file']}</td></tr>
      <tr><th>Versão</th><td>{stats['version']}</td></tr>
      <tr><th>Data de modificação</th><td>{stats['modified_at']}</td></tr>
      <tr><th>IRI da ontologia</th><td>{stats['ontology_iri']}</td></tr>
      <tr><th>Consistência (checagem automática)</th><td>{stats['consistency_check']}</td></tr>
      <tr><th>Perfil OWL detectado</th><td>{stats['owl_profile']}</td></tr>
    </table>

    <h3>Consistência Detalhada (Múltiplos Reasoners)</h3>
    <table>
      {reasoners_html}
    </table>

    <h3>Estrutura</h3>
    <table>
      <tr><th>Classes</th><td>{stats['structure']['classes']}</td></tr>
      <tr><th>ObjectProperties</th><td>{stats['structure']['object_properties']}</td></tr>
      <tr><th>DataProperties</th><td>{stats['structure']['data_properties']}</td></tr>
      <tr><th>Individuals</th><td>{stats['structure']['individuals']}</td></tr>
      <tr><th>Axiomas (triples)</th><td>{stats['structure']['axioms']}</td></tr>
    </table>
    <h4>Ontologias importadas</h4>
    <ul>
      {imports_html}
    </ul>

    <h3>Hierarquia</h3>
    <table>
      <tr><th>Profundidade máxima</th><td>{stats['hierarchy']['max_depth']}</td></tr>
      <tr><th>Média de subclasses por classe</th><td>{stats['hierarchy']['avg_subclasses']:.2f}</td></tr>
      <tr><th>Classes folha</th><td>{stats['hierarchy']['leaf_classes']}</td></tr>
      <tr><th>Classes sem superclasse explícita</th><td>{stats['hierarchy']['no_explicit_superclass']}</td></tr>
    </table>

    <h3>Qualidade objetiva</h3>
    <table>
      <tr><th>Classes sem rdfs:label</th><td>{stats['quality']['classes_no_label']}</td></tr>
      <tr><th>Classes sem rdfs:comment</th><td>{stats['quality']['classes_no_comment']}</td></tr>
      <tr><th>Propriedades sem domínio</th><td>{stats['quality']['properties_no_domain']}</td></tr>
      <tr><th>Propriedades sem range</th><td>{stats['quality']['properties_no_range']}</td></tr>
    </table>

    <h3>Evolução</h3>
    <table>
      {evolution_html}
    </table>
  </div>
</body>
</html>
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera estatísticas sobre as ontologias OWL.")
    parser.add_argument('--owl-dir', required=True, help='Diretório contendo os arquivos .owl.')
    parser.add_argument('--site-dir', required=True, help='Diretório de saída para os arquivos de estatísticas.')
    parser.add_argument('--robot-jar', required=True, help='Caminho para o arquivo robot.jar.')
    
    args = parser.parse_args()
    
    main(args.owl_dir, args.site_dir, args.robot_jar)
