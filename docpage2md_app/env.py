from .secrets import get_secret_value, set_user_env_value


def get_dashscope_api_key():
    return get_env_value("DASHSCOPE_API_KEY")


def get_deepseek_api_key():
    return get_env_value("DEEPSEEK_API_KEY")


def get_env_value(name):
    return get_secret_value(name)
