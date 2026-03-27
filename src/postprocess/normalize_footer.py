#!/usr/bin/env python3
"""
normalize_footer.py - Normaliza o rodape de todas as paginas HTML do site AirData.

Regra Canonica:
- O template do rodape esta embutido diretamente neste script
- Nenhuma pagina pode definir, gerar ou manter rodape proprio
- O script remove qualquer <footer> existente e insere o canonico antes de </body>
"""

import os
import re
import argparse


FOOTER_START = "<!-- AirData Footer Start -->"
FOOTER_END = "<!-- AirData Footer End -->"
FOOTER_STYLE_START = "<!-- AirData Footer Style Start -->"
FOOTER_STYLE_END = "<!-- AirData Footer Style End -->"

# Template CSS do rodape (embutido)
FOOTER_CSS_TEMPLATE = """/* Footer Styles */
.footer {
  background-color: #f6f8fa;
  border-top: 1px solid #d1d5da;
  padding-top: 32px;
  margin-top: 60px;
  text-align: center;
  color: #586069;
  padding-bottom: 0;
}

.footer-content {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 32px;
}

.footer-org {
  font-size: 1rem;
  margin: 0;
}

.footer-links {
  display: flex;
  gap: 24px;
  margin: 1rem 0;
}

.footer-links a {
  color: #003C7D;
  text-decoration: none;
  font-weight: 500;
}

.footer-links a:hover {
  text-decoration: underline;
}

.footer-copyright {
  margin: 0;
  opacity: 0.8;
  font-size: 0.9rem;
}

.footer-bottom-bar {
  height: 8px;
  background-color: #003C7D;
  width: 100%;
}"""

# Template HTML do rodape (embutido)
FOOTER_HTML_TEMPLATE = """<footer class="footer">
    <div class="footer-content">
        <p class="footer-org"><strong>Instituto Tecnológico de Aeronáutica - ITA</strong></p>
        <div class="footer-links">
            <a href="https://www.airdata.ita.br" target="_blank">Portal AirData</a>
            <a href="https://github.com/ita-airdata/OntoSite" target="_blank">GitHub</a>
        </div>
        <p class="footer-copyright">
            © 2026 Projeto AirData - Todos os direitos reservados
        </p>
    </div>
    <div class="footer-bottom-bar"></div>
</footer>"""


def get_footer_template():
    """Retorna os templates de HTML e CSS do rodape embutidos."""
    return FOOTER_HTML_TEMPLATE, FOOTER_CSS_TEMPLATE


def remove_existing_footers(content):
    """Remove todos os footers existentes do HTML."""
    # Remove footer marcado com comentarios AirData
    content = re.sub(
        rf"{re.escape(FOOTER_START)}[\s\S]*?{re.escape(FOOTER_END)}",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # Remove estilo de footer marcado
    content = re.sub(
        rf"{re.escape(FOOTER_STYLE_START)}[\s\S]*?{re.escape(FOOTER_STYLE_END)}",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # Remove qualquer tag <footer> existente (Widoco, ROBOT, etc.)
    content = re.sub(
        r"<footer\b[^>]*>[\s\S]*?</footer>",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # Remove estilos inline de footer (.footer { ... })
    content = re.sub(
        r"/\*\s*Footer\s*Styles?\s*\*/[\s\S]*?(?=\n\s*/\*|\n\s*</style>|\n\s*$)",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # Remove blocos de estilo .footer duplicados
    content = re.sub(
        r"\.footer\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"\.footer-content\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"\.footer-org\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"\.footer-links\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"\.footer-links\s+a\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"\.footer-links\s+a:hover\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"\.footer-copyright\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(
        r"\.footer-bottom-bar\s*\{[^}]*\}",
        "",
        content,
        flags=re.IGNORECASE,
    )

    return content


def insert_footer_style(content, footer_css):
    """Insere o CSS do footer no <head>."""
    style_block = f"""
{FOOTER_STYLE_START}
<style>
{footer_css}
</style>
{FOOTER_STYLE_END}
"""
    # Insere antes de </head>
    if "</head>" in content:
        content = content.replace("</head>", f"{style_block}\n</head>", 1)
    elif "</HEAD>" in content:
        content = content.replace("</HEAD>", f"{style_block}\n</HEAD>", 1)

    return content


def insert_footer_html(content, footer_html):
    """Insere o HTML do footer antes de </body>."""
    footer_block = f"""
{FOOTER_START}
{footer_html}
{FOOTER_END}
"""
    # Insere antes de </body>
    if "</body>" in content:
        content = content.replace("</body>", f"{footer_block}\n</body>", 1)
    elif "</BODY>" in content:
        content = content.replace("</BODY>", f"{footer_block}\n</BODY>", 1)

    return content


def normalize_file(path, footer_html, footer_css):
    """Normaliza o footer de um arquivo HTML."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Remove footers existentes
    content = remove_existing_footers(content)

    # Insere o CSS do footer
    content = insert_footer_style(content, footer_css)

    # Insere o HTML do footer
    content = insert_footer_html(content, footer_html)

    # Limpa linhas vazias multiplas
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Salva apenas se houve mudanca
    if content != original_content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main(site_dir):
    """Processa todas as paginas HTML do site."""
    footer_html, footer_css = get_footer_template()

    # Lista de paginas que devem receber o rodape
    pages = [
        "index.html",
        "development.html",
        "statistics.html",
        "versions.html",
        "changelog.html",
        "quality_report.html",
        "quality_report_extended.html",
        "quality-guide.html",
        "logic_report.html",            # NOVO: Validação de axiomas lógicos
        "llm_readability.html",         # NOVO: LLM-readability
        "sparql_validation.html",       # NOVO: Validação SPARQL
        os.path.join("docs", "index-pt.html"),
        os.path.join("docs", "webvowl", "index.html"),
    ]

    # Adiciona paginas de provenance se existirem
    provenance_dir = os.path.join(site_dir, "docs", "provenance")
    if os.path.isdir(provenance_dir):
        for name in os.listdir(provenance_dir):
            if name.endswith(".html"):
                pages.append(os.path.join("docs", "provenance", name))

    processed = 0
    modified = 0

    for page in pages:
        path = os.path.join(site_dir, page)
        if os.path.exists(path):
            was_modified = normalize_file(path, footer_html, footer_css)
            processed += 1
            if was_modified:
                modified += 1
                print(f"  [OK] {page}")
            else:
                print(f"  [--] {page} (sem mudancas)")
        else:
            print(f"  [!!] {page} (nao encontrado)")

    print(f"\nResumo: {modified}/{processed} arquivos modificados")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Normaliza o rodape de arquivos HTML do projeto AirData."
    )
    parser.add_argument(
        "--site-dir",
        required=True,
        help="Diretorio raiz do site a ser processado."
    )

    args = parser.parse_args()

    print("🦶 Normalizando rodape do site AirData...")
    main(args.site_dir)
    print("✅ Concluido!")
