# Example Workspace Usage

## Install

```bash
pip install -e .
```

## Configure API Key

```bash
export OPENAI_API_KEY=...
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="..."
```

## Generate App

```bash
umabuild new --workspace example
```

## Run Web Preview

```bash
umabuild run --workspace example
```

## Iterate

```bash
umabuild iterate --workspace example
```

Edit `example/README.md` to change the app spec, then re-run `iterate`.
