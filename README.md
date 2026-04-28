# AirData Ontology

Sistema de avaliacao de qualidade e documentacao para ontologias OWL.

**Principio fundamental:** A ontologia OWL e a fonte da verdade conceitual do projeto.

## Estrutura do Projeto

```
airdata-owl/
│
├── ontology/                # FONTE DA VERDADE
│   └── airdata_owl_v*.owl   # Ontologias versionadas
│
├── src/                     # CODIGO FONTE
│   ├── analysis/           # Scripts de analise de qualidade
│   │   ├── quality_report.py
│   │   ├── logic_validator.py
│   │   ├── llm_readability.py
│   │   ├── sparql_validator.py
│   │   └── competency_tester.py
│   │
│   ├── generators/         # Geradores de relatorios
│   │   ├── statistics.py
│   │   ├── changelog.py
│   │   └── versions.py
│   │
│   └── postprocess/        # Pos-processamento HTML
│       ├── normalize_links.py
│       └── normalize_header.py
│
├── tools/                   # FERRAMENTAS EXTERNAS
│   ├── robot.jar           # Validacao OWL
│   └── widoco.jar          # Documentacao HTML
│
├── config/                  # CONFIGURACAO
│   ├── competency_questions.json
│   └── requirements.txt
│
├── output/                  # SAIDA GERADA
│   ├── site/               # Site HTML publico
│   └── data/               # JSONs de relatorios
│
├── make.py                  # CLI principal
└── README.md
```

## Uso Rapido

```bash
# Ativar ambiente
source ~/ai-envs/airdata-owl/bin/activate

# Ver estado do projeto
python make.py status

# Executar pipeline completo
python make.py all

# Apenas analises de qualidade
python make.py analyze

# Apenas documentacao WIDOCO
python make.py docs

# Visualizar site localmente
python make.py serve
```

## Workflow

```
ontology/           src/              output/site/
   │                 │                    │
   │  ┌──────────────┴──────────────┐    │
   │  │                             │    │
   ▼  ▼                             ▼    ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│  .owl   │ --> │ scripts │ --> │  .html  │
│ (fonte) │     │ Python  │     │ (site)  │
└─────────┘     └─────────┘     └─────────┘
```

1. Editar ontologia no Protege
2. Salvar em `ontology/airdata_owl_vX.Y.Z.owl`
3. Executar `python make.py all`
4. Revisar relatorios em `output/site/`

## Relatorios Gerados

| Relatorio | Descricao |
|-----------|-----------|
| quality_report.html | Analise de qualidade geral |
| logic_report.html | Validacao de axiomas logicos |
| llm_readability.html | Legibilidade para LLMs |
| competency_report.html | Perguntas de competencia |
| sparql_validation.html | Queries SPARQL |
| statistics.html | Estatisticas estruturais |
| changelog.html | Historico de mudancas |
| docs/index-pt.html | Documentacao WIDOCO |

## Requisitos

- Python 3.10+
- Java 11+ (para WIDOCO e ROBOT)

## Setup Inicial

```bash
# Criar ambiente virtual
python3 -m venv ~/ai-envs/airdata-owl

# Ativar e instalar dependencias
source ~/ai-envs/airdata-owl/bin/activate
pip install -r config/requirements.txt
```

## Versionamento de Ontologias

**Formato obrigatorio:** `airdata_owl_vX.Y.Z.owl`

| Componente    | Quando incrementar                                                       |
| ------------- | ------------------------------------------------------------------------ |
| **Major (X)** | Remocao de classes/propriedades, mudanca de hierarquia, alteracao de IRI |
| **Minor (Y)** | Novas classes, novas propriedades, novos individuos                      |
| **Patch (Z)** | Correcoes tipograficas, ajustes de metadados                             |

**Regras:**

- Sempre usar tres digitos: `v1.0.0` (nao `v1.0`)
- Manter prefixo: `airdata_owl_`
- Nao usar sufixos: nada de `_final`, `_improved`
- Zerar numeros a direita ao incrementar: `v1.2.0` → `v2.0.0`

## Links

- Portal: https://www.airdata.ita.br
- Docs: https://airdata-ita.github.io/ita-airdata-owl/index.html
- GitHub: https://github.com/ita-airdata
