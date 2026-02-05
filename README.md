# umabuild

A Python CLI that generates and previews Expo (React Native) apps on the web from a workspace README spec.

## Quick Start

1. Create a workspace folder and add a spec:

```bash
mkdir -p /path/to/workspace
cat > /path/to/workspace/README.md <<'EOF'
# My App

## Screens
- Home
- Profile

## Features
- Simple greeting
- Basic navigation (if needed)
EOF
```

2. Generate the app:

```bash
umabuild new --workspace /path/to/workspace
```

3. Iterate on changes (edit the workspace README first):

```bash
umabuild iterate --workspace /path/to/workspace
```

4. Run Expo web preview:

```bash
umabuild run --workspace /path/to/workspace
```

## Example Workspace

An example workspace is included at `example/`.

```bash
poetry install
poetry run umabuild doctor
export OPENAI_API_KEY=...
poetry run umabuild new --workspace example
poetry run umabuild run --workspace example
```

Using pip:

```bash
pip install -e .
export OPENAI_API_KEY=...
umabuild new --workspace example
umabuild run --workspace example
```

See `example/USAGE.md` for full instructions.

## Environment Variables

- `OPENAI_API_KEY` (required)
- `OPENAI_BASE_URL` (optional, default is official OpenAI-compatible endpoint)

## Commands

- `umabuild new --workspace <path> [--provider openai] [--model <name>] [--project-dir app] [--no-install]`
- `umabuild iterate --workspace <path> [--provider openai] [--model <name>] [--project-dir app]`
- `umabuild run --workspace <path> [--project-dir app] [--port <port>]`
- `umabuild doctor`

## Workspace Layout

- `<workspace>/README.md`: app spec (required)
- `<workspace>/app/`: generated Expo app (default)
- `<workspace>/.umabuild/`:
  - `spec_snapshot.md`
  - `managed.json`
  - `generation_log.jsonl`

## Safety Notes

- API keys are never printed or written to disk.
- Generation logs redact common secrets.
- If your README contains secrets, you will be warned.
