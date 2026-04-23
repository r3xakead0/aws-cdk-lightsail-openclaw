# AGENTS

## Scope
- Single Python CDK app that provisions one Lightsail OpenClaw stack.
- Entry point is `app.py`; config comes from `OPENCLAW_CONFIG_PATH` (default `config/dev.json`).
- All infrastructure behavior is in `stacks/lightsail_openclaw_stack.py`.

## Current deployment model (source of truth)
- This repo is blueprint-only (no container/user-data path anymore).
- Use Lightsail blueprint ID `openclaw_ls_1_0` (not `openclaw`, which fails in `us-east-1`).
- Recommended bundle is `medium_3_0`.
- Stack uses a custom resource to `attachStaticIp`/`detachStaticIp`; keep it when editing stack lifecycle behavior.
- Stack also bootstraps a Bedrock IAM role for the Lightsail instance through a custom resource (replaces the manual CloudShell script step).
- Bedrock custom resource handler source is `lambda/bedrock_role_setup/index.py`.

## Commands

### Windows PowerShell
```powershell
# Install deps
uv sync

# Bootstrap (dev/prod)
.\scripts\windows\dev\bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>
.\scripts\windows\prod\bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>

# Synthesize
.\scripts\windows\dev\synth.ps1
.\scripts\windows\prod\synth.ps1

# Diff
.\scripts\windows\dev\diff.ps1
.\scripts\windows\prod\diff.ps1

# Deploy
.\scripts\windows\dev\deploy.ps1
.\scripts\windows\prod\deploy.ps1

# Destroy
.\scripts\windows\dev\destroy.ps1
.\scripts\windows\prod\destroy.ps1
```

### Linux / macOS
```bash
# Install deps
uv sync

# Bootstrap (dev/prod)
./scripts/linux-mac/dev/bootstrap <ACCOUNT_ID> <REGION>
./scripts/linux-mac/prod/bootstrap <ACCOUNT_ID> <REGION>

# Synthesize
./scripts/linux-mac/dev/synth
./scripts/linux-mac/prod/synth

# Diff
./scripts/linux-mac/dev/diff
./scripts/linux-mac/prod/diff

# Deploy
./scripts/linux-mac/dev/deploy
./scripts/linux-mac/prod/deploy

# Destroy
./scripts/linux-mac/dev/destroy
./scripts/linux-mac/prod/destroy
```

### Direct commands (any platform)
```bash
uv run cdk bootstrap aws://<ACCOUNT>/<REGION>
uv run cdk synth
uv run cdk diff
uv run cdk deploy --require-approval never
uv run cdk destroy --force
```

## Config and operational gotchas
- Use Node.js 22 LTS for CDK CLI compatibility (`nvm use` reads `.nvmrc`).
- Keep `config/dev.json` aligned with a real Lightsail key pair name in target account/region.
- Set `AWS_PROFILE` explicitly before deploy/destroy when using non-default credentials.
- Changing `instance_name` replaces the Lightsail instance; static IP name remains whatever `static_ip_name` is set to.
- Auto snapshot add-on is opt-in via `enable_auto_snapshot` (defaults to `false`).
- Bedrock role setup and cleanup are part of the default stack lifecycle (no config flags).
- If a create fails and stack is `ROLLBACK_COMPLETE`, delete the stack before redeploy.

## Fast verification
- Syntax: `python -m compileall app.py stacks`
- Unit tests: `uv run pytest`
- Infra sanity: `uv run cdk synth`
