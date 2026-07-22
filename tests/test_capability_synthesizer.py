"""
Tests unitaires enrichis pour CapabilitySynthesizer (Level 8.0 Auto-Évolution Collective).
"""

import os
import pytest
from orchestrator.agents.capability_synthesizer import CapabilitySynthesizer


@pytest.fixture
def temp_cap_dir(tmp_path):
    cdir = tmp_path / "synthetic_capabilities"
    return str(cdir)


def test_capability_synthesizer_reuse_and_dynamic_load(temp_cap_dir):
    synth = CapabilitySynthesizer(cap_dir=temp_cap_dir)
    res1 = synth.synthesize_capability("JSON Validator", "Valider un schéma JSON.")
    assert os.path.exists(res1["file_path"])
    assert os.path.exists(res1["test_file_path"])

    res2 = synth.synthesize_capability("JSON Validator", "Valider un schéma JSON.")
    assert res2["status"] == "REUSED"

    mod = synth.load_capability_dynamically("JSON Validator")
    assert mod is not None
    assert hasattr(mod, "execute")
