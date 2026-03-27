#!/usr/bin/env python3
"""
normalize_header.py - Normaliza o cabecalho de todas as paginas HTML do site AirData.

Os templates de estilo e navegacao estao embutidos diretamente neste script,
eliminando a necessidade de arquivos externos em assets/.
"""
import os
import re
import argparse


STYLE_START = "<!-- AirData Header Style Start -->"
STYLE_END = "<!-- AirData Header Style End -->"
HEADER_START = "<!-- AirData Header Start -->"
HEADER_END = "<!-- AirData Header End -->"
LEGACY_STYLE_START = "<!-- AirData Global Header Style Start -->"
LEGACY_STYLE_END = "<!-- AirData Global Header Style End -->"
LEGACY_HEADER_START = "<!-- AirData Global Header Start -->"
LEGACY_HEADER_END = "<!-- AirData Global Header End -->"

# Template de estilos do cabecalho (embutido)
HEADER_STYLE_TEMPLATE = """<style>
  /* Base Styles */
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    margin: 0;
    color: #24292e;
  }

  /* Header */
  .airdata-header {
    background-color: #ffffff;
    border-bottom: 1px solid #d1d5da;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 40px;
  }

  /* Logo */
  .airdata-header .logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
    text-decoration: none;
    color: #003C7D;
  }

  .airdata-header .logo-img {
    height: 40px;
  }

  .airdata-header .logo-text {
    font-size: 1.25rem;
    font-weight: 600;
    white-space: nowrap;
  }

  /* Navigation */
  .airdata-header .nav-container {
    display: flex;
    gap: 16px;
  }

  .airdata-header .nav-item {
    position: relative;
  }

  .airdata-header .nav-link {
    display: block;
    padding: 8px 12px;
    color: #586069;
    text-decoration: none;
    font-weight: 500;
    font-size: 1rem;
    border-radius: 6px;
    transition: background-color 0.2s ease, color 0.2s ease;
  }

  .airdata-header .nav-link:hover,
  .airdata-header .dropdown:hover .nav-link {
    background-color: #f6f8fa;
    color: #0366d6;
  }

  /* Dropdown */
  .airdata-header .dropdown-content {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    background-color: #ffffff;
    min-width: 220px;
    border: 1px solid #d1d5da;
    border-radius: 6px;
    box-shadow: 0 8px 24px rgba(149, 157, 165, 0.2);
    z-index: 1000;
    padding: 8px 0;
  }

  .airdata-header .dropdown:hover .dropdown-content {
    display: block;
  }

  .airdata-header .dropdown-item {
    display: block;
    padding: 8px 16px;
    color: #24292e;
    text-decoration: none;
    font-weight: 400;
    font-size: 0.9rem;
    text-align: left;
  }

  .airdata-header .dropdown-item:hover {
    background-color: #f6f8fa;
  }
</style>"""

