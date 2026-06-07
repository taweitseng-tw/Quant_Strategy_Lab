import hashlib
import os
from dataclasses import dataclass
from os import PathLike
import pandas as pd


@dataclass
class DatasetSnapshotResult:
    row_count: int
    columns: list[str]
    filename: str
    sha256_hash: str


def write_dataset_snapshot(
    df: pd.DataFrame,
    output_path: str | PathLike[str],
) -> DatasetSnapshotResult:
    """
    Writes a pandas DataFrame to a deterministic CSV snapshot.

    Requirements:
    - Stable column order (preserves input DataFrame order)
    - index=False
    - Deterministic float formatting
    - Normalize line endings to \n
    - Compute SHA-256 from the exact bytes written

    Returns:
        DatasetSnapshotResult containing metadata and hash.
    """
    csv_str = df.to_csv(
        index=False,
        float_format="%.8f",
        lineterminator="\n"
    )

    # Hash exactly what gets written.
    csv_str = csv_str.replace("\r\n", "\n").replace("\r", "\n")
    csv_bytes = csv_str.encode("utf-8")

    with open(output_path, "wb") as f:
        f.write(csv_bytes)

    sha256_hash = hashlib.sha256(csv_bytes).hexdigest()

    return DatasetSnapshotResult(
        row_count=len(df),
        columns=list(df.columns),
        filename=os.path.basename(os.fspath(output_path)),
        sha256_hash=sha256_hash
    )
