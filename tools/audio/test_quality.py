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


ALIASES = q.aliases()  # a family that plays another family's sprites: measured as its target, skipped itself


@pytest.fixture(scope="module")
def measured():
    return {f: q.measure(f) for f in FAMS if f not in ALIASES}


def gated(f):
    return f not in q.OWNER_OK


# Provisional table (26 Oct 2026): families the owner passed by ear that still fail a gate. Each family + gate pair is a
# strict xfail with its reason (an unexpected pass is reported, so the entry gets removed); nothing else is excused and
# the gates themselves are unchanged. ohv_v6 and vintage_i6 are NOT here until the owner re-listens (round three).
PROVISIONAL: dict = {}


def marks(fam, gate):
    if fam in ALIASES:
        return [pytest.mark.skip(reason=f"{fam} is an alias of {ALIASES[fam]}: the same sprites, gated there")]
    why = PROVISIONAL.get(fam, {}).get(gate)
    return [pytest.mark.xfail(strict=True, reason=why)] if why else []


def params(gate, only_gated=True):
    return [pytest.param(f, marks=marks(f, gate)) for f in FAMS if gated(f) or not only_gated]


def test_every_family_measured(measured):
    assert len(measured) + len(ALIASES) == 14


@pytest.mark.parametrize("fam", params("speech", False))
def test_no_speech(measured, fam):
    assert not q.gate_failures(measured[fam])["speech"], fam


@pytest.mark.parametrize("fam", params("ratio"))
def test_pitch_ratio_from_a_real_recording(measured, fam):
    assert not q.gate_failures(measured[fam])["ratio"], fam


@pytest.mark.parametrize("fam", params("idle"))
def test_idle_bin_is_a_real_idle_recording(measured, fam):
    assert not q.gate_failures(measured[fam])["idle"], fam


@pytest.mark.parametrize("fam", params("loop"))
def test_loops_long_enough(measured, fam):
    assert not q.gate_failures(measured[fam])["loop"], fam


@pytest.mark.parametrize("fam", params("seam"))
def test_seam_correlation_not_worse(measured, fam):
    s = q.summary(measured[fam])
    assert s["seam_corr_med"] >= BASE[fam]["seam_corr_med"] - 1e-9, (fam, s["seam_corr_med"], BASE[fam]["seam_corr_med"])


@pytest.mark.parametrize("fam", params("size", False))
def test_sprite_size_reasonable(measured, fam):
    assert q.summary(measured[fam])["bytes"] <= MAX_BYTES, fam
