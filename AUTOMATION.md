# Automacao de publicacao da ontologia AirData

Este repositorio e a fonte da verdade da ontologia. Existem dois fluxos:

- GitHub Actions, recomendado para publicacao automatica apos `git push`.
- Script local, util para testar e publicar pela sua maquina.

## GitHub Actions

O workflow fica em:

```text
.github/workflows/deploy.yml
```

Quando uma nova ontologia `ontology/airdata_owl_vX.Y.Z.owl` for enviada para a branch `main`, o GitHub Actions:

- instala Java 11 e Python 3.10;
- instala as dependencias de `config/requirements.txt`;
- roda `python make.py all`;
- publica apenas no GitHub Pages por padrao;
- envia `output/site` para a Lessonia somente se esse deploy for ativado explicitamente.

Importante: o job da Lessonia roda em runner do GitHub (`ubuntu-latest`). Se o SSH da Lessonia so for acessivel pela VPN/rede interna, esse job tambem dara timeout. Nesse caso, use um GitHub self-hosted runner em uma maquina que esteja dentro da VPN/rede do ITA, ou exponha um bastion/tunel SSH acessivel ao GitHub Actions.

### Deploy futuro para a Lessonia

Por enquanto, a Lessonia fica desligada. Para ativar no futuro, crie uma variable em `Settings > Secrets and variables > Actions > Variables`:

```text
LESSONIA_DEPLOY_ENABLED=true
```

Depois cadastre em `Settings > Secrets and variables > Actions > Repository secrets`:

```text
LESSONIA_HOST=161.24.29.22
LESSONIA_PORT=2222
LESSONIA_USER=guilhermetolentino
LESSONIA_PASSWORD=<senha>
LESSONIA_PATH=/caminho/do/site/na/lessonia
```

Nao coloque senha em arquivo do repositorio.

### Uso normal

```bash
git add ontology/airdata_owl_v0.0.3.owl
git commit -m "Add AirData ontology v0.0.3"
git push origin main
```

Tambem e possivel rodar manualmente em `Actions > Deploy AirData OWL Documentation > Run workflow`.

## Script local

O fluxo automatizado local fica em:

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
