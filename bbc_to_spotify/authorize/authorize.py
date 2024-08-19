import logging
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from pydantic import ValidationError

from bbc_to_spotify.authorize.models.external import (
    CredentialsModel,
    Environment,
    GetAuthenticationCodeParams,
    GetRefreshTokenRequestBody,
    GetRefreshTokenResponseBody,
)
from bbc_to_spotify.authorize.models.internal import Credentials

SCOPE = "playlist-modify-public playlist-modify-private"
ACCOUNTS_BASE_URL = "https://accounts.spotify.com"
REDIRECT_URI = "http://localhost:8080/bbc-to-spotify"
CREDENTIALS_PATH = Path(os.path.expanduser("~"), ".bbc-to-spotify", "credentials.json")


class ParseCredentialsError(Exception):
    pass


def write_credentials_file(path: Path | str, credentials: Credentials):

    credentialsWire = CredentialsWire(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        refresh_token=credentials.refresh_token,
    )
    with open(path, "w") as file:
        file.write(credentialsWire.model_dump_json())


def maybe_read_credentials_file(path: Path | str) -> Credentials | None:

    try:
        with open(path, "r") as file:
            try:
                credentials_model = CredentialsModel.model_validate_json(file.read())
                credentials = Credentials.from_external(credentials_model)
            except Exception as e:
                logging.error("Error parsing credentials file.")
                raise ParseCredentialsError(
                    f"Could not parse credentials file at {str(path)}. Exception: {e}"
                )
    except FileNotFoundError as e:
        logging.debug("No credentials file found.")
        credentials = None

    return credentials


def maybe_get_credentials() -> Credentials | None:

    logging.info("Getting credentials.")

    credentials = None
    try:
        environment = Environment.model_validate(os.environ)
        credentials = Credentials(
            client_id=environment.SPOTIFY_CLIENT_ID,
            client_secret=environment.SPOTIFY_CLIENT_SECRET,
            refresh_token=environment.SPOTIFY_REFRESH_TOKEN,
        )
        logging.info("Successfully read credentials from environment variables.")
    except ValidationError:
        logging.debug(
            "Environment variable credentials not found. Checking for credentials file."
        )
        credentials = maybe_read_credentials_file(CREDENTIALS_PATH)
        if credentials is None:
            logging.debug("Credentials file not found.")
        else:
            logging.info("Successfully read credentials from credentials file.")

    return credentials


def yes_no_prompt(prompt: str, default: str = "Y") -> bool:
    valid = {"yes": True, "y": True, "no": False, "n": False}
    default = default.lower()

    if default == "y":
        prompt = f"{prompt} [Y/n]: "
    elif default == "n":
        prompt = f"{prompt} [y/N]: "
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    while True:
        choice = input(prompt).strip().lower()

        if choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'y' or 'n' (or just press Enter for default).")


def get_authorization_code(client_id: str, scope: str, redirect_uri: str) -> str:
    url_ext = "authorize?"
    url = urljoin(base=ACCOUNTS_BASE_URL, url=url_ext)

    params = GetAuthenticationCodeParams(
        client_id=client_id, redirect_uri=redirect_uri, scope=scope
    ).model_dump()

    response = requests.get(url=url, params=params, timeout=30)

    response.raise_for_status()

    authorization_code = input(
        f"\nOpen this URL in your browser: \n\n{response.url}\n\nYou will be asked to"
        " sign in if not already, and then redirected to a URL of format: "
        f"{redirect_uri}?code=<authorization-code>\n\nCopy your authorization code and"
        " enter it here: "
    )

    return authorization_code


def get_refresh_token(
    authorization_code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> str:
    url_ext = "api/token"
    url = urljoin(base=ACCOUNTS_BASE_URL, url=url_ext)
    body = GetRefreshTokenRequestBody(
        code=authorization_code,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    ).model_dump()

    response = requests.post(url=url, data=body, timeout=30)

    response.raise_for_status()

    refresh_token = GetRefreshTokenResponseBody.model_validate(
        response.json()
    ).refresh_token

    print(f"\nAuthorization successful!\n\nHere is your refresh token: {refresh_token}")

    return refresh_token


def maybe_write_credentials(credentials: Credentials):

    write_to_file = yes_no_prompt(
        f"\nStore your credentials (client ID, client secret, refresh token) in your"
        f" home folder to enable automatic authentication in future (you must provide"
        f" credentials via environment variable otherwise)?"
    )

    if write_to_file:
        os.makedirs(CREDENTIALS_PATH.parent, exist_ok=True)

        write_credentials_file(path=CREDENTIALS_PATH, credentials=credentials)
        print(
            "\nCredentials successfully written credentials here:"
            f" {CREDENTIALS_PATH}.\n\nYou can now use the 'create-playlist' and "
            "'update-playlist' commands"
        )
    else:
        print(
            "\nCredentials not stored. To use the 'create-playlist' or "
            "'update-playlist' commands please set the following environment "
            "variables before use: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, "
            "SPOTIFY_REFRESH_TOKEN."
        )


def authorize(redirect_uri: str = REDIRECT_URI) -> Credentials:

    credentials = maybe_get_credentials()

    if credentials is not None:
        re_auth = yes_no_prompt("Credentials found, are you sure want to re-authorize?")
        if not re_auth:
            return credentials

    client_id = input(
        "\nBeginning authorization flow.\n\nPlease provide your Spotify client ID and"
        " secret. If you don't have these credentials, you can get them by creating a"
        " web app here:\n"
        "https://developer.spotify.com/documentation/web-api/concepts/apps\n\n"
        "Permission will be asked before storing any credentials.\n\nEnter your client "
        "ID: "
    )
    client_secret = input("Enter your client secret: ")

    authorization_code = get_authorization_code(
        client_id=client_id,
        scope=SCOPE,
        redirect_uri=redirect_uri,
    )

    refresh_token = get_refresh_token(
        authorization_code=authorization_code,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    credentials = Credentials(
        client_id=client_id, client_secret=client_secret, refresh_token=refresh_token
    )

    maybe_write_credentials(credentials=credentials)

    return credentials
