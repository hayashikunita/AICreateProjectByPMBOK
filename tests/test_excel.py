from __future__ import annotations

import os
from pathlib import Path

from pmbok_gpt.excel import create_risk_register_excel, create_stakeholder_register_excel


def test_create_risk_register_excel(tmp_path: Path):
    out = tmp_path / "risk.xlsx"
    path = create_risk_register_excel(str(out))
    assert os.path.exists(path)


def test_create_stakeholder_register_excel(tmp_path: Path):
    out = tmp_path / "stake.xlsx"
    path = create_stakeholder_register_excel(str(out))
    assert os.path.exists(path)
