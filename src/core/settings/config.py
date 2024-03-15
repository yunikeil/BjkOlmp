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