# Template de navegacao do cabecalho (embutido)
# Use {{prefix}} como placeholder para o caminho relativo
HEADER_NAV_TEMPLATE = """<!-- AirData Header Start -->
<header class="airdata-header">
  <a href="{{prefix}}index.html" class="logo-container">
    <img src="{{prefix}}airdata-logo.png" alt="AirData Logo" class="logo-img">
    <span class="logo-text">AirData Ontology</span>
  </a>

  <nav class="nav-container">
    <div class="nav-item">
      <a href="{{prefix}}index.html" class="nav-link">In&iacute;cio</a>
    </div>

    <div class="nav-item dropdown">
      <a href="#" class="nav-link">Ontologia &#9662;</a>
      <div class="dropdown-content">
        <a href="{{prefix}}docs/index-pt.html" class="dropdown-item">Documenta&ccedil;&atilde;o</a>
        <a href="{{prefix}}docs/webvowl/index.html" class="dropdown-item">Grafo</a>
        <a href="{{prefix}}statistics.html" class="dropdown-item">Estat&iacute;sticas</a>
      </div>
    </div>

    <div class="nav-item dropdown">
      <a href="#" class="nav-link">Evolu&ccedil;&atilde;o &#9662;</a>
      <div class="dropdown-content">
        <a href="{{prefix}}changelog.html" class="dropdown-item">Hist&oacute;rico de Mudan&ccedil;as</a>
        <a href="{{prefix}}versions.html" class="dropdown-item">Vers&otilde;es OWL</a>
      </div>
    </div>

    <div class="nav-item dropdown">
      <a href="#" class="nav-link">Relat&oacute;rios &#9662;</a>
      <div class="dropdown-content">
        <a href="{{prefix}}quality_report.html" class="dropdown-item">Valida&ccedil;&atilde;o Sint&aacute;tica</a>
        <a href="{{prefix}}quality_report_extended.html" class="dropdown-item">An&aacute;lise Sem&acirc;ntica</a>
        <a href="{{prefix}}logic_report.html" class="dropdown-item">Axiomas L&oacute;gicos OWL</a>
        <a href="{{prefix}}llm_readability.html" class="dropdown-item">Usabilidade para LLMs</a>
        <a href="{{prefix}}sparql_validation.html" class="dropdown-item">Valida&ccedil;&atilde;o SPARQL</a>
        <a href="{{prefix}}competency_report.html" class="dropdown-item">Perguntas de Compet&ecirc;ncia</a>
        <a href="{{prefix}}quality-guide.html" class="dropdown-item">Guia de Interpreta&ccedil;&atilde;o</a>
      </div>
    </div>

    <div class="nav-item dropdown">
      <a href="#" class="nav-link">Evolu&ccedil;&atilde;o &#9662;</a>
      <div class="dropdown-content">
        <a href="{{prefix}}changelog.html" class="dropdown-item">Hist&oacute;rico de Mudan&ccedil;as</a>
        <a href="{{prefix}}versions.html" class="dropdown-item">Vers&otilde;es OWL</a>
        <a href="{{prefix}}delta_report.html" class="dropdown-item">Relat&oacute;rio Delta de Qualidade</a>
      </div>
    </div>
  </nav>
</header>
<!-- AirData Header End -->"""


def get_header_template():
    """Retorna os templates de estilo e navegacao embutidos."""
    return HEADER_STYLE_TEMPLATE, HEADER_NAV_TEMPLATE


def prefix_for_path(path, site_dir):
    rel = os.path.relpath(path, site_dir)
    parts = os.path.dirname(rel).split(os.sep)
    if parts == ['.'] or parts == [''] or parts == []:
        return ""
    return "../" * len(parts)


def ensure_structure(content):
    # Garante que a estrutura basica (html, head, body) existe
    if not re.search(r"<html[^>]*>", content, flags=re.IGNORECASE):
        content = "<html>\n" + content + "\n</html>"
    if not re.search(r"<head[^>]*>", content, flags=re.IGNORECASE):
        content = content.replace("<html>", "<html>\n<head>\n</head>", 1)
    
    # Garante que a codificação UTF-8 está declarada
    if not re.search(r"<meta\s+charset=", content, flags=re.IGNORECASE):
        # Adiciona a tag meta charset logo apos a abertura do head
        content = re.sub(r"(<head[^>]*>)", r'\1\n    <meta charset="UTF-8">', content, count=1, flags=re.IGNORECASE)

    if not re.search(r"<body[^>]*>", content, flags=re.IGNORECASE):
        content = re.sub(r"</head>", "</head>\n<body>", content, count=1, flags=re.IGNORECASE)
    if not re.search(r"</body>", content, flags=re.IGNORECASE):
        content = content.replace("</html>", "</body>\n</html>", 1)
    return content


def remove_existing_headers(content):
    content = re.sub(
        rf"{re.escape(STYLE_START)}[\s\S]*?{re.escape(STYLE_END)}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        rf"{re.escape(LEGACY_STYLE_START)}[\s\S]*?{re.escape(LEGACY_STYLE_END)}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        rf"{re.escape(HEADER_START)}[\s\S]*?{re.escape(HEADER_END)}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        rf"{re.escape(LEGACY_HEADER_START)}[\s\S]*?{re.escape(LEGACY_HEADER_END)}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"<nav\b[^>]*class=[\"'][^\"']*(navbar|airdata-header)[^\"']*[\"'][\s\S]*?</nav>",
        "",
        content,
        flags=re.IGNORECASE,
    )
    return content


