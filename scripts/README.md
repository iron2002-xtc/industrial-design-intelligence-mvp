# Data Scripts

This folder contains the local data pipeline for the MVP.

## Generate mock data

Mac:

```bash
python3 scripts/generate_mock_data.py
```

Windows:

```powershell
py -3 scripts/generate_mock_data.py
```

The script writes the same files to both `data/` and `public/data/`.

- `data/` is the canonical project data folder for future automation and commits.
- `public/data/` is the static copy served by Vite and Vercel at `/data/...`.

## Validate data

Mac:

```bash
python3 scripts/validate_data.py
```

Windows:

```powershell
py -3 scripts/validate_data.py
```

The validator checks JSON syntax, required report fields, latest/index consistency, and count consistency.
