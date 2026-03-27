# AGENT_PLATFORM_OVERVIEW

## Visao Geral da Plataforma AirData

## Idioma do Projeto

Sempre interagir em portugues.

## Contexto do Projeto
- Projeto: AirData (ITA)
- Natureza: Engenharia de Ontologias
- Organizacao GitHub: ita-airdata

## Restricoes Importantes
- Nunca modificar arquivos OWL
- Nunca criar exemplos que contradigam axiomas
- Nunca simplificar conceitos ontologicos para “facilitar UX”

## Repositorios Principais
- OntoOWLs: ontologias OWL (nucleo do projeto)
- OntoDoc: documentacao ontologica (Widoco)
- OntoSite: publicacao do site e docs
- OntoSetup: scripts de configuracao
- json_database

## Principio Arquitetural Fundamental
A ontologia OWL e a fonte da verdade conceitual do projeto.

## Natureza Ontologica
- O foco e:
  - classes
  - propriedades
  - axiomas
  - alinhamentos ontologicos
- Codigo, sites e scripts existem apenas para:
  - documentar
  - visualizar
  - publicar a ontologia

## Restricoes Conceituais
- Nunca reinterpretar a ontologia como:
  - modelo relacional
  - modelo OO
- Nunca propor mudancas sem explicitar impacto ontologico

## Links Canonicos
- GitHub: https://github.com/ita-airdata
- Portal: https://www.airdata.ita.br
- Docs: https://ita-airdata.github.io/OntoSite/docs/index-pt.html

## Principio Fundamental
Em caso de conflito:
- praticidade tecnica ❌
- coerencia ontologica ✅
