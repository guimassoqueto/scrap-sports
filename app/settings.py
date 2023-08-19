from dotenv import load_dotenv
from os import getenv

load_dotenv()


POSTGRES_PORT = getenv("POSTGRES_PORT") or 5432
POSTGRES_DB = getenv("POSTGRES_DB") or "postgres"
POSTGRES_USER = getenv("POSTGRES_USER") or "postgres"
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD") or "password"
POSTGRES_HOST = getenv("POSTGRES_HOST") or "127.0.0.1"
NIKE_OFFERS_API = getenv("NIKE_OFFERS_API") or "none"
ADIDAS_OFFERS_API = getenv("ADIDAS_OFFERS_API") or "none"
MAX_CONCURRENCY = int(getenv("MAX_CONCURRENCY") or 8) 