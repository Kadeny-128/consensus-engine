from __future__ import annotations

import base64
import io

from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')

from rdkit import Chem
from rdkit.Chem import Descriptors, Draw, QED


def analyze_smiles(smiles: str) -> dict | None:
    """Validate a SMILES string and return physics-graded properties, or None if invalid."""
    try:
        mol = Chem.MolFromSmiles(smiles)
    except Exception:
        return None
    if mol is None:
        return None

    try:
        Chem.SanitizeMol(mol)
    except Exception:
        return None

    canonical = Chem.MolToSmiles(mol)
    mw = round(Descriptors.MolWt(mol), 2)
    logp = round(Descriptors.MolLogP(mol), 2)
    tpsa = round(Descriptors.TPSA(mol), 2)
    qed = round(QED.qed(mol), 2)

    score = 0
    if mw < 500:
        score += 10
    if logp < 5:
        score += 10
    if tpsa < 140:
        score += 10
    if qed > 0.5:
        score += 10
    if qed > 0.7:
        score += 10

    # Generate image and return as base64 string (safe for session state + HTML)
    pil_img = Draw.MolToImage(mol, size=(400, 400))
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "valid": True,
        "smiles": canonical,
        "mw": mw,
        "logp": logp,
        "tpsa": tpsa,
        "qed": qed,
        "hard_score": score,
        "image_b64": img_b64,
    }
