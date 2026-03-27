#!/usr/bin/env python3
"""
AirData Ontology - Pipeline de Qualidade e Documentacao

Script unificado para avaliar qualidade da ontologia e gerar documentacao.

A ONTOLOGIA OWL E A FONTE DA VERDADE.
Este script existe apenas para documentar, visualizar e publicar.

Uso:
    python make.py status      # Ver estado atual do projeto
    python make.py analyze     # Executar analises de qualidade
    python make.py docs        # Gerar documentacao WIDOCO
    python make.py all         # Executar pipeline completo
    python make.py clean       # Limpar arquivos gerados

Autor: Projeto AirData (ITA)
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURACAO
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.resolve()

# Estrutura de diretórios
OWL_DIR = PROJECT_ROOT / "ontology"
SRC_DIR = PROJECT_ROOT / "src"
TOOLS_DIR = PROJECT_ROOT / "tools"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"
SITE_DIR = OUTPUT_DIR / "site"
DATA_DIR = OUTPUT_DIR / "data"

# Subdiretórios de código
ANALYSIS_DIR = SRC_DIR / "analysis"
GENERATORS_DIR = SRC_DIR / "generators"
POSTPROCESS_DIR = SRC_DIR / "postprocess"

# Ferramentas Java
ROBOT_JAR = TOOLS_DIR / "robot.jar"
WIDOCO_JAR = TOOLS_DIR / "widoco.jar"

# Ambiente virtual
VENV_PATH = Path.home() / "ai-envs" / "airdata-owl"

# =============================================================================
# UTILIDADES
# =============================================================================

class Colors:
    """Cores ANSI para terminal."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(msg: str):
    """Imprime cabecalho formatado."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")


def print_step(msg: str):
    """Imprime passo do processo."""
    print(f"  {Colors.CYAN}>{Colors.ENDC} {msg}")


def print_success(msg: str):
    """Imprime mensagem de sucesso."""
    print(f"  {Colors.GREEN}OK{Colors.ENDC} {msg}")


def print_error(msg: str):
    """Imprime mensagem de erro."""
    print(f"  {Colors.RED}ERRO{Colors.ENDC} {msg}")


def print_warning(msg: str):
    """Imprime aviso."""
    print(f"  {Colors.YELLOW}!{Colors.ENDC} {msg}")


def get_latest_owl() -> Path:
    """Encontra a ontologia mais recente no diretorio OntoOwl."""
    owl_files = list(OWL_DIR.glob("airdata_owl_v*.owl"))
    if not owl_files:
        # Tenta qualquer .owl
        owl_files = list(OWL_DIR.glob("*.owl"))
    if not owl_files:
        return None
    # Ordena por versao (se seguir padrao) ou data de modificacao
    return max(owl_files, key=lambda f: f.stat().st_mtime)


def run_python(script_path: Path, args: list = None) -> bool:
    """Executa script Python."""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print_error(f"Falha ao executar {script_path.name}: {e}")
        return False


def run_java(jar: Path, args: list) -> bool:
    """Executa JAR Java."""
    cmd = ["java", "-jar", str(jar)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        print_error("Java nao encontrado. Instale Java 11+ para usar WIDOCO/ROBOT.")
        return False
    except Exception as e:
        print_error(f"Falha ao executar {jar.name}: {e}")
        return False


# =============================================================================
# COMANDOS
# =============================================================================

def cmd_status():
    """Mostra estado atual do projeto."""
    print_header("Estado do Projeto AirData Ontology")

    # Ontologias
    print(f"{Colors.BOLD}Ontologias (ontology/):{Colors.ENDC}")
    owl_files = sorted(OWL_DIR.glob("*.owl"), key=lambda f: f.stat().st_mtime, reverse=True)
    if owl_files:
        for f in owl_files[:5]:
            size = f.stat().st_size / 1024
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            latest = " <- mais recente" if f == owl_files[0] else ""
            print(f"  {f.name:40} {size:>7.1f} KB  {mtime}{Colors.GREEN}{latest}{Colors.ENDC}")
    else:
        print_warning("Nenhuma ontologia encontrada")

    # Scripts de analise
    print(f"\n{Colors.BOLD}Scripts de Analise (src/analysis/):{Colors.ENDC}")
    analysis_scripts = [
        ("quality_report.py", "Relatorio de qualidade geral"),
        ("logic_validator.py", "Validacao de axiomas logicos"),
        ("llm_readability.py", "Analise de legibilidade LLM"),
        ("competency_tester.py", "Teste de perguntas de competencia"),
        ("sparql_validator.py", "Validacao de queries SPARQL"),
    ]
    for script, desc in analysis_scripts:
        exists = (ANALYSIS_DIR / script).exists()
        status = f"{Colors.GREEN}OK{Colors.ENDC}" if exists else f"{Colors.RED}--{Colors.ENDC}"
        print(f"  [{status}] {script:35} {desc}")

    # Scripts geradores
    print(f"\n{Colors.BOLD}Scripts Geradores (src/generators/):{Colors.ENDC}")
    generator_scripts = [
        ("statistics.py", "Estatisticas estruturais"),
        ("changelog.py", "Historico de mudancas"),
        ("delta_report.py", "Relatorio delta entre versoes"),
        ("versions.py", "Catalogo de versoes"),
    ]
    for script, desc in generator_scripts:
        exists = (GENERATORS_DIR / script).exists()
        status = f"{Colors.GREEN}OK{Colors.ENDC}" if exists else f"{Colors.RED}--{Colors.ENDC}"
        print(f"  [{status}] {script:35} {desc}")

    # Ferramentas Java
    print(f"\n{Colors.BOLD}Ferramentas Java (tools/):{Colors.ENDC}")
    for jar, desc in [(ROBOT_JAR, "Validacao OWL"), (WIDOCO_JAR, "Documentacao HTML")]:
        exists = jar.exists()
        status = f"{Colors.GREEN}OK{Colors.ENDC}" if exists else f"{Colors.RED}--{Colors.ENDC}"
        size = f"({jar.stat().st_size / 1024 / 1024:.1f} MB)" if exists else ""
        print(f"  [{status}] {jar.name:20} {desc} {size}")

    # Relatorios gerados
    print(f"\n{Colors.BOLD}Relatorios Gerados (output/site/):{Colors.ENDC}")
    reports = [
        "quality_report.html",
        "logic_report.html",
        "llm_readability.html",
        "competency_report.html",
        "sparql_validation.html",
        "statistics.html",
        "changelog.html",
        "docs/index-pt.html",
    ]
    for report in reports:
        path = SITE_DIR / report
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"  {Colors.GREEN}OK{Colors.ENDC} {report:35} {mtime}")
        else:
            print(f"  {Colors.YELLOW}--{Colors.ENDC} {report}")

    print()
    return True


def cmd_analyze():
    """Executa analises de qualidade da ontologia."""
    print_header("Analise de Qualidade da Ontologia")

    owl_file = get_latest_owl()
    if not owl_file:
        print_error("Nenhuma ontologia encontrada em ontology/")
        return False

    print(f"Ontologia: {Colors.CYAN}{owl_file.name}{Colors.ENDC}\n")

    analyses = [
        (ANALYSIS_DIR / "logic_validator.py", [
            str(owl_file),
            "--output", str(SITE_DIR / "logic_report.html"),
            "--json", str(SITE_DIR / "logic_report.json")
        ], "Validacao de axiomas logicos"),

        (ANALYSIS_DIR / "llm_readability.py", [
            str(owl_file),
            "--output", str(SITE_DIR / "llm_readability.html"),
            "--json", str(SITE_DIR / "llm_readability.json")
        ], "Analise de legibilidade LLM"),

        (ANALYSIS_DIR / "sparql_validator.py", [
            str(owl_file),
            "--output", str(SITE_DIR / "sparql_validation.html"),
            "--json", str(SITE_DIR / "sparql_validation.json")
        ], "Validacao de queries SPARQL"),

        (ANALYSIS_DIR / "competency_tester.py", [
            str(owl_file),
            str(CONFIG_DIR / "competency_questions.json"),
            "--output", str(SITE_DIR / "competency_report.html"),
            "--json", str(SITE_DIR / "competency_report.json")
        ], "Teste de perguntas de competencia"),

        (GENERATORS_DIR / "statistics.py", [
            "--owl-dir", str(OWL_DIR),
            "--site-dir", str(SITE_DIR),
            "--robot-jar", str(ROBOT_JAR)
        ], "Estatisticas estruturais"),

        (GENERATORS_DIR / "changelog.py", [
            "--owl-dir", str(OWL_DIR),
            "--output-file", str(SITE_DIR / "changelog.html")
        ], "Historico de mudancas"),
    ]

    success_count = 0
    for script_path, args, desc in analyses:
        print_step(desc)
        if run_python(script_path, args):
            print_success(script_path.name)
            success_count += 1
        else:
            print_error(script_path.name)

    print(f"\n{Colors.BOLD}Resultado:{Colors.ENDC} {success_count}/{len(analyses)} analises concluidas")

    # Aplica header/footer
    print_step("Aplicando header/footer padrao...")
    run_python(POSTPROCESS_DIR / "normalize_header.py", ["--site-dir", str(SITE_DIR)])
    run_python(POSTPROCESS_DIR / "normalize_footer.py", ["--site-dir", str(SITE_DIR)])

    return success_count == len(analyses)


def cmd_docs():
    """Gera documentacao WIDOCO."""
    print_header("Geracao de Documentacao WIDOCO")

    if not WIDOCO_JAR.exists():
        print_error(f"WIDOCO nao encontrado: {WIDOCO_JAR}")
        return False

    owl_file = get_latest_owl()
    if not owl_file:
        print_error("Nenhuma ontologia encontrada")
        return False

    print(f"Ontologia: {Colors.CYAN}{owl_file.name}{Colors.ENDC}\n")

    # Limpa pasta docs
    docs_dir = SITE_DIR / "docs"
    if docs_dir.exists():
        import shutil
        shutil.rmtree(docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    print_step("Executando WIDOCO...")
    success = run_java(WIDOCO_JAR, [
        "-ontFile", str(owl_file),
        "-outFolder", str(docs_dir),
        "-rewriteAll",
        "-getOntologyMetadata",
        "-webVowl",
        "-uniteSections",
        "-includeImportedOntologies",
        "-lang", "pt"
    ])

    if success:
        print_success("Documentacao gerada")

        # Pos-processamento
        print_step("Normalizando links...")
        run_python(POSTPROCESS_DIR / "normalize_links.py", ["--html-file", str(docs_dir / "index-pt.html")])

        print_step("Normalizando iframe...")
        run_python(POSTPROCESS_DIR / "normalize_iframe.py", ["--html-file", str(docs_dir / "index-pt.html")])

        print_step("Atualizando catalogo de versoes...")
        run_python(GENERATORS_DIR / "versions.py", [
            "--owl-dir", str(OWL_DIR),
            "--output-file", str(SITE_DIR / "versions.json")
        ])

        return True
    else:
        print_error("Falha na geracao de documentacao")
        return False


def cmd_all():
    """Executa pipeline completo."""
    print_header("Pipeline Completo de Documentacao")

    owl_file = get_latest_owl()
    if not owl_file:
        print_error("Nenhuma ontologia encontrada em OntoOwl/")
        return False

    print(f"Ontologia: {Colors.CYAN}{owl_file.name}{Colors.ENDC}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    steps = [
        ("Documentacao WIDOCO", cmd_docs),
        ("Analises de Qualidade", cmd_analyze),
    ]

    results = []
    for name, func in steps:
        print(f"\n{Colors.BOLD}[{len(results)+1}/{len(steps)}] {name}{Colors.ENDC}")
        results.append((name, func()))

    # Resumo
    print_header("Resumo do Pipeline")
    for name, success in results:
        status = f"{Colors.GREEN}OK{Colors.ENDC}" if success else f"{Colors.RED}FALHA{Colors.ENDC}"
        print(f"  [{status}] {name}")

    print(f"\n{Colors.BOLD}Arquivos gerados em:{Colors.ENDC}")
    print(f"  {SITE_DIR}/")
    print(f"\n{Colors.BOLD}Documentacao principal:{Colors.ENDC}")
    print(f"  {SITE_DIR}/docs/index-pt.html")

    return all(r[1] for r in results)


def cmd_clean():
    """Limpa arquivos gerados."""
    print_header("Limpeza de Arquivos Gerados")

    to_clean = [
        SITE_DIR / "docs",
        SITE_DIR / "quality_report.html",
        SITE_DIR / "logic_report.html",
        SITE_DIR / "logic_report.json",
        SITE_DIR / "llm_readability.html",
        SITE_DIR / "llm_readability.json",
        SITE_DIR / "sparql_validation.html",
        SITE_DIR / "sparql_validation.json",
        SITE_DIR / "competency_report.html",
        SITE_DIR / "competency_report.json",
        SITE_DIR / "statistics.html",
        SITE_DIR / "statistics.json",
        SITE_DIR / "changelog.html",
        SITE_DIR / "versions.json",
    ]

    import shutil
    for path in to_clean:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print_step(f"Removido: {path.name}")

    print_success("Limpeza concluida")
    return True


def cmd_serve():
    """Inicia servidor HTTP local para visualizar o site."""
    import http.server
    import socketserver
    import webbrowser

    print_header("Servidor Local")

    port = 8080
    os.chdir(SITE_DIR)

    print(f"Servindo em: {Colors.CYAN}http://localhost:{port}{Colors.ENDC}")
    print(f"Diretorio: {SITE_DIR}")
    print(f"\nPressione Ctrl+C para parar.\n")

    # Abre navegador
    webbrowser.open(f"http://localhost:{port}")

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")

    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AirData Ontology - Pipeline de Qualidade e Documentacao",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos disponiveis:
  status    Mostra estado atual do projeto
  analyze   Executa analises de qualidade
  docs      Gera documentacao WIDOCO
  all       Executa pipeline completo
  serve     Inicia servidor local para visualizar o site
  clean     Limpa arquivos gerados

Exemplos:
  python make.py status
  python make.py all
  python make.py serve
"""
    )

    parser.add_argument(
        "command",
        choices=["status", "analyze", "docs", "all", "serve", "clean"],
        help="Comando a executar"
    )

    args = parser.parse_args()

    # Muda para diretorio do projeto
    os.chdir(PROJECT_ROOT)

    commands = {
        "status": cmd_status,
        "analyze": cmd_analyze,
        "docs": cmd_docs,
        "all": cmd_all,
        "serve": cmd_serve,
        "clean": cmd_clean,
    }

    success = commands[args.command]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
