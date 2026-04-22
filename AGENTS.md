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

## Commands (Windows PowerShell)
- Install deps: `python -m uv sync`
- Bootstrap: `python -m uv run cdk.cmd bootstrap aws://<ACCOUNT>/<REGION>`
- Synthesize: `python -m uv run cdk.cmd synth`
- Diff: `python -m uv run cdk.cmd diff`
- Deploy: `python -m uv run cdk.cmd deploy --require-approval never`
- Destroy: `python -m uv run cdk.cmd destroy --force`
- Script wrappers in `scripts/*.ps1` set `OPENCLAW_CONFIG_PATH` automatically (default `config/dev.json`).

## Config and operational gotchas
- Keep `config/dev.json` aligned with a real Lightsail key pair name in target account/region.
- Set `AWS_PROFILE` explicitly before deploy/destroy when using non-default credentials.
- Changing `instance_name` replaces the Lightsail instance; static IP name remains whatever `static_ip_name` is set to.
- If a create fails and stack is `ROLLBACK_COMPLETE`, delete the stack before redeploy.

## Fast verification
- Syntax: `python -m compileall app.py stacks`
- Infra sanity: `python -m uv run cdk.cmd synth`
