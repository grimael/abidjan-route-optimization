"""Test du cycle sauvegarde / rechargement d'instance."""
import sys, pathlib, shutil
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from vrp.instance import Instance
from vrp.data.load import load_instance, save_instance

TMP = pathlib.Path(__file__).resolve().parent / "_tmp"


def test_roundtrip():
    TMP.mkdir(exist_ok=True)
    inst = Instance.random(n=10, seed=21)
    inst.name = "test_roundtrip"
    inst.source = "unitaire"
    try:
        p = TMP / "i.json"
        save_instance(inst, p)
        back = load_instance(p)
        assert back.n == inst.n
        assert np.allclose(back.matrix, inst.matrix, atol=0.05), "matrices divergentes"
        assert back.meta["points"][0]["name"] == "p0"
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("OK  save/load roundtrip")


if __name__ == "__main__":
    test_roundtrip()
    print("Test data: OK")
