"""The ghost builder's optional local driver-label aliases (tools/ghosts/build_ghosts.py docstring; Astra round-4
review of Mid-Ohio): plain and sha256 keys map logger labels onto the repository's labels, unknown labels pass through,
no file means no change. Synthetic labels only."""
import hashlib
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ghosts"))
import build_ghosts as BG  # noqa: E402


def test_plain_and_hashed_keys_map_unknown_pass_through():
    h = "sha256:" + hashlib.sha256("logger label 2".encode("utf-8")).hexdigest()
    al = {"logger label 1": "driver A", h: "driver B"}
    s = pd.Series(["logger label 1", "logger label 2", "Coby", "16d7 pre-stop"])
    assert list(BG.alias_labels(s, al)) == ["driver A", "driver B", "Coby", "16d7 pre-stop"]


def test_no_aliases_is_identity():
    s = pd.Series(["x", "y"])
    assert BG.alias_labels(s, {}) is s


def test_load_aliases_absent_and_present(tmp_path):
    assert BG.load_aliases(str(tmp_path / "none.json")) == ({}, None)
    p = tmp_path / "a.json"
    p.write_text(json.dumps({"aliases": {"sha256:00": "driver C"}, "derived": "note"}))
    assert BG.load_aliases(str(p)) == ({"sha256:00": "driver C"}, str(p))
