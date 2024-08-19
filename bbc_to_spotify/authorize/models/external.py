from typing import Literal

from pydantic import BaseModel


class Environment(BaseModel):
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REFRESH_TOKEN: str


class CredentialsModel(BaseModel):
    client_id: str
    client_secret: str
    refresh_token: str


class GetRefreshTokenResponseBody(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    scope: str
    token_type: str


class GetAuthenticationCodeParams(BaseModel):
    client_id: str
    redirect_uri: str
    scope: str
    response_type: Literal["code"] = "code"


class GetRefreshTokenRequestBody(BaseModel):
    code: str
    client_id: str
    client_secret: str
    redirect_uri: str
    grant_type: Literal["authorization_code"] = "authorization_code"
