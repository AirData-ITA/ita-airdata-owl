# AirData Ontology - Instrucoes para Agentes

**Ativacao de Sessao:** "Load Setup"

## Contexto

1. [.github/copilot-instructions.md](.github/copilot-instructions.md) - instrucoes e fluxo de trabalho
2. [.github/agents/ai_rules_design.md](.github/agents/ai_rules_design.md) - regras de design
3. [.github/agents/ai_contexto_geral.md](.github/agents/ai_contexto_geral.md) - visao geral do projeto

## Ambiente Python

```bash
source ~/ai-envs/airdata-owl/bin/activate
```

## Estrutura do Projeto

```text
airdata-owl/
├── ontology/                    # FONTE DA VERDADE - Arquivos OWL
│   ├── airdata_owl_v0.0.1.owl
│   └── airdata_owl_v0.0.2.owl
│
├── src/                         # CODIGO FONTE
│   ├── analysis/                # Scripts de analise de qualidade
│   │   ├── quality_report.py        # Validacao sintatica (ROBOT)
│   │   ├── logic_validator.py       # Axiomas logicos OWL
│   │   ├── llm_readability.py       # Usabilidade para LLMs
│   │   ├── sparql_validator.py      # Validacao SPARQL
│   │   └── competency_tester.py     # Perguntas de competencia
│   │
│   ├── generators/              # Geradores de relatorios/dados
│   │   ├── statistics.py            # Estatisticas da ontologia
│   │   ├── changelog.py             # Historico de mudancas
│   │   ├── delta_report.py          # Comparacao entre versoes
│   │   ├── versions.py              # Gestao de versoes
│   │   └── version_compare.py       # Utilitario de comparacao
│   │
│   └── postprocess/             # Pos-processamento HTML
│       ├── normalize_header.py      # Cabecalho padrao
│       ├── normalize_footer.py      # Rodape padrao
│       ├── normalize_links.py       # Links relativos
│       └── normalize_iframe.py      # Correcao de iframes
│
├── tools/                       # FERRAMENTAS EXTERNAS (JARs)
│   ├── robot.jar                    # Validacao OWL
│   └── widoco.jar                   # Documentacao WIDOCO
│
├── config/                      # CONFIGURACAO
│   ├── competency_questions.json    # Perguntas de competencia
│   └── requirements.txt             # Dependencias Python
│
├── output/                      # SAIDA GERADA
│   ├── site/                        # Site HTML publicavel
│   │   ├── index.html
│   │   ├── docs/                    # Documentacao WIDOCO
│   │   └── ...
│   └── data/                        # Dados JSON
│       └── *.json
│
└── make.py                      # CLI UNIFICADO
```

## Workflow Principal

```bash
python make.py status   # Ver estado do projeto
python make.py analyze  # Executar todas as analises
python make.py docs     # Gerar documentacao WIDOCO
python make.py all      # Pipeline completo
python make.py serve    # Servidor local para visualizar site
```

## Principio Fundamental

**A ontologia OWL e a fonte da verdade.**

Scripts existem apenas para:

- Documentar (WIDOCO)
- Analisar qualidade (ROBOT, validadores)
- Visualizar (WebVOWL)
- Publicar (site estatico)

## Pipeline de Analise

1. **Validacao Sintatica** - ROBOT verifica sintaxe OWL
2. **Axiomas Logicos** - Analise de consistencia logica
3. **Usabilidade LLM** - Legibilidade para modelos de linguagem
4. **Validacao SPARQL** - Testes de consultas
5. **Perguntas de Competencia** - Verifica se ontologia responde perguntas chave

## Visualizacao Local

Sempre use servidor HTTP para visualizar o site localmente:

```bash
python make.py serve
# Acesse: http://localhost:8000
```

Nao abra arquivos via `file://` - causa erros de CORS no WebVOWL.
