# Automacao de publicacao da ontologia AirData

Este repositorio e a fonte da verdade da ontologia. O fluxo automatizado fica em:

```powershell
scripts\publish-airdata-ontology.ps1
```

## Fluxo recomendado

1. Salve a nova ontologia em `ontology\airdata_owl_vX.Y.Z.owl`.
2. Rode o script de publicacao.

```powershell
cd C:\Users\User\Documents\GitHub\ita-airdata-owl
powershell -ExecutionPolicy Bypass -File .\scripts\publish-airdata-ontology.ps1
```

Por padrao, o script:

- detecta a maior versao `airdata_owl_vX.Y.Z.owl`;
- executa `python make.py all`;
- copia `output\site` para o repositorio irmao `ita-airdata-ontology`;
- mostra o `git status` do site gerado.

## Publicar no GitHub

Para gerar, copiar, commitar e enviar os dois repositorios:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish-airdata-ontology.ps1 -Commit -Push
```

Tambem e possivel indicar explicitamente a versao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish-airdata-ontology.ps1 -OwlFile airdata_owl_v0.0.3.owl -Commit -Push
```

## Deploy para a Lessonia

O script ja usa estes defaults para a Lessonia:

- host: `161.24.29.22`
- port: `2222`
- user: `guilhermetolentino`

Configure apenas o caminho remoto e, se usar chave SSH, o arquivo da chave:

```powershell
$env:LESSONIA_PATH = "/var/www/airdata-ontology"
# Opcional:
$env:LESSONIA_SSH_KEY = "C:\Users\User\.ssh\id_ed25519"
```

Nao salve senha no repositorio. Se o servidor ainda usa senha, informe a senha quando o SSH/SCP pedir ou migre para chave SSH.

Depois execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish-airdata-ontology.ps1 -DeployLessonia
```

Se o servidor deve substituir completamente a pasta remota, use `-CleanRemote`.
Use isso apenas quando `LESSONIA_PATH` estiver conferido.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish-airdata-ontology.ps1 -DeployLessonia -CleanRemote
```

## Comando completo

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish-airdata-ontology.ps1 -OwlFile airdata_owl_v0.0.3.owl -Commit -Push -DeployLessonia
```
