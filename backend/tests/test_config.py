from pathlib import Path

from config import BACKEND_DIR, Settings


def test_env_file_can_be_loaded_independent_of_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.delenv("INVESTIGATION_DB_PATH", raising=False)

    env_file = tmp_path / "backend.env"
    env_file.write_text("DEMO_MODE=false\nINVESTIGATION_DB_PATH=from-env.sqlite3\n", encoding="utf-8")

    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    settings = Settings(_env_file=env_file)

    assert settings.DEMO_MODE is False
    assert settings.INVESTIGATION_DB_PATH == str(BACKEND_DIR / "from-env.sqlite3")


def test_relative_db_path_resolves_under_backend_dir(monkeypatch):
    monkeypatch.delenv("INVESTIGATION_DB_PATH", raising=False)

    settings = Settings(_env_file=None, INVESTIGATION_DB_PATH="data/investigations.sqlite3")

    assert settings.INVESTIGATION_DB_PATH == str(BACKEND_DIR / "data" / "investigations.sqlite3")


def test_absolute_db_path_is_preserved(tmp_path, monkeypatch):
    monkeypatch.delenv("INVESTIGATION_DB_PATH", raising=False)

    db_path = tmp_path / "investigations.sqlite3"

    settings = Settings(_env_file=None, INVESTIGATION_DB_PATH=str(db_path))

    assert Path(settings.INVESTIGATION_DB_PATH) == db_path


def test_memory_db_path_is_preserved(monkeypatch):
    monkeypatch.delenv("INVESTIGATION_DB_PATH", raising=False)

    settings = Settings(_env_file=None, INVESTIGATION_DB_PATH=":memory:")

    assert settings.INVESTIGATION_DB_PATH == ":memory:"
