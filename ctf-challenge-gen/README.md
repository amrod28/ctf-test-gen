## CTF Challenge Generator — README

This repository stores CTF challenge metadata and artifacts in a simple CSV + artifacts layout so challenges can be generated, listed, and reused programmatically.

High-level idea
- Challenges are described in `records/challenges.csv`.
- Challenge files and supporting data live in `artifacts/` (and `templates/` if templates are used).
- A generator script (for example `generator.py`) can load `records/challenges.csv` and produce challenge packages or tests.

Repository layout
- `generator.py` — (optional) generator script that uses the CSV and artifacts.
- `requirements.txt` — python dependencies, if any.
- `artifacts/` — challenge artifacts (binaries, data files, shadow files, etc.).
- `records/challenges.csv` — the canonical challenge registry (CSV table).
- `templates/` — optional challenge templates.

CSV schema
The current `records/challenges.csv` header is:

`id,name,path_in_repo,type,description,template_present,template_path,flag_present,flag_location,exposed_ports,challenge_dependencies,artifacts_needed,prereqs,exploit_vector,runtime_requirements,hints`

Column meanings (short):
- id — integer unique ID for the challenge.
- name — user-friendly name.
- path_in_repo — relative path to the primary artifact or folder (e.g. `artifacts/shadow`).
- type —  classification (e.g. `rev`, `pwn`, `password file`, `web`).
- description —  human-readable description.
- template_present — `true|false` whether a template exists for automated generation.
- template_path — path to template if present.
- flag_present — `true|false` whether a flag is embedded in the artifact.
- flag_location — where the flag is stored (informational).
- exposed_ports — ports required for networked challenges (semicolon-separated or empty).
- challenge_dependencies — other challenge IDs or named dependencies.
- artifacts_needed — list of artifact paths needed (Semicolon-separated).
- prereqs — prerequisites for players (skills, tools).
- exploit_vector — short phrase on the expected exploit or technique.
- runtime_requirements — services or runtime to run the challenge.
- hints — optional hint text.

Example CSV row (one line):

`3,shadow-simple-carol,artifacts/shadow,password file,Find carol's password in the provided shadow file,false,,false,,, ,artifacts/shadow,,password disclosure,,Try reading the file; passwords are weak`

How to add a challenge (recommended)
1. Add the artifact(s) to `artifacts/` (e.g. `artifacts/my-challenge/`, `artifacts/shadow`).
2. Add a single descriptive row to `records/challenges.csv`. Use an incremented `id` and set `artifacts_needed`/`path_in_repo` to point to the artifact location.
3. If you use templates, place them in `templates/` and set `template_present` and `template_path`.




