from loguru import logger
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    manticore_url: str = Field("http://127.0.0.1:9308", env='MANTICORE_URL')

    manticore_tables: List[str] = Field(
        ...,
        env='MANTICORE_TABLES'
    )

    manticore_default_table: str = Field(
        ...,
        env='MANTICORE_DEFAULT_TABLE'
    )

    manticore_max_matches: int = Field(
        10000,
        env='MANTICORE_MAX_MATCHES'
    )

    manticore_matches_default: int = Field(
        100,
        env='MANTICORE_MATCHES_DEFAULT'
    )

    file_upload_max_size: int = Field(
        1 * 1024 * 1024,
        env='FILE_UPLOAD_MAX_SIZE'
    )

    file_upload_limit_lines: int = Field(
        10_000,
        env='FILE_UPLOAD_LIMIT_LINES'
    )

    limit_records_on_page: int = Field(
        500,
        env='LIMIT_RECORDS_ON_PAGE'
    )

    limit_unloading: int = Field(
        1_000_000,
        env='LIMIT_UNLOADING'
    )

    highlight_start: str = Field(
        '<span class="highlight">',
        env='HIGHLIGHT_START'
    )

    highlight_end: str = Field(
        '</span>',
        env='HIGHLIGHT_END'
    )

    unloading_data_dir: str = Field(
        ...,
        env='UNLOADING_DATA_DIR'
    )

    ttl_long_unloading_task: int = Field(
        60 * 60 * 24,
        env='TTL_UNLOADING_TASK'
    )

    ttl_unloading_task: int = Field(
        60 * 60 * 1,
        env='TTL_UNLOADING_TASK'
    )

    redis_host: str = Field(
        'localhost',
        env='REDIS_HOST'
    )

    redis_port: int = Field(
        6379,
        env='REDIS_PORT'
    )

    redis_db: int = Field(
        0,
        env='REDIS_DB'
    )

    cleaning_start: bool = Field(
        True,
        env='CLEANING_START'
    )

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
logger.info(settings)
