# Deploys Discloud

Esta pasta guarda os arquivos `.zip` usados para deploy manual na Discloud.

Os zips não são enviados ao GitHub, porque o `.gitignore` ignora `*.zip`.

Use este padrão para próximos arquivos:

```text
YoshiBot-Discloud-YYYYMMDD-HHMM-descricao-curta.zip
```

Exemplo:

```text
YoshiBot-Discloud-20260820-1531-log-mensagens-deletadas.zip
```

Antes de enviar um zip para a Discloud, confirme que ele não contém:

- `.env`
- `.git/`
- `.venv/`
- `venv/`
- `__pycache__/`
- `.idea/`
- `.vscode/`
- arquivos `.pyc`
- zips antigos