def remove_widoco_sidebar(content):
    content = re.sub(
        r"<div\b[^>]*class=[\"'][^\"']*status[^\"']*[\"'][\s\S]*?</div>\s*</div>",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"<div\b[^>]*class=[\"'][^\"']*status[^\"']*[\"'][\s\S]*?</div>",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"<div\b[^>]*id=[\"']sidebar[\"'][\s\S]*?</div>",
        "",
        content,
        flags=re.IGNORECASE,
    )
    return content


def insert_header(content, style_block, nav_block, prefix):
    style_tag = style_block.replace("{{prefix}}", prefix)
    nav_tag = nav_block.replace("{{prefix}}", prefix)
    content = content.replace("\n\\1\n", "\n").replace("\n\\1", "\n")

    if STYLE_START in content and STYLE_END in content:
        content = re.sub(
            rf"{re.escape(STYLE_START)}[\\s\\S]*?{re.escape(STYLE_END)}",
            f"{STYLE_START}\n{style_tag}\n{STYLE_END}",
            content,
            flags=re.IGNORECASE,
        )
    else:
        content = content.replace(
            "</head>",
            f"\n{STYLE_START}\n{style_tag}\n{STYLE_END}\n</head>",
            1,
        )

    if HEADER_START in content and HEADER_END in content:
        content = re.sub(
            rf"{re.escape(HEADER_START)}[\\s\\S]*?{re.escape(HEADER_END)}",
            nav_tag,
            content,
            flags=re.IGNORECASE,
        )
    else:
        def insert_nav(match):
            return match.group(1) + "\n" + nav_tag

        content = re.sub(
            r"(<body[^>]*>)",
            insert_nav,
            content,
            count=1,
            flags=re.IGNORECASE,
        )
    return content


def normalize_file(path, mode, style_block, nav_block, site_dir):
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    content = content.replace("\n\\1\n", "\n").replace("\n\\1", "\n").replace("\\1", "")
    content = ensure_structure(content)
    content = remove_existing_headers(content)
    if mode == "widoco":
        content = remove_widoco_sidebar(content)

    prefix = prefix_for_path(path, site_dir)
    content = insert_header(content, style_block, nav_block, prefix)
    content = content.replace("\n\\1\n", "\n").replace("\n\\1", "\n").replace("\\1", "")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def main(site_dir):
    style_block, nav_block = get_header_template()

    portal_pages = [
        "index.html",
        "statistics.html",
        "versions.html",
        "changelog.html",
        "quality_report.html",
        "quality_report_extended.html",
        "quality-guide.html",
        "logic_report.html",            # NOVO: Validação de axiomas lógicos
        "llm_readability.html",         # NOVO: LLM-readability
        "sparql_validation.html",       # NOVO: Validação SPARQL
        "competency_report.html",       # NOVO: Perguntas de competência
        "delta_report.html",            # NOVO: Relatório delta
        "development.html",
    ]
    widoco_pages = [
        os.path.join("docs", "index-pt.html"),
    ]
    provenance_dir = os.path.join(site_dir, "docs", "provenance")
    if os.path.isdir(provenance_dir):
        for name in os.listdir(provenance_dir):
            if name.endswith(".html"):
                widoco_pages.append(os.path.join("docs", "provenance", name))

    webvowl_pages = [
        os.path.join("docs", "webvowl", "index.html"),
    ]

    for name in portal_pages:
        path = os.path.join(site_dir, name)
        if os.path.exists(path):
            normalize_file(path, "portal", style_block, nav_block, site_dir)

    for name in widoco_pages:
        path = os.path.join(site_dir, name)
        if os.path.exists(path):
            normalize_file(path, "widoco", style_block, nav_block, site_dir)

    for name in webvowl_pages:
        path = os.path.join(site_dir, name)
        if os.path.exists(path):
            normalize_file(path, "webvowl", style_block, nav_block, site_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normaliza o cabeçalho de arquivos HTML do projeto.")
    parser.add_argument('--site-dir', required=True, help='Diretório raiz do site a ser processado.')

    args = parser.parse_args()

    print("🔝 Normalizando cabeçalho do site AirData...")
    main(args.site_dir)
    print("✅ Concluído!")
