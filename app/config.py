from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

@lru_cache
def get_settings():
    return Settings()

class Settings(BaseSettings):
    database_uri: str
    secret_key: str
    env: str
    jwt_algorithm: str="HS256"
    jwt_access_token_expires:int=30
    app_host: str="0.0.0.0"
    app_port: int=8000
    db_pool_size:int=10
    db_additional_overflow:int=10
    db_pool_timeout:int=10
    db_pool_recycle:int=10
    ascend_rapidapi_key: str | None = None
    ascend_rapidapi_host: str = "edb-with-videos-and-images-by-ascendapi.p.rapidapi.com"
    
    model_config = SettingsConfigDict(env_file=".env")
