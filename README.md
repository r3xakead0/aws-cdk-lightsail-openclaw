# AWS CDK Lightsail OpenClaw (Python + uv)

Proyecto base para aprovisionar OpenClaw en AWS Lightsail usando AWS CDK con Python y uv.

El stack usa el blueprint administrado de OpenClaw en Lightsail (recomendado por AWS).

## Requisitos

- Python 3.11+
- uv
- Node.js LTS (requerido por CDK)
- AWS CLI v2
- AWS CDK CLI (`npm install -g aws-cdk`)

## Estructura

- `app.py`: entrypoint CDK
- `stacks/lightsail_openclaw_stack.py`: stack principal
- `config/dev.json`: parametros de infraestructura
- `scripts/*.ps1`: comandos de sintesis/despliegue

## Configuracion inicial

1. Configura credenciales de AWS:

```powershell
aws configure
aws sts get-caller-identity
```

2. Edita `config/dev.json` con valores reales:

- `account`
- `region`
- `availability_zone`
- `key_pair_name`
- `ssh_cidr` (recomendado restringirlo, no usar `0.0.0.0/0` en produccion)

- `blueprint_id` recomendado: `openclaw_ls_1_0`
- `bundle_id` recomendado por AWS: `medium_3_0` (4 GB)

Puedes listar blueprints disponibles en tu region con:

```powershell
aws lightsail get-blueprints --query "blueprints[?contains(name, 'OpenClaw') || contains(blueprintId, 'openclaw')].[name,blueprintId,isActive,version]" --output table
```

3. Instala dependencias Python:

```powershell
uv sync
```

4. Bootstrapping de CDK (una vez por cuenta/region):

```powershell
./scripts/bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>
```

## Uso

Sintetizar:

```powershell
./scripts/synth.ps1
```

Ver cambios:

```powershell
./scripts/diff.ps1
```

Desplegar:

```powershell
./scripts/deploy.ps1
```

Eliminar stack:

```powershell
./scripts/destroy.ps1
```

## Que aprovisiona este stack

- Instancia Lightsail OpenClaw (blueprint administrado por defecto)
- Apertura de puertos publicos 22/80/443
- Static IP para endpoint estable
- Auto snapshots diarios

## Notas operativas

- El acceso inicial se completa con pairing desde la consola de Lightsail (Getting started + SSH web).
- La habilitacion de Bedrock se realiza con el script de la guia oficial en CloudShell.
- Al adjuntar o cambiar Static IP, es normal tener que re-parear navegadores/dispositivos.
