from http import HTTPStatus

from flask_jwt_extended import JWTManager

from app import messages
from app.api.api_extension import api

jwt = JWTManager()


jwt._set_error_handler_callbacks(api)


@jwt.expired_token_loader
def my_expired_token_callback():
    return messages.TOKEN_HAS_EXPIRED, HTTPStatus.UNAUTHORIZED


@jwt.invalid_token_loader
def my_invalid_token_callback(error_message):
    return messages.TOKEN_IS_INVALID, HTTPStatus.UNAUTHORIZED


@jwt.unauthorized_loader
def my_unauthorized_request_callback(error_message):
    return messages.AUTHORISATION_TOKEN_IS_MISSING, HTTPStatus.UNAUTHORIZED
