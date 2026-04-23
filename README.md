# AWS CDK Lightsail OpenClaw (Python + uv)

Proyecto base para aprovisionar OpenClaw en AWS Lightsail usando AWS CDK con Python y uv.

El stack usa el blueprint administrado de OpenClaw en Lightsail (recomendado por AWS).

## Requisitos

- Python 3.11+
- uv
- Node.js 22 LTS (requerido por CDK; version pinneada en `.nvmrc`)
- AWS CLI v2
- AWS CDK CLI (`npm install -g aws-cdk`)

## Estructura

- `app.py`: entrypoint CDK
- `stacks/lightsail_openclaw_stack.py`: stack principal
- `config/dev.json`: parametros de infraestructura
- `scripts/windows/dev/*.ps1` y `scripts/windows/prod/*.ps1`: wrappers por ambiente para Windows PowerShell
- `scripts/linux-mac/dev/*` y `scripts/linux-mac/prod/*`: wrappers por ambiente para Linux/macOS

## Configuracion inicial

1. Configura credenciales de AWS:

```bash
aws configure
aws sts get-caller-identity
```

2. Edita `config/dev.json` con valores reales:

- `account`
- `region`
- `availability_zone`
- `key_pair_name`
- `ssh_cidr` (recomendado restringirlo, no usar `0.0.0.0/0` en produccion)
- `enable_auto_snapshot` (`false` por defecto; habilita snapshots diarios si es `true`)
- `snapshot_time_of_day_utc` (solo aplica cuando `enable_auto_snapshot=true`)
- `blueprint_id` recomendado: `openclaw_ls_1_0`
- `bundle_id` recomendado por AWS: `medium_3_0` (4 GB)

Puedes listar blueprints disponibles en tu region con:

```bash
aws lightsail get-blueprints --query "blueprints[?contains(name, 'OpenClaw') || contains(blueprintId, 'openclaw')].[name,blueprintId,isActive,version]" --output table
```

3. Instala dependencias Python:

```bash
uv sync
```

4. Alinea la version de Node.js (si usas nvm):

```bash
nvm use
```

5. Bootstrapping de CDK (una vez por cuenta/region):

Windows PowerShell (dev/prod):

```powershell
.\scripts\windows\dev\bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>
.\scripts\windows\prod\bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>
```

Linux/macOS (dev/prod):

```bash
./scripts/linux-mac/dev/bootstrap <ACCOUNT_ID> <REGION>
./scripts/linux-mac/prod/bootstrap <ACCOUNT_ID> <REGION>
```

## Generar e importar clave SSH (macOS/Windows)

Este proyecto usa `key_pair_name` para asociar una clave SSH a la instancia Lightsail.
La clave privada se guarda en tu maquina local y no se sube al repositorio.

Notas importantes:

- Para `aws lightsail import-key-pair`, usa clave publica tipo `ssh-rsa`.
- Si `key_pair_name` ya existe, elige otro nombre y actualizalo en `config/dev.json`.

### macOS

1. Genera la clave RSA local:

```bash
ssh-keygen -t rsa -b 4096 -m PEM -f ~/.ssh/openclaw-dev-key -C "openclaw-lightsail"
chmod 600 ~/.ssh/openclaw-dev-key
chmod 644 ~/.ssh/openclaw-dev-key.pub
```

2. Importa la clave publica a Lightsail:

```bash
aws lightsail import-key-pair \
  --key-pair-name openclaw-dev-key \
  --public-key-base64 "$(cat ~/.ssh/openclaw-dev-key.pub)" \
  --region us-east-1
```

3. Verifica que exista:

```bash
aws lightsail get-key-pairs --region us-east-1 --query "keyPairs[?name=='openclaw-dev-key'].name" --output table
```

### Windows PowerShell

1. Genera la clave RSA local:

```powershell
ssh-keygen -t rsa -b 4096 -m PEM -f "$HOME\.ssh\openclaw-dev-key" -C "openclaw-lightsail"
```

2. Importa la clave publica a Lightsail:

```powershell
$pub = Get-Content "$HOME\.ssh\openclaw-dev-key.pub" -Raw
aws lightsail import-key-pair `
  --key-pair-name openclaw-dev-key `
  --public-key-base64 $pub `
  --region us-east-1
```

3. Verifica que exista:

```powershell
aws lightsail get-key-pairs --region us-east-1 --query "keyPairs[?name=='openclaw-dev-key'].name" --output table
```

### Conectar por SSH despues del deploy

1. Asegura que `config/dev.json` tenga `key_pair_name` con el mismo nombre importado.
2. Despliega infraestructura.
3. Conecta por SSH usando la clave privada local.

Ejemplo (Linux/macOS):

```bash
ssh -i ~/.ssh/openclaw-dev-key ubuntu@<PUBLIC_IP>
```

Ejemplo (Windows PowerShell):

```powershell
ssh -i "$HOME\.ssh\openclaw-dev-key" ubuntu@<PUBLIC_IP>
```

No subas archivos de clave privada (`.pem`, `id_*`, `openclaw-dev-key`) al repositorio.

## Uso

### Windows PowerShell

Dev:

```powershell
.\scripts\windows\dev\synth.ps1
.\scripts\windows\dev\diff.ps1
.\scripts\windows\dev\deploy.ps1
.\scripts\windows\dev\destroy.ps1
```

Prod:

```powershell
.\scripts\windows\prod\synth.ps1
.\scripts\windows\prod\diff.ps1
.\scripts\windows\prod\deploy.ps1
.\scripts\windows\prod\destroy.ps1
```

### Linux/macOS

Dev:

```bash
./scripts/linux-mac/dev/synth
./scripts/linux-mac/dev/diff
./scripts/linux-mac/dev/deploy
./scripts/linux-mac/dev/destroy
```

Prod:

```bash
./scripts/linux-mac/prod/synth
./scripts/linux-mac/prod/diff
./scripts/linux-mac/prod/deploy
./scripts/linux-mac/prod/destroy
```

### Comandos directos (cualquier plataforma)

```bash
uv run cdk bootstrap aws://<ACCOUNT>/<REGION>
uv run cdk synth
uv run cdk diff
uv run cdk deploy --require-approval never
uv run cdk destroy --force
```

## Que aprovisiona este stack

- Instancia Lightsail OpenClaw (blueprint administrado por defecto)
- Apertura de puertos publicos 22/80/443
- Static IP para endpoint estable
- Auto snapshots diarios opcionales (`enable_auto_snapshot=true`)
- Rol IAM para que la instancia OpenClaw invoque Bedrock (sin paso manual en CloudShell)

## Notas operativas

- El acceso inicial se completa con pairing desde la consola de Lightsail (Getting started + SSH web).
- La habilitacion del rol Bedrock se ejecuta automaticamente durante `cdk deploy` y se elimina durante `cdk destroy`.
- Al adjuntar o cambiar Static IP, es normal tener que re-parear navegadores/dispositivos.
