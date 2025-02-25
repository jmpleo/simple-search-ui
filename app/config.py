from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    manticore_url: str = Field("http://127.0.0.1:9308", env='MANTICORE_URL')

    manticore_tables: List[str] = Field(
        default_factory=lambda: ['ulp_raw_1', 'ulp_raw_mpl5_dictk'],
        env='MANTICORE_TABLES'
    )

    manticore_default_table: str = Field(
        'ulp_raw_1',
        env='MANTICORE_DEFAULT_TABLE'
    )

    limit_records_on_page: int = Field(
        500,
        env='LIMIT_RECORDS_ON_PAGE'
    )

    manticore_max_matches: int = Field(
        10000,
        env='MANTICORE_MAX_MATCHES'
    )

    manticore_matches_default: int = Field(
        100,
        env='MANTICORE_MATCHES_DEFAULT'
    )

    limit_unloading: int = Field(
        500000,
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
        "/var/lib/ulp-ui/unload",
        env='UNLOADING_DATA_DIR'
    )

    ttl_unloading_task: int = Field(
        60 * 60 * 24,
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

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
