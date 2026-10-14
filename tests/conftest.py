import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def write_session(dirpath, sid, lines):
    p = pathlib.Path(dirpath) / f"{sid}.jsonl"
    with p.open("w") as fh:
        for line in lines:
            fh.write(line if isinstance(line, str) else json.dumps(line))
            fh.write("\n")
    return p


def user(text, ts, **extra):
    return {"type": "user", "timestamp": ts, "cwd": "/home/u/code/app", "gitBranch": "main",
            "message": {"role": "user", "content": text}, **extra}


def assistant(text, ts):
    return {"type": "assistant", "timestamp": ts,
            "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


@pytest.fixture
def projects(tmp_path):
    root = tmp_path / "projects" / "-home-u-code-app"
    root.mkdir(parents=True)
    return root
