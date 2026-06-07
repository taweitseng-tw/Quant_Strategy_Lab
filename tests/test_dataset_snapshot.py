import hashlib

import pandas as pd
from archive import DatasetSnapshotResult, write_dataset_snapshot

def test_dataset_snapshot_deterministic_hash(tmp_path):
    df = pd.DataFrame({
        "open": [1.1, 2.2, 3.3],
        "close": [1.2, 2.3, 3.4],
        "volume": [100, 200, 300]
    })
    
    file1 = tmp_path / "snap1.csv"
    file2 = tmp_path / "snap2.csv"
    
    res1 = write_dataset_snapshot(df, str(file1))
    res2 = write_dataset_snapshot(df, str(file2))
    
    assert res1.sha256_hash == res2.sha256_hash
    assert res1.row_count == 3
    assert res1.columns == ["open", "close", "volume"]
    assert res1.filename == "snap1.csv"

def test_dataset_snapshot_hash_changes_on_data_change(tmp_path):
    df1 = pd.DataFrame({
        "open": [1.1, 2.2],
        "close": [1.2, 2.3]
    })
    df2 = pd.DataFrame({
        "open": [1.1, 2.20000001],
        "close": [1.2, 2.3]
    })
    
    file1 = tmp_path / "snap1.csv"
    file2 = tmp_path / "snap2.csv"
    
    res1 = write_dataset_snapshot(df1, str(file1))
    res2 = write_dataset_snapshot(df2, str(file2))
    
    assert res1.sha256_hash != res2.sha256_hash

def test_dataset_snapshot_line_endings_are_lf(tmp_path):
    df = pd.DataFrame({
        "A": [1, 2],
        "B": ["foo", "bar"]
    })
    
    out_file = tmp_path / "snap.csv"
    write_dataset_snapshot(df, str(out_file))
    
    with open(out_file, "rb") as f:
        content = f.read()
        
    assert b"\r\n" not in content
    assert b"\n" in content

def test_dataset_snapshot_metadata(tmp_path):
    df = pd.DataFrame({
        "timestamp": ["2026-06-07 10:00", "2026-06-07 10:05"],
        "price": [100.5, 101.2]
    })
    
    out_file = tmp_path / "meta_snap.csv"
    res = write_dataset_snapshot(df, str(out_file))
    
    assert isinstance(res, DatasetSnapshotResult)
    assert res.row_count == 2
    assert res.columns == ["timestamp", "price"]
    assert res.filename == "meta_snap.csv"
    
    # ensure file was written and hash matches
    with open(out_file, "rb") as f:
        file_bytes = f.read()
        expected_hash = hashlib.sha256(file_bytes).hexdigest()
        assert res.sha256_hash == expected_hash


def test_dataset_snapshot_accepts_path_objects(tmp_path):
    df = pd.DataFrame({"open": [1.0]})

    out_file = tmp_path / "path_snap.csv"
    res = write_dataset_snapshot(df, out_file)

    assert out_file.is_file()
    assert res.filename == "path_snap.csv"
