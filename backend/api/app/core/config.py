from pydantic import BaseModel, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBCredentials(BaseModel):
    username: str
    password: str
    host: str
    port: int
    dbname: str


class Settings(BaseSettings):
    documents_bucket_name: str
    sqs_queue_url: str
    cognito_user_pool_id: str | None = None
    cognito_user_pool_client_id: str | None = None
    # Raw value loaded from env/Secrets Manager
    db_credentials: str
    aws_region: str = "us-east-1"
    environment: str = "dev"
    migration_db_credentials: str | None = None
    bedrock_guardrail_arn: str | None = None
    bedrock_guardrail_version: str = "DRAFT"
    redis_url: str | None = None
    redis_auth_token: str | None = None
    query_rate_limit_per_minute: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def db(self) -> DBCredentials:
        return DBCredentials.model_validate_json(self.db_credentials)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def migration_db(self) -> DBCredentials:
        if self.migration_db_credentials is None:
            raise ValueError("MIGRATION_DB_CREDENTIALS is not set")
        return DBCredentials.model_validate_json(self.migration_db_credentials)

    @model_validator(mode="after")
    def _require_prod_settings(self) -> Settings:
        if self.environment != "prod":
            return self

        missing = [
            name
            for name, value in (
                ("BEDROCK_GUARDRAIL_ARN", self.bedrock_guardrail_arn),
                ("REDIS_URL", self.redis_url),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required production settings: {', '.join(missing)}")
        return self


settings = Settings()

API_V1_PREFIX = "/v1"
