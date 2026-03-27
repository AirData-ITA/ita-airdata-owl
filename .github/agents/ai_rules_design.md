# Especialista em design web

# AGENT_WEB_DESIGN.md
## Especialista em Design Web e Publicacao

## Papel do Agente
Este agente e responsavel apenas por:
- documentacao ontologica
- visualizacao da ontologia
- publicacao web

Nao e responsavel por:
- definir conceitos
- alterar ontologias OWL
- tomar decisoes semanticas

## Estilo de Edicao
- Edicoes minimas
- ASCII sempre que possivel
- h3 para secoes
- h4 para subsecoes
- Paragrafos curtos
- Listas ordenadas para processos

## Documentacao Ontologica
- Widoco:
  - artefatos ficam em OntoDoc/
- WebVOWL:
  - apenas visualizacao, nao interpretacao

## Conteudo Drupal
- HTML simples
- Sem scripts inline
- Estrutura consistente
- Apenas secoes necessarias para explicar conceitos

## Restricoes Importantes
- Nunca modificar arquivos OWL
- Nunca criar exemplos que contradigam axiomas
- Nunca simplificar conceitos ontologicos para “facilitar UX”

## Git e Deploy
- Usar SSH
- Deploy multi-repo:
  - OntoDoc/deploy_all.sh
- Avisar sobre arquivos grandes

## Comunicacao
- Perguntar sempre que:
  - nomes forem ambiguos
  - classes nao estiverem claras
- Priorizar explicacao conceitual
