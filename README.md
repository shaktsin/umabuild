# umabuild

Build Expo apps from a single README. Fast, repeatable, and web‑previewable.

`umabuild` is a Python CLI that turns a workspace README into a runnable Expo (React Native) app, then launches the web preview.

---

## Why umabuild?

- **Spec-driven**: Your app spec lives in `README.md` inside a workspace.
- **Repeatable**: Managed files are regenerated on demand.
- **Web-first preview**: Start `expo start --web` with one command.
- **Real LLM**: Uses OpenAI‑compatible chat completions API.

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

## How It Works

- You write an app spec in `<workspace>/README.md`.
- `umabuild new` bootstraps an Expo app and generates managed files.
- `umabuild iterate` regenerates only managed files.
- `umabuild run` starts Expo web preview.

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

## Troubleshooting

- **Expo web missing deps**: run `npx expo install react-dom react-native-web`.
- **TypeScript missing deps**: run `npx expo install typescript @types/react`.
- **AsyncStorage missing**: run `npx expo install @react-native-async-storage/async-storage`.

## License

See `LICENSE`.
