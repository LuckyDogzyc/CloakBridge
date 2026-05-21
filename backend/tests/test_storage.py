from pathlib import Path

import pytest

from cloakbridge.storage.paths import AppPaths
from cloakbridge.storage.sqlite_store import SQLiteStore
from cloakbridge.storage.vault import MappingVault


def test_app_paths_keep_data_in_local_data_dir(tmp_path: Path):
    paths = AppPaths.from_base(tmp_path)

    assert paths.data_dir == tmp_path
    assert paths.uploads_dir == tmp_path / "uploads"
    assert paths.outputs_dir == tmp_path / "outputs"
    assert paths.vault_dir == tmp_path / "vault"


def test_sqlite_store_initializes_dictionary_table(tmp_path: Path):
    store = SQLiteStore(tmp_path / "cloakbridge.sqlite")
    store.initialize()

    rows = store.connection.execute(
        "select name from sqlite_master where type='table' and name='dictionary_entries'"
    ).fetchall()

    assert rows == [("dictionary_entries",)]


def test_mapping_vault_round_trips_encrypted_token_map(tmp_path: Path):
    vault = MappingVault(tmp_path / "vault")
    vault.save("job-1", {"<PROJECT_001>": "华东三期项目"})

    raw = (tmp_path / "vault" / "job-1.bin").read_bytes()
    assert "华东三期项目".encode("utf-8") not in raw
    assert vault.load("job-1") == {"<PROJECT_001>": "华东三期项目"}


def test_mapping_vault_rejects_path_traversal_job_id(tmp_path: Path):
    vault = MappingVault(tmp_path / "vault")

    with pytest.raises(ValueError, match="Invalid vault job id"):
        vault.save("../escape", {"<PROJECT_001>": "华东三期项目"})

    assert not (tmp_path / "escape.bin").exists()
