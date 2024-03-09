import os

from dotenv import load_dotenv


# Загрузка переменных из .env файла
current_file_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_path = os.path.dirname(os.path.dirname(current_file_path))
env_path = os.path.join(root_path, ".env")

load_dotenv(dotenv_path=env_path, override=True)


DEBUG: str = os.getenv("DEBUG").lower() == "true"

HOST: str = os.getenv("HOST")
PORT: int = int(os.getenv("PORT"))

REDIS_URL: str = os.getenv("REDIS_URL")

# Крайне не советую использовать log уровень с tg
TG_LOG_TOKEN: str
TG_INFO_LOG_CHANNEL: str
TG_ERROR_LOG_CHANNEL: str

