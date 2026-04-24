import os
import glob
import html
import datetime
import argparse

from owlready2 import World


HTML_TEMPLATE_START = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changelog - AirData Ontology</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(0, 60, 125, 0.08), transparent 28%),
                linear-gradient(180deg, #f6f9fc 0%, #eef3f8 100%);
            color: #1f2937;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .container {
            max-width: 1180px;
            margin: 0 auto;
            padding: 3.5rem 1.5rem 4rem;
            flex: 1;
            width: 100%;
        }

        .hero {
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
            gap: 1.5rem;
            align-items: stretch;
            margin-bottom: 2.5rem;
        }

        .hero-panel,
        .summary-panel {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(209, 217, 224, 0.9);
            border-radius: 16px;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
        }

        .hero-panel {
            padding: 2rem 2.2rem;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: rgba(0, 60, 125, 0.08);
            color: #003C7D;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }

        h1 {
            color: #0f172a;
            font-size: clamp(2rem, 3vw, 2.8rem);
            line-height: 1.1;
            margin-bottom: 0.9rem;
        }

        .hero-text {
            color: #475569;
            font-size: 1rem;
            line-height: 1.75;
            max-width: 62ch;
        }

        .summary-panel {
            padding: 1.6rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 1.2rem;
        }

        .summary-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #0f172a;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
        }

        .summary-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
        }

        .summary-value {
            font-size: 1.6rem;
            font-weight: 800;
            color: #003C7D;
            line-height: 1;
            margin-bottom: 0.35rem;
        }

        .summary-label {
            color: #64748b;
            font-size: 0.9rem;
        }

        .summary-note {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.6;
        }

        .timeline {
            position: relative;
            padding-left: 2.25rem;
        }

        .timeline::before {
            content: "";
            position: absolute;
            left: 0.6rem;
            top: 0.4rem;
            bottom: 0.4rem;
            width: 2px;
            background: linear-gradient(180deg, #93c5fd 0%, #cbd5e1 100%);
        }

        .version-card {
            position: relative;
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(209, 217, 224, 0.9);
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.6rem;
            overflow: hidden;
        }

        .version-card::before {
            content: "";
            position: absolute;
            left: -1.95rem;
            top: 1.7rem;
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: #0ea5e9;
            border: 4px solid #dbeafe;
            box-shadow: 0 0 0 6px rgba(14, 165, 233, 0.12);
        }

        .version-header {
            padding: 1.35rem 1.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            border-bottom: 1px solid #eef2f7;
            background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.92));
        }

        .version-meta {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }

        .version-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #0f172a;
        }

        .version-subtitle {
            color: #64748b;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .version-date {
            color: #003C7D;
            background: rgba(0, 60, 125, 0.08);
            border: 1px solid rgba(0, 60, 125, 0.12);
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            white-space: nowrap;
            font-size: 0.85rem;
            font-weight: 700;
        }

        .change-groups {
            padding: 1.1rem 1.3rem 1.35rem;
            display: grid;
            gap: 1rem;
        }

        .change-group {
            background: #fcfdff;
            border: 1px solid #e7edf4;
            border-radius: 14px;
            padding: 1rem 1.05rem 1rem 1.15rem;
        }

        .change-title {
            font-weight: 700;
            margin-bottom: 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.65rem;
            color: #0f172a;
        }

        .change-count {
            margin-left: auto;
            color: #64748b;
            font-size: 0.86rem;
            font-weight: 600;
        }

        .badge {
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .badge-added { background: #dcfce7; color: #166534; }
        .badge-removed { background: #fee2e2; color: #b91c1c; }
        .badge-changed { background: #ffedd5; color: #c2410c; }

        .tree-list,
        .tree-list ul {
            list-style: none;
            margin: 0;
            padding-left: 1.2rem;
            position: relative;
        }

        .tree-list {
            padding-left: 0.3rem;
        }

        .tree-list ul {
            margin-top: 0.7rem;
        }

        .tree-list li {
            position: relative;
            padding-left: 1.15rem;
            margin-bottom: 0.8rem;
        }

        .tree-list li:last-child {
            margin-bottom: 0;
        }

        .tree-list li::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0.75rem;
            width: 0.7rem;
            height: 1px;
            background: #94a3b8;
        }

        .tree-list li::after {
            content: "";
            position: absolute;
            left: 0;
            top: -0.55rem;
            bottom: -0.55rem;
            width: 1px;
            background: #cbd5e1;
        }

        .tree-list li:last-child::after {
            bottom: calc(100% - 0.75rem);
        }

        .tree-item {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.55rem;
            padding: 0.7rem 0.8rem;
            border-radius: 12px;
            background: white;
            border: 1px solid #edf2f7;
        }

        .entity-name {
            font-family: "Consolas", "SFMono-Regular", "Courier New", monospace;
            font-size: 0.95rem;
            font-weight: 700;
            color: #0f172a;
        }

        .item-iri {
            color: #64748b;
            font-size: 0.8rem;
            word-break: break-all;
        }

        .change-detail {
            font-size: 0.9rem;
            color: #475569;
            line-height: 1.6;
        }

        .change-detail .old-value {
            color: #b91c1c;
            text-decoration: line-through;
            margin-right: 0.35rem;
        }

        .change-detail .new-value {
            color: #166534;
            font-weight: 700;
            margin-left: 0.35rem;
        }

        .empty-state {
            padding: 2.2rem;
            text-align: center;
            color: #64748b;
            font-style: italic;
            background: rgba(255, 255, 255, 0.9);
            border: 1px dashed #cbd5e1;
            border-radius: 16px;
        }

        @media (max-width: 900px) {
            .hero {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 720px) {
            .container {
                padding: 2rem 1rem 3rem;
            }

            .timeline {
                padding-left: 1.55rem;
            }

            .timeline::before {
                left: 0.35rem;
            }

            .version-card::before {
                left: -1.3rem;
            }

            .version-header {
                flex-direction: column;
                align-items: flex-start;
            }
        }

        @media (max-width: 560px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

    <main class="container">
        <section class="hero">
            <div class="hero-panel">
                <div class="eyebrow">Evolucao da Ontologia</div>
                <h1>Historico de Mudancas</h1>
                <p class="hero-text">
                    Acompanhe a evolucao da AirData Ontology em uma linha do tempo por versao, com visualizacao em arvore para entidades adicionadas, removidas e alteradas.
                </p>
            </div>
            <aside class="summary-panel">
                <div class="summary-title">Resumo do Changelog</div>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-value">{{version_count}}</div>
                        <div class="summary-label">comparacoes</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{{entity_delta}}</div>
                        <div class="summary-label">mudancas rastreadas</div>
                    </div>
                </div>
                <p class="summary-note">
                    Cada cartao representa uma versao comparada com sua anterior, destacando a estrutura do dominio que evoluiu ao longo do projeto.
                </p>
            </aside>
        </section>

        <section class="timeline">
"""

HTML_END = """
        </section>
    </main>
</body>
</html>
"""


def get_owl_files(owl_dir):
    files = glob.glob(f"{owl_dir}/*.owl")
    files.sort(key=os.path.getctime, reverse=True)
    return files


def get_entities(onto):
    entities = {}

    def add_entity_fingerprint(entity):
        iri = str(entity.iri)
        label = str(entity.label) if hasattr(entity, "label") else None
        comment = str(entity.comment) if hasattr(entity, "comment") else None

        if isinstance(label, list):
            label = label[0] if label else None
        if isinstance(comment, list):
            comment = comment[0] if comment else None

        entities[iri] = {
            "iri": iri,
            "label": label,
            "comment": comment,
        }

    for cls in onto.classes():
        add_entity_fingerprint(cls)
    for prop in onto.properties():
        add_entity_fingerprint(prop)

    return entities


def compare_versions(new_file, old_file):
    print(f"Comparando: {os.path.basename(new_file)} vs {os.path.basename(old_file)}")

    world_new = World()
    onto_new = world_new.get_ontology(new_file).load()
    entities_new_map = get_entities(onto_new)

    world_old = World()
    onto_old = world_old.get_ontology(old_file).load()
    entities_old_map = get_entities(onto_old)

    iris_new = set(entities_new_map.keys())
    iris_old = set(entities_old_map.keys())

    added_iris = iris_new - iris_old
    removed_iris = iris_old - iris_new
    common_iris = iris_new.intersection(iris_old)

    added_entities = [entities_new_map[iri] for iri in added_iris]
    removed_entities = [entities_old_map[iri] for iri in removed_iris]
    changed_entities = []

    for iri in common_iris:
        fingerprint_new = entities_new_map[iri]
        fingerprint_old = entities_old_map[iri]

        changes = {}
        if fingerprint_new["label"] != fingerprint_old["label"]:
            changes["label"] = {
                "old": fingerprint_old["label"],
                "new": fingerprint_new["label"],
            }
        if fingerprint_new["comment"] != fingerprint_old["comment"]:
            changes["comment"] = {
                "old": fingerprint_old["comment"],
                "new": fingerprint_new["comment"],
            }

        if changes:
            changed_entities.append({
                "entity": fingerprint_new,
                "changes": changes,
            })

    return {
        "new_file": os.path.basename(new_file),
        "old_file": os.path.basename(old_file),
        "date": datetime.datetime.fromtimestamp(os.path.getctime(new_file)).strftime("%d/%m/%Y"),
        "added": sorted(added_entities, key=lambda x: x["iri"]),
        "removed": sorted(removed_entities, key=lambda x: x["iri"]),
        "changed": sorted(changed_entities, key=lambda x: x["entity"]["iri"]),
    }


def esc(value):
    return html.escape(str(value), quote=True)


def format_entity_item(entity_data):
    name = esc(entity_data["iri"].split("#")[-1])
    iri = esc(entity_data["iri"])
    return (
        '<li><div class="tree-item">'
        f'<span class="entity-name">{name}</span>'
        f'<span class="item-iri">{iri}</span>'
        "</div></li>"
    )


def render_change_group(badge_class, badge_text, title, items_html, count):
    return f"""
            <div class="change-group">
                <div class="change-title">
                    <span class="badge {badge_class}">{badge_text}</span>
                    {title}
                    <span class="change-count">{count} itens</span>
                </div>
                <ul class="tree-list">
                    {items_html}
                </ul>
            </div>
"""


def generate_html_card(diff_data):
    total_changes = len(diff_data["added"]) + len(diff_data["removed"]) + len(diff_data["changed"])
    html_parts = [f"""
        <div class="version-card">
            <div class="version-header">
                <div class="version-meta">
                    <div class="version-title">{esc(diff_data["new_file"])}</div>
                    <div class="version-subtitle">Comparado com {esc(diff_data["old_file"])}</div>
                </div>
                <div class="version-date">{esc(diff_data["date"])} • {total_changes} mudancas</div>
            </div>
            <div class="change-groups">
"""]

    has_changes = False

    if diff_data["added"]:
        has_changes = True
        items_html = "".join(format_entity_item(entity_data) for entity_data in diff_data["added"])
        html_parts.append(render_change_group("badge-added", "ADICIONADO", "Novas Entidades", items_html, len(diff_data["added"])))

    if diff_data["removed"]:
        has_changes = True
        items_html = "".join(format_entity_item(entity_data) for entity_data in diff_data["removed"])
        html_parts.append(render_change_group("badge-removed", "REMOVIDO", "Entidades Excluidas", items_html, len(diff_data["removed"])))

    if diff_data["changed"]:
        has_changes = True
        items_html = []
        for change_data in diff_data["changed"]:
            entity = change_data["entity"]
            changes = change_data["changes"]
            name = esc(entity["iri"].split("#")[-1])
            iri = esc(entity["iri"])

            detail_items = []
            if "label" in changes:
                old_label = esc(changes["label"]["old"] if changes["label"]["old"] is not None else "N/A")
                new_label = esc(changes["label"]["new"] if changes["label"]["new"] is not None else "N/A")
                detail_items.append(
                    '<li><div class="tree-item change-detail">'
                    f'Label: <span class="old-value">{old_label}</span> → <span class="new-value">{new_label}</span>'
                    '</div></li>'
                )
            if "comment" in changes:
                old_comment = esc(changes["comment"]["old"] if changes["comment"]["old"] is not None else "N/A")
                new_comment = esc(changes["comment"]["new"] if changes["comment"]["new"] is not None else "N/A")
                detail_items.append(
                    '<li><div class="tree-item change-detail">'
                    f'Comment: <span class="old-value">{old_comment}</span> → <span class="new-value">{new_comment}</span>'
                    '</div></li>'
                )

            items_html.append(
                '<li>'
                '<div class="tree-item">'
                f'<span class="entity-name">{name}</span>'
                f'<span class="item-iri">{iri}</span>'
                '</div>'
                '<ul class="tree-list">'
                f'{"".join(detail_items)}'
                '</ul>'
                '</li>'
            )

        html_parts.append(render_change_group("badge-changed", "ALTERADO", "Entidades Modificadas", "".join(items_html), len(diff_data["changed"])))

    if not has_changes:
        html_parts.append('<div class="empty-state">Nenhuma mudanca estrutural (classes/propriedades) detectada.</div>')

    html_parts.append("""
            </div>
        </div>
""")
    return "".join(html_parts)


def main(owl_dir, output_file):
    files = get_owl_files(owl_dir)

    if len(files) < 2:
        full_html = (
            HTML_TEMPLATE_START
            .replace("{{version_count}}", "0")
            .replace("{{entity_delta}}", "0")
            + '<div class="empty-state">Aguardando mais versoes para gerar historico.</div>'
            + HTML_END
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_html)
        return

    content_html = ""
    summary = {
        "version_count": len(files) - 1,
        "entity_delta": 0,
    }

    for i in range(len(files) - 1):
        try:
            diff = compare_versions(files[i], files[i + 1])
            summary["entity_delta"] += len(diff["added"]) + len(diff["removed"]) + len(diff["changed"])
            content_html += generate_html_card(diff)
        except Exception as e:
            print(f"Erro ao comparar {files[i]} e {files[i + 1]}: {e}")

    full_html = (
        HTML_TEMPLATE_START
        .replace("{{version_count}}", str(summary["version_count"]))
        .replace("{{entity_delta}}", str(summary["entity_delta"]))
        + content_html
        + HTML_END
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Changelog gerado em {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera um changelog HTML comparando versoes de ontologias.")
    parser.add_argument("--owl-dir", required=True, help="Diretorio contendo os arquivos .owl.")
    parser.add_argument("--output-file", required=True, help="Caminho para o arquivo HTML de saida.")

    args = parser.parse_args()
    main(args.owl_dir, args.output_file)
