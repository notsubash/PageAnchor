from pathlib import Path

import lancedb


def test_lancedb_connects_to_local_dir(tmp_path: Path):
    db = lancedb.connect(tmp_path / "lancedb")
    assert db.list_tables().tables == []
