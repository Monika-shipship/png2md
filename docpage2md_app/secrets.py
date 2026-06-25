from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path
from typing import Literal


SecretStore = Literal["env", "local", "credential"]
LOCAL_SECRETS_FILE = ".env.local.json"
CREDENTIAL_TARGET_PREFIX = "docpage2md:"


def get_secret_value(name: str, *, repo_root: str | Path | None = None) -> str | None:
    env_value = os.getenv(name)
    if env_value:
        return env_value
    local_value = get_local_secret(name, repo_root=repo_root)
    if local_value:
        return local_value
    user_value = _get_windows_user_env(name)
    if user_value:
        return user_value
    return get_windows_credential(name)


def set_secret_value(name: str, value: str, *, store: SecretStore = "env", repo_root: str | Path | None = None) -> bool:
    if store == "env":
        return set_user_env_value(name, value)
    if store == "local":
        set_local_secret(name, value, repo_root=repo_root)
        os.environ[name] = value
        return True
    if store == "credential":
        ok = set_windows_credential(name, value)
        if ok:
            os.environ[name] = value
        return ok
    raise ValueError(f"Unknown secret store: {store}")


def check_secret_exists(name: str, *, repo_root: str | Path | None = None) -> tuple[bool, str]:
    if os.getenv(name):
        return True, "进程环境变量"
    if get_local_secret(name, repo_root=repo_root):
        return True, "本地 .env.local.json"
    if _get_windows_user_env(name):
        return True, "Windows 用户环境变量"
    if get_windows_credential(name):
        return True, "Windows Credential Manager"
    return False, "未找到"


def local_secrets_path(repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root) / LOCAL_SECRETS_FILE
    return Path(__file__).resolve().parent.parent / LOCAL_SECRETS_FILE


def load_local_secrets(*, repo_root: str | Path | None = None) -> dict[str, str]:
    path = local_secrets_path(repo_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict) and isinstance(data.get("secrets"), dict):
        data = data["secrets"]
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str)}


def get_local_secret(name: str, *, repo_root: str | Path | None = None) -> str | None:
    return load_local_secrets(repo_root=repo_root).get(name) or None


def set_local_secret(name: str, value: str, *, repo_root: str | Path | None = None) -> Path:
    path = local_secrets_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_local_secrets(repo_root=repo_root)
    data[name] = value
    path.write_text(json.dumps({"secrets": data}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def set_user_env_value(name: str, value: str) -> bool:
    os.environ[name] = value
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as env_key:
                winreg.SetValueEx(env_key, name, 0, winreg.REG_SZ, value)
            return True
        except OSError:
            return False
    return False


def _get_windows_user_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env_key:
            value, _ = winreg.QueryValueEx(env_key, name)
            return value or None
    except OSError:
        return None


def get_windows_credential(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        cred_ptr = ctypes.c_void_p()
        if not ctypes.windll.advapi32.CredReadW(_credential_target(name), 1, 0, ctypes.byref(cred_ptr)):
            return None
        credential = ctypes.cast(cred_ptr, ctypes.POINTER(_CREDENTIALW)).contents
        if not credential.CredentialBlob or credential.CredentialBlobSize == 0:
            return None
        raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        return raw.decode("utf-16-le", errors="ignore") or None
    except Exception:
        return None
    finally:
        try:
            if cred_ptr:
                ctypes.windll.advapi32.CredFree(cred_ptr)
        except Exception:
            pass


def set_windows_credential(name: str, value: str) -> bool:
    if os.name != "nt":
        return False
    try:
        blob = value.encode("utf-16-le")
        credential = _CREDENTIALW()
        credential.Type = 1
        credential.TargetName = _credential_target(name)
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = ctypes.cast(ctypes.create_string_buffer(blob), ctypes.c_void_p)
        credential.Persist = 2
        credential.UserName = name
        return bool(ctypes.windll.advapi32.CredWriteW(ctypes.byref(credential), 0))
    except Exception:
        return False


def _credential_target(name: str) -> str:
    return f"{CREDENTIAL_TARGET_PREFIX}{name}"


class _CREDENTIAL_ATTRIBUTEW(ctypes.Structure):
    _fields_ = [
        ("Keyword", wintypes.LPWSTR),
        ("Flags", wintypes.DWORD),
        ("ValueSize", wintypes.DWORD),
        ("Value", ctypes.c_void_p),
    ]


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(_CREDENTIAL_ATTRIBUTEW)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]
