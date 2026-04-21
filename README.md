# AWS CDK Lightsail OpenClaw (Python + uv)

Proyecto base para aprovisionar OpenClaw en una instancia AWS Lightsail usando AWS CDK con Python y uv.

## Requisitos

- Python 3.11+
- uv
- Node.js LTS (requerido por CDK)
- AWS CLI v2
- AWS CDK CLI (`npm install -g aws-cdk`)

## Estructura

- `app.py`: entrypoint CDK
- `stacks/lightsail_openclaw_stack.py`: stack principal
- `config/prod.json`: parametros de infraestructura
- `scripts/*.ps1`: comandos de sintesis/despliegue

## Configuracion inicial

1. Configura credenciales de AWS:

```powershell
aws configure
aws sts get-caller-identity
```

2. Edita `config/prod.json` con valores reales:

- `account`
- `region`
- `availability_zone`
- `key_pair_name`
- `ssh_cidr` (recomendado restringirlo, no usar `0.0.0.0/0` en produccion)

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

- Instancia Lightsail Linux (Ubuntu 22.04 por defecto)
- Apertura de puertos publicos 22/80/443
- Static IP para endpoint estable
- Auto snapshots diarios
- User data para:
  - instalar Docker
  - descargar imagen de OpenClaw
  - iniciar contenedor `openclaw` en puerto 80 del host

## Notas operativas

- El contenedor usa `ghcr.io/opengovern/openclaw:latest` por defecto.
- Si necesitas una version fija, cambia `openclaw_image` en `config/prod.json`.
- Para TLS con dominio, agrega reverse proxy (Nginx/Caddy) en `user_data` o mediante configuracion posterior.
