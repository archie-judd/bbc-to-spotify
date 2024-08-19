from dataclasses import dataclass
from typing import Self

from bbc_to_spotify.authorize.models.external import CredentialsModel


@dataclass(frozen=True)
class Credentials:
    client_id: str
    client_secret: str
    refresh_token: str

    @classmethod
    def from_external(cls, credentials_model: CredentialsModel) -> Self:
        credentials = cls(
            client_id=credentials_model.client_id,
            client_secret=credentials_model.client_secret,
            refresh_token=credentials_model.refresh_token,
        )
        return credentials
