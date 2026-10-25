"""Native proof conditions retain distinct SS11 pixels and omit NF duplicates."""

from pathlib import Path
import shutil

import numpy as np
import pytest

import candidate_proof
from test_word_measure import word_fixture_path


def test_candidate_sheet_separates_the_four_conditions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = word_fixture_path(tmp_path)
    shutil.copy2(source, tmp_path / "TalhaMono-Regular.otf")
    shutil.copy2(source, tmp_path / "TalhaMonoNF-Regular.otf")
    monkeypatch.setattr(candidate_proof, "PROOF_LINES", ((15, "iam"),))
    proof = candidate_proof.candidate_sheet(tmp_path, tmp_path)
    assert proof.size == (2520, 445)
    off, on = (np.array(proof.crop((x, 158, x + 550, 210))) for x in (40, 660))
    assert not np.array_equal(off, on)
    assert np.array_equal(off, np.array(proof.crop((1280, 158, 1830, 210))))
    assert np.array_equal(on, np.array(proof.crop((1900, 158, 2450, 210))))
