import os
from datetime import timedelta


def get_mock_email_config() -> bool:
    MOCK_EMAIL = os.getenv("MOCK_EMAIL")

    if MOCK_EMAIL:

        MOCK_EMAIL = MOCK_EMAIL.lower()

        if MOCK_EMAIL == "true":
            return True
        elif MOCK_EMAIL == "false":
            return False
        else:

            raise ValueError(
                "MOCK_EMAIL environment variable is optional if set, it has to be valued as either 'True' or 'False'"
            )
    else:

        return False


class BaseConfig(object):
    """Base configuration."""

    DEBUG = False
    TESTING = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 3600

    DB_TYPE = os.getenv("DB_TYPE")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_ENDPOINT = os.getenv("DB_ENDPOINT")
    DB_NAME = os.getenv("DB_NAME")

    UNVERIFIED_USER_THRESHOLD = 2592000

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=10)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(weeks=4)

    SECRET_KEY = os.getenv("SECRET_KEY", None)

    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")

    BCRYPT_LOG_ROUNDS = 13
    WTF_CSRF_ENABLED = True

    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    MOCK_EMAIL = get_mock_email_config()
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    MAIL_USERNAME = os.getenv("APP_MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("APP_MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    @staticmethod
    def build_db_uri(
        db_type_arg=DB_TYPE,
        db_user_arg=DB_USERNAME,
        db_password_arg=DB_PASSWORD,
        db_endpoint_arg=DB_ENDPOINT,
        db_name_arg=DB_NAME,
    ):
        """Build remote database uri using specific environment variables."""

        return "{db_type}://{db_user}:{db_password}@{db_endpoint}/{db_name}".format(
            db_type=db_type_arg,
            db_user=db_user_arg,
            db_password=db_password_arg,
            db_endpoint=db_endpoint_arg,
            db_name=db_name_arg,
        )


class ProductionConfig(BaseConfig):
    """Production configuration."""

    SQLALCHEMY_DATABASE_URI = BaseConfig.build_db_uri()
    MOCK_EMAIL = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = BaseConfig.build_db_uri()


class StagingConfig(BaseConfig):
    """Staging configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = BaseConfig.build_db_uri()
    MOCK_EMAIL = False


class LocalConfig(BaseConfig):
    """Local configuration."""

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "sqlite:///local_data.db"


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True
    MOCK_EMAIL = True

    SQLALCHEMY_DATABASE_URI = "sqlite://"


def get_env_config() -> str:
    flask_config_name = os.getenv("FLASK_ENVIRONMENT_CONFIG", "dev")
    if flask_config_name not in ["prod", "test", "dev", "local", "stag"]:
        raise ValueError(
            "The environment config value has to be within these values: prod, dev, test, local, stag."
        )
    return CONFIGURATION_MAPPER[flask_config_name]


CONFIGURATION_MAPPER = {
    "dev": "config.DevelopmentConfig",
    "prod": "config.ProductionConfig",
    "stag": "config.StagingConfig",
    "local": "config.LocalConfig",
    "test": "config.TestingConfig",
}
