# BBC to Spotify

Sync your Spotify playlists with BBC radio station playlists.

## What is BBC to Spotify

`bbc-to-spotify` grabs the current playlist for a given BBC radio station, and uses these songs to create or update a Spotify playlist of your choice.

It works for: BBC Radio 1, BBC Radio 1 Xtra, BBC Radio 2, BBC Radio 6 Music, and BBC Asian Network.

## Contents

<!-- vim-markdown-toc GFM -->

* [Requirements](#requirements)
* [Installation](#installation)
    * [Option 1: Using Poetry](#option-1-using-poetry)
    * [Option 2: Using Nix](#option-2-using-nix)
* [Authorize the CLI](#authorize-the-cli)
    * [1. Run the Authorization Command:](#1-run-the-authorization-command)
    * [2. Follow the Prompts:](#2-follow-the-prompts)
    * [3. Complete the Authorization:](#3-complete-the-authorization)
    * [Troubleshooting Authorization:](#troubleshooting-authorization)
* [Usage](#usage)
* [Examples](#examples)
    * [Creating a playlist (with Poetry)](#creating-a-playlist-with-poetry)
    * [Updating a playlist (with Nix)](#updating-a-playlist-with-nix)
* [FAQ](#faq)
    * [1. How can I find a playlist's ID?](#1-how-can-i-find-a-playlists-id)
    * [2. I don't want to store my credentials. Can I still use the CLI?](#2-i-dont-want-to-store-my-credentials-can-i-still-use-the-cli)
    * [3. What permission scopes are provided to the CLI?](#3-what-permission-scopes-are-provided-to-the-cli)

<!-- vim-markdown-toc -->

## Requirements

- **Spotify Account**: A valid Spotify account is required to use this app.
- **Spotify Developer App**: You need to create a Spotify app to generate client credentials that will be required for authorizing the CLI.
  - You can follow [Spotify's instructions](https://developer.spotify.com/documentation/web-api/concepts/apps).
  - It is recommended to use the following redirect URI: `http://localhost:8080/bbc-to-spotify`.
  - Make a note of your client ID and secret, you will need them to authorize the CLI.
- **For a Poetry installation**:
  - Python 3.10+
  - [Poetry](https://python-poetry.org/)
- **For a Nix installation**:
  - [Nix](https://nixos.org/download)
  - Ensure nix-command and flakes are enabled. Instructions here: https://nixos.wiki/wiki/Flakes.

## Installation

### Option 1: Using Poetry

Install directly from the Git URL:

```bash
poetry add git+https://github.com/archie-judd/bbc-to-spotify
```

Or clone the repo and install locally:

```bash
git clone https://github.com/archie-judd/bbc-to-spotify
cd bbc-to-spotify
poetry install
```

Check install was successful by running the following command:

```bash
poetry run bbc-to-spotify --version
```

### Option 2: Using Nix

Enter a temporary nix bash with `bbc-to-spotify` installed:

```bash
nix bash github:archie-judd/bbc-to-spotify
```

Or install imperatively:

```bash
nix profile install github:archie-judd/bbc-to-spotify
```

Or install declaratively with a flake:

- For example: https://nixos-and-flakes.thiscute.world/nixos-with-flakes/nixos-flake-and-module-system#install-system-packages-from-other-flakes.

Check install was successful by running the following command:

```bash
bbc-to-spotify --version
```

## Authorize the CLI

To authorize the app to access Spotify’s API, you need to run the authorize command.

### 1. Run the Authorization Command:

If you installed via **Poetry**, use poetry run to run the authorization command:

`poetry run bbc-to-spotify authorize`

If you installed via **Nix**, simply run:

`bbc-to-spotify authorize`

### 2. Follow the Prompts:

The command will prompt you to log in to enter your client ID and Secret, and then login to your Spotify account (if not already logged in). It will then request authorization to access the necessary Spotify data.

### 3. Complete the Authorization:

Once authenticated, the CLI app will store the necessary credentials (like your Client ID and Client Secret) for future use. These credentials will be automatically used by the app during operation.

If you need to reauthorize, simply run the authorize command again.

### Troubleshooting Authorization:

If you did not use the recommended redirect URI when creating your Spotify App, make sure to add the argument `--redirect-uri <your-redirect-uri>`.

## Usage

Commands take the following format:

- For **Poetry**:
  ```bash
  poetry run bbc-to-spotify <command> [arguments]
  ```
- For **Nix**:
  ```bash
  bbc-to-spotify <command> [arguments]
  ```

The available commands are: `authorize`, `create-playlist` and `update-playlist`.

To find help for a particular command:

```bash
bbc-to-spotify <command> -h
```

## Examples

### Creating a playlist (with Poetry)

The `create-playlist` playlist command is used to create a new Spotify playlist with songs from a BBC radio station's current playlist.

To create a new playlist called "BBC Radio 6 Music" using BBC Radio 6 Music as a source:

```bash
poetry run bbc-to-spotify create-playlist <your-new-playlist-name>  radio-6
```

Possible sources include:
`radio-1`
`radio-1-xtra`
`radio-2`
`radio-6`
`bbc-asian-network`

The playlist ID will be printed when the playlist has been successfully created. Make a note of it, it will be required for updating the playlist.

Run `poetry run bbc-to-spotify create-playlist -h` to show help and options for this command.

### Updating a playlist (with Nix)

`update-playlist` is used to update an existing Spotify playlist with songs from a BBC radio station's current playlist.

To update your playlist with songs from BBC Radio 1:

```bash
bbc-to-spotify update-playlist <your-playlist-id> radio-1
```

Run `bbc-to-spotify update-playlist -h` to show help and options for this command.

## FAQ

### 1. How can I find a playlist's ID?

The playlists ID should be printed out after successfully executing the `create-playlist` command.

Alternatively you can get a Spotify playlist ID by clicking `...` on the playlist's page, and then clicking `Copy link to playlist` under the `Share` menu.

This will give you a full playlist link that looks like the following:

`https://open.spotify.com/playlist/37i9dQZF1DWXRqgorJj26U?si=9f6A6U2jTk-njyZJ64rk3g`

The playlist ID is the code after `playlist/` and before `?si` (`37i9dQZF1DWXRqgorJj26U`).

### 2. I don't want to store my credentials. Can I still use the CLI?

Yes. You can then authorize `bbc-to-spotify` by setting the following environment variables before use: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN`.

You can get a refresh token by running `bbc-to-spotify authorize` and pressing `N` when asked to store credentials.

### 3. What permission scopes are provided to the CLI?

The scopes `modify-playlist-public`and `modify-playlist-private` are provided. See more about scopes here: https://developer.spotify.com/documentation/web-api/concepts/scopes.
