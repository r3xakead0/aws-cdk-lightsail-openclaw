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

## Commands

### Windows PowerShell
```powershell
# Install deps
uv sync

# Bootstrap
.\scripts\windows\bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>

# Synthesize
.\scripts\windows\synth.ps1

# Diff
.\scripts\windows\diff.ps1

# Deploy
.\scripts\windows\deploy.ps1

# Destroy
.\scripts\windows\destroy.ps1
```

### Linux / macOS
```bash
# Install deps
uv sync

# Bootstrap
./scripts/linux-mac/bootstrap <ACCOUNT_ID> <REGION>

# Synthesize
./scripts/linux-mac/synth

# Diff
./scripts/linux-mac/diff

# Deploy
./scripts/linux-mac/deploy

# Destroy
./scripts/linux-mac/destroy
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
- Keep `config/dev.json` aligned with a real Lightsail key pair name in target account/region.
- Set `AWS_PROFILE` explicitly before deploy/destroy when using non-default credentials.
- Changing `instance_name` replaces the Lightsail instance; static IP name remains whatever `static_ip_name` is set to.
- If a create fails and stack is `ROLLBACK_COMPLETE`, delete the stack before redeploy.

## Fast verification
- Syntax: `python -m compileall app.py stacks`
- Infra sanity: `uv run cdk synth`
