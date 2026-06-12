import os


def get_dashscope_api_key():
    return get_env_value("DASHSCOPE_API_KEY")


def get_deepseek_api_key():
    return get_env_value("DEEPSEEK_API_KEY")


def get_env_value(name):
    if os.name == "nt":
        user_key = _get_windows_user_env(name)
        if user_key:
            return user_key

    return os.getenv(name)


def set_user_env_value(name, value):
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


def _get_windows_user_env(name):
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env_key:
            value, _ = winreg.QueryValueEx(env_key, name)
            return value or None
    except OSError:
        return None
