#!/usr/bin/env python3
"""Entry program: The Passport Page of a Country That Isn't There.

Writes one 1024x1024 PNG of an invented passport spread for the
Republic of Veskar to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
Deterministic: two runs write identical bytes. No network, stdlib + PIL.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.render import render  # noqa: E402


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = render()
    path = os.path.join(out_dir, "entry.png")
    img.save(path, format="PNG")
    print(f"wrote {path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
