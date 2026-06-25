import docpage2md_app.secrets as secrets
from docpage2md_app.secrets import check_secret_exists, get_secret_value, local_secrets_path, set_local_secret, set_secret_value


def test_local_secrets_roundtrip_uses_ignored_filename(tmp_path, monkeypatch):
    monkeypatch.delenv("DOCPAGE2MD_TEST_SECRET", raising=False)

    path = set_local_secret("DOCPAGE2MD_TEST_SECRET", "local-secret", repo_root=tmp_path)

    assert path == tmp_path / ".env.local.json"
    assert local_secrets_path(tmp_path).name == ".env.local.json"
    assert get_secret_value("DOCPAGE2MD_TEST_SECRET", repo_root=tmp_path) == "local-secret"


def test_process_env_wins_over_local_secret(tmp_path, monkeypatch):
    set_local_secret("DOCPAGE2MD_TEST_PRIORITY", "local-secret", repo_root=tmp_path)
    monkeypatch.setenv("DOCPAGE2MD_TEST_PRIORITY", "env-secret")

    assert get_secret_value("DOCPAGE2MD_TEST_PRIORITY", repo_root=tmp_path) == "env-secret"


def test_local_secret_wins_over_windows_user_env_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("DOCPAGE2MD_TEST_LOCAL_PRIORITY", raising=False)
    monkeypatch.setattr(secrets, "_get_windows_user_env", lambda _name: "windows-user-secret")
    set_local_secret("DOCPAGE2MD_TEST_LOCAL_PRIORITY", "local-secret", repo_root=tmp_path)

    assert get_secret_value("DOCPAGE2MD_TEST_LOCAL_PRIORITY", repo_root=tmp_path) == "local-secret"


def test_set_secret_value_local_reports_checkable_location(tmp_path, monkeypatch):
    monkeypatch.delenv("DOCPAGE2MD_TEST_CHECK", raising=False)

    assert set_secret_value("DOCPAGE2MD_TEST_CHECK", "secret-value", store="local", repo_root=tmp_path) is True
    ok, where = check_secret_exists("DOCPAGE2MD_TEST_CHECK", repo_root=tmp_path)

    assert ok is True
    assert where in {"进程环境变量", "本地 .env.local.json"}
