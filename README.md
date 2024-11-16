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
    * [Troubleshooting Authorization:](#troubleshooting-authorization)
* [Usage](#usage)
* [Examples](#examples)
    * [Creating a playlist](#creating-a-playlist)
    * [Updating a playlist](#updating-a-playlist)
* [FAQ](#faq)
    * [How can I find a playlist's ID?](#how-can-i-find-a-playlists-id)
    * [I don't want to store my credentials. Can I still use the CLI?](#i-dont-want-to-store-my-credentials-can-i-still-use-the-cli)
    * [What permission scopes are provided to the CLI?](#what-permission-scopes-are-provided-to-the-cli)

<!-- vim-markdown-toc -->

## Requirements

The app can be installed using Poetry or Nix.

- **Spotify Account**: A valid Spotify account is required to use this app (free or premium, depending on the functionality).
- **Spotify Developer App**: You need to create a Spotify app to generate client credentials that will be required for authorizing the CLI.
  - You can follow [Spotify instructions](https://developer.spotify.com/documentation/web-api/concepts/apps).
  - It is recommended to use the following redirect URI: `http://localhost:8080/bbc-to-spotify`.
  - Make a note of your client ID and secret.
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

- Enter a temporary nix bash with `bbc-to-spotify` installed:

```bash
nix bash github:archie-judd/bbc-to-spotify
```

- Install imperatively:

```bash
nix profile install github:archie-judd/bbc-to-spotify
```

- Install declaratively with a flake:
  - For example: https://nixos-and-flakes.thiscute.world/nixos-with-flakes/nixos-flake-and-module-system#install-system-packages-from-other-flakes.

Check install was successful by running the following command:

```bash
bbc-to-spotify --version
```

## Authorize the CLI

This process will generate a refresh token, and optionally store it with your client credentials in your home folder for future authentication.

- With **Poetry**:
  ```bash
  poetry run bbc-to-spotify authorize
  ```
- With **Nix**:
  ```bash
  bbc-to-spotify authorize
  ```

You will be prompted for your client ID and client secret. You can copy them from your app's page.

You will then be taken through the steps to generate a refresh token, and asked if your credentials may be stored for future authentication.

> See [I don't want to store my credentials. Can I still use the CLI?](#i-dont-want-to-store-my-credentials-can-i-still-use-the-cli) if you want to use the CLI without storing your credentials.

### Troubleshooting Authorization:

If you did not use `http://localhost:8080/bbc-to-spotify` as a redirect URI when creating your Spotify App, make sure to add the argument `--redirect-uri <your-redirect-uri>`.

Run `poetry run bbc-to-spotify authorize -h` (Poetry) or `bbc-to-spotify -h` (Nix) for help on the `authorize` command.

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

- For **Poetry**:
  ```bash
  poetry run bbc-to-spotify <command> -h
  ```
- For **Nix**:
  ```bash
  bbc-to-spotify <command> -h
  ```

## Examples

### Creating a playlist

The `create-playlist` playlist command is used to create a new Spotify playlist with songs from a BBC radio station's current playlist.

To create a new playlist called "BBC Radio 6 Music" using BBC Radio 6 Music as a source:

- For **Poetry**:
  ```bash
  poetry run bbc-to-spotify create-playlist "BBC Radio 6 Music"  radio-6
  ```
- For **Nix**:
  ```bash
  bbc-to-spotify create-playlist "BBC Radio 6 Music"  radio-6
  ```

Possible sources include:
`radio-1`
`radio-1-xtra`
`radio-2`
`radio-6`
`bbc-asian-network`

The playlist ID will be printed when the playlist has been successfully created. Make a note of it, it will be required for updating the playlist.

### Updating a playlist

`update-playlist` is used to update an existing Spotify playlist with songs from a BBC radio station's current playlist.

To update add songs from BBC radio 1 to a playlist with ID `3UoR0uBr3rl6LXEPDR8n5B`:

- For **Poetry**:
  ```bash
  poetry run bbc-to-spotify update-playlist 3UoR0uBr3rl6LXEPDR8n5B radio-1
  ```
- For **Nix**:
  ```bash
  bbc-to-spotify update-playlist 3UoR0uBr3rl6LXEPDR8n5B radio-1
  ```

See the CLI help for options that can be used with this command.

## FAQ

### How can I find a playlist's ID?

The playlists ID should be printed out after successfully executing the `create-playlist` command.

Alternatively you can get a Spotify playlist ID by clicking `...` on the playlist's page, and then clicking `Copy link to playlist` under the `Share` menu.

This will give you a full playlist link that looks like the following:

`https://open.spotify.com/playlist/37i9dQZF1DWXRqgorJj26U?si=9f6A6U2jTk-njyZJ64rk3g`

The playlist ID is the code after `playlist/` and before `?si` (`37i9dQZF1DWXRqgorJj26U`).

### I don't want to store my credentials. Can I still use the CLI?

Yes. You can then authorize `bbc-to-spotify` by setting the following environment variables before use: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN`.

You can get a refresh token by running `bbc-to-spotify authorize` and pressing `N` when asked to store credentials.

### What permission scopes are provided to the CLI?

The scopes `modify-playlist-public`and `modify-playlist-private` are provided. See more about scopes here: https://developer.spotify.com/documentation/web-api/concepts/scopes.
