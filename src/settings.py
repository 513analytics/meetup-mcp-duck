from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    API_KEY: str = Field(
        default="something_because_its_required",
        env="API_KEY",
        description="API key for the OpenAI API. This is used to authenticate requests.",
    )
    BASE_URL: str = Field(
        default="http://localhost:11434/v1",
        env="BASE_URL",
        description="Base URL for the OpenAI API. This is used to route requests to the correct server.",
    )
    LLM_MODEL: str = Field(
        default="gemma3:27b",
        env="LLM_MODEL",
        description="The model to use for the OpenAI API. This is the specific model version.",
    )


settings = Settings()
