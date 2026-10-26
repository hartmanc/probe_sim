"""Quality gates for the AI engine families (round two, 26 Oct 2026): the owner's listening notes as tests.

    uv run --python 3.12 --with pytest,numpy,scipy,soundfile,webrtcvad-wheels,onnxruntime python -I -m pytest tools/audio/test_quality.py
    QUALITY_PUBLIC=/path/to/other/public/audio ... (the same gates on another tree: round one's fail them)

Gates (families/quality.py GATES): no speech in any loop; every bin within a pitch ratio of 0.88-1.14 (on) /
0.85-1.18 (off) of the real recording it came from; the lowest bin is a real idle recording and plays the idle within
the same windows; every loop at least 1.0 s and 8 engine cycles; seam correlation not worse than round one (family
median); sprites of a reasonable size. `mazda_kl_v6` and `sohc_i4_loud` are "OK" by the owner's ear (26 Oct 2026)
and are held to the speech gate only (their other gate results are reported in LEDGER.md, not enforced).
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "families"))
import quality as q  # noqa: E402

BASE = json.load(open(os.path.join(HERE, "families", "quality_baseline.json")))
FAMS = q.all_families()
MAX_BYTES = 650_000  # Ogg on + off + engine.json per family


@pytest.fixture(scope="module")
def measured():
    return {f: q.measure(f) for f in FAMS}


def gated(f):
    return f not in q.OWNER_OK


def test_every_family_measured(measured):
    assert len(measured) == 14


@pytest.mark.parametrize("fam", FAMS)
def test_no_speech(measured, fam):
    assert not q.gate_failures(measured[fam])["speech"], fam


@pytest.mark.parametrize("fam", [f for f in FAMS if gated(f)])
def test_pitch_ratio_from_a_real_recording(measured, fam):
    assert not q.gate_failures(measured[fam])["ratio"], fam


@pytest.mark.parametrize("fam", [f for f in FAMS if gated(f)])
def test_idle_bin_is_a_real_idle_recording(measured, fam):
    assert not q.gate_failures(measured[fam])["idle"], fam


@pytest.mark.parametrize("fam", [f for f in FAMS if gated(f)])
def test_loops_long_enough(measured, fam):
    assert not q.gate_failures(measured[fam])["loop"], fam


@pytest.mark.parametrize("fam", [f for f in FAMS if gated(f)])
def test_seam_correlation_not_worse(measured, fam):
    s = q.summary(measured[fam])
    assert s["seam_corr_med"] >= BASE[fam]["seam_corr_med"] - 1e-9, (fam, s["seam_corr_med"], BASE[fam]["seam_corr_med"])


@pytest.mark.parametrize("fam", FAMS)
def test_sprite_size_reasonable(measured, fam):
    assert q.summary(measured[fam])["bytes"] <= MAX_BYTES, fam
