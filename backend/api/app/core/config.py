from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBCredentials(BaseModel):
    username: str
    password: str
    host: str
    port: int
    dbname: str


class Settings(BaseSettings):
    documents_bucket_name: str
    redis_endpoint: str
    sqs_queue_url: str
    cognito_user_pool_id: str
    cognito_user_pool_client_id: str
    # Raw value loaded from env/Secrets Manager
    db_credentials: str
    aws_region: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @computed_field
    @property
    def db(self) -> DBCredentials:
        return DBCredentials.model_validate_json(self.db_credentials)


settings = Settings()