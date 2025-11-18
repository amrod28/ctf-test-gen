#!/usr/bin/env python3
"""
generate_docker_compose.py

Read a JSON file listing binary filenames and produce a Docker build context
and a `docker-compose.yml` that builds an image containing those binaries.

Assumptions:
- The input JSON is either an array of file paths (strings) or an object mapping
  names to file paths. Paths are resolved relative to the workspace root by
  default.
- All listed files must exist (the script will error if not).

Usage (simple):
  ./generate_docker_compose.py binaries.json

Output:
- ./docker_build/  (contains the binaries and the Dockerfile)
- docker-compose.yml

"""
import argparse
import json
import os
import shutil
from pathlib import Path
import sys


DOCKER_BUILD_DIR = Path("docker_build2")
DOCKERFILE_NAME = "Dockerfile"
COMPOSE_FILENAME = "docker-compose.yml"


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise SystemExit(f"Failed to read JSON {path}: {e}")


def normalize_entries(data):
    """Return list of (name, path) tuples."""
    entries = []
    if isinstance(data, list):
        for p in data:
            if not isinstance(p, str):
                raise SystemExit("JSON list items must be strings (file paths)")
            entries.append((Path(p).name, Path(p)))
    elif isinstance(data, dict):
        # allow mapping name -> path
        for k, v in data.items():
            if not isinstance(v, str):
                raise SystemExit("JSON object values must be strings (file paths)")
            entries.append((k, Path(v)))
    else:
        raise SystemExit("JSON must be an array (list of paths) or an object mapping names to paths")
    return entries


def prepare_build_context(entries, workspace_root: Path, out_dir: Path):
    # clear out_dir
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # copy files into out_dir, preserving requested name
    for name, relpath in entries:
        src = (workspace_root / relpath).resolve()
        if not src.exists():
            raise SystemExit(f"Source file not found: {src}")
        dest = out_dir / name
        shutil.copy2(src, dest)
        # ensure executable bit for file user
        dest.chmod(dest.stat().st_mode | 0o100)


def write_dockerfile(out_dir: Path, target_dir: str = "/opt/binaries"):
    content = f"""
FROM ubuntu:22.04
WORKDIR {target_dir}
COPY . {target_dir}
RUN chmod +x {target_dir}/* || true
CMD ["/bin/bash"]
""".lstrip()
    (out_dir / DOCKERFILE_NAME).write_text(content, encoding="utf-8")


def write_compose(service_name: str, image_name: str, build_dir: str, compose_path: Path):
    # simple YAML without external deps
    content = f"""
version: '3.8'
services:
  {service_name}:
    build:
      context: {build_dir}
    image: {image_name}
    tty: true
""".lstrip()
    compose_path.write_text(content, encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description="Generate Docker build context + docker-compose.yml from a JSON list of binaries")
    p.add_argument("json", help="Path to JSON file (array of paths or object name->path)")
    p.add_argument("--workspace", help="Workspace root to resolve relative paths (default: current dir)", default=".")
    p.add_argument("--out", help="Output build context directory (default: ./docker_build)", default=str(DOCKER_BUILD_DIR))
    p.add_argument("--service", help="Service name to use in docker-compose (default: binaries)", default="binaries")
    p.add_argument("--image", help="Image name to build (default: ctf-binaries:latest)", default="ctf-binaries:latest")
    args = p.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    json_path = (workspace / args.json).resolve() if not Path(args.json).is_absolute() else Path(args.json)
    if not json_path.exists():
        raise SystemExit(f"JSON file not found: {json_path}")

    raw = load_json(json_path)
    entries = normalize_entries(raw)

    out_dir = Path(args.out)
    # prepare build context
    prepare_build_context(entries, workspace, out_dir)

    write_dockerfile(out_dir)
    write_compose(args.service, args.image, str(out_dir), Path(COMPOSE_FILENAME))

    print(f"Wrote build context to: {out_dir.resolve()}")
    print(f"Wrote compose file: {Path(COMPOSE_FILENAME).resolve()}")
    print("To build: docker-compose build")
    print("To run: docker-compose up --build")


if __name__ == '__main__':
    main()
