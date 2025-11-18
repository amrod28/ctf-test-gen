#!/usr/bin/env python3
import os
import random
import string
import subprocess
import tempfile
import shutil
import json
from pathlib import Path

# Config
BASE = Path.cwd()
TEMPLATES_DIR = BASE / "templates"
OUT_BASE = BASE / "out"
NUM = 4  # how many binaries to produce

# Default compile flags if template metadata doesn't provide them
DEFAULT_CFLAGS_CHOICES = [
    "-O0 -g",
    "-O2",
    "-Os",
    "-O3",
    "-O1 -s"
]

# Default Dockerfile content (script writes this into the temp build context)
DOCKERFILE = r'''
# syntax=docker/dockerfile:1
FROM alpine AS build
RUN apk add --no-cache gcc musl-dev
WORKDIR /src
COPY program.c .
ARG CFLAGS
RUN gcc $CFLAGS -static -o /bin/challenge program.c
FROM scratch
COPY --from=build /bin/challenge /challenge
ENTRYPOINT ["/challenge"]
'''

def list_templates():
    if not TEMPLATES_DIR.exists():
        raise SystemExit(f"Templates directory not found: {TEMPLATES_DIR}")
    # collect files with .c extension (or any extension if you prefer)
    templates = sorted([p for p in TEMPLATES_DIR.iterdir() if p.is_file() and p.suffix in ['.c', '.txt']])
    return templates

def load_metadata(template_path: Path):
    meta_path = template_path.with_suffix(".json")
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            print("[!] Failed to read metadata", meta_path, e)
    return {}

def gen_flag():
    return "flag{" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=12)) + "}"

def xor_encode_bytes(s: str):
    key = random.randint(1, 255)
    enc_bytes = bytes([b ^ key for b in s.encode('utf-8')])
    # represent as C escaped string: "\xab\xcd..."
    esc = ''.join('\\x{:02x}'.format(b) for b in enc_bytes)
    return esc, key

def prepare_program_from_template(template_text: str, flag: str):
    # Replace {FLAG}
    program = template_text.replace("{FLAG}", flag)

    # XOR encoding support: if template uses {XOR_ENC} and {KEY}
    if "{XOR_ENC}" in program:
        enc, key = xor_encode_bytes(flag)
        program = program.replace("{XOR_ENC}", enc)
        program = program.replace("{KEY}", str(key))

    # Random integer placeholder
    if "{RANDOM_INT}" in program:
        ri = str(random.randint(1, 10_000))
        program = program.replace("{RANDOM_INT}", ri)

    return program

def build_one(template_path: Path, idx: int):
    meta = load_metadata(template_path)
    cflags_choices = meta.get("cflags", DEFAULT_CFLAGS_CHOICES)
    pad_max = meta.get("pad_max", meta.get("pad", 1024))  # bytes
    difficulty = meta.get("difficulty", "unknown")

    out_dir = OUT_BASE / f"{template_path.stem}_{idx}"
    out_dir.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix=f"ctx_{template_path.stem}_{idx}_"))
    try:
        # read template
        tpl_text = template_path.read_text(encoding="utf-8")
        flag = gen_flag()
        program_c = prepare_program_from_template(tpl_text, flag)

        # write program.c and Dockerfile
        (tmp / "program.c").write_text(program_c, encoding="utf-8")
        (tmp / "Dockerfile").write_text(DOCKERFILE.strip() + "\n", encoding="utf-8")

        # select cflags
        cflags = random.choice(cflags_choices)

        # build with docker
        cmd = ["docker", "build", "--build-arg", f"CFLAGS={cflags}", "--output", str(out_dir.resolve()), str(tmp.resolve())]
        print(f"[*] Building {out_dir.name} from template {template_path.name} (cflags: {cflags}, difficulty: {difficulty})")
        subprocess.run(cmd, check=True)

        # optional padding for uniqueness
        bin_path = out_dir / "challenge"
        pad_len = 0
        if bin_path.exists() and pad_max and pad_max > 0:
            pad_len = random.randint(0, pad_max)
            if pad_len:
                with open(bin_path, "ab") as f:
                    f.write(os.urandom(pad_len))

        # write metadata next to binary for grader use
        meta_out = {
            "template": template_path.name,
            "flag": flag,
            "cflags": cflags,
            "pad": pad_len,
            "difficulty": difficulty
        }
        (out_dir / "meta.json").write_text(json.dumps(meta_out, indent=2), encoding="utf-8")

        print(f"[+] Built {out_dir}/challenge (flag: {flag}, pad: {pad_len} bytes)")
        return meta_out

    finally:
        try:
            shutil.rmtree(tmp)
        except Exception as e:
            print("[!] Warning: could not remove tmp dir", tmp, e)

if __name__ == "__main__":
    OUT_BASE.mkdir(exist_ok=True)
    templates = list_templates()
    if not templates:
        raise SystemExit("No templates found in templates/")

    results = []
    # choose a template randomly for each output, or iterate templates cyclically
    for i in range(NUM):
        tpl = random.choice(templates)
        try:
            r = build_one(tpl, i)
            if r: results.append(r)
        except subprocess.CalledProcessError as e:
            print("[!] Docker build failed for template", tpl.name, e)

    print("\nSummary:")
    for r in results:
        print(r)


