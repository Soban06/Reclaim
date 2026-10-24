"""Read checksum-pinned ASOS pandas tables with an explicit pickle allowlist."""
import hashlib
import pickle
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASHES = {
    "event_table_training.p": "6d61ce2fc645e6720aed243d45174bfc7fc139dbed70b9306798c648c6a7fed6",
    "product_nodes_training.p": "eb731fc46ba6712fb986971d0af235822ebc2317e38877f5627ee6b6f2f8d9e0",
    "customer_nodes_training.p": "8517d56a4a27d38be28f2b0b5fb0d5281c1c74246ebc666e2bad49e8efccfcae",
}
ALLOWED = {
    ("pandas.core.frame", "DataFrame"),
    ("pandas.core.internals.managers", "BlockManager"),
    ("pandas._libs.internals", "_unpickle_block"),
    ("numpy.core.multiarray", "_reconstruct"), ("numpy", "ndarray"),
    ("numpy", "dtype"), ("builtins", "slice"),
    ("pandas.core.indexes.base", "_new_Index"),
    ("pandas.core.indexes.base", "Index"),
    ("pandas.core.indexes.range", "RangeIndex"),
    ("pandas.core.indexes.numeric", "Int64Index"),
}


class TableUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) not in ALLOWED:
            raise pickle.UnpicklingError(f"Unsupported source object: {module}.{name}")
        if module == "pandas.core.indexes.numeric":
            from pandas import Index
            return Index
        return super().find_class(module, name)


def read_source(name):
    path = ROOT / "data" / "raw" / name
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    if hasher.hexdigest() != HASHES[name]:
        raise ValueError(f"Source checksum mismatch: {name}")
    with path.open("rb") as stream:
        return TableUnpickler(stream).load()
