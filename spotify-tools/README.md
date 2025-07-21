# Spotify Tools MCP Server

A Model Context Protocol (MCP) server that provides comprehensive read-only access to Spotify's music data and metadata.

## Features

- **Search**: Search for tracks, albums, artists, playlists, shows, and episodes
- **Track Information**: Get detailed track metadata, audio features, and audio analysis
- **Album Information**: Get album details and track listings
- **Artist Information**: Get artist details, albums, top tracks, and related artists
- **Playlist Information**: Get playlist details and track listings
- **Music Discovery**: Get recommendations based on seeds and audio features
- **Browse Content**: Access new releases, featured playlists, and browse categories
- **Audio Analysis**: Get detailed audio features and analysis for tracks
- **Market Support**: Access content specific to different countries/markets

## Configuration


The server requires Spotify API credentials. You can provide them in any of these ways:

### Option 1: Separate Environment Variables (Recommended)
Set the following environment variables:

* `MCP_SPOTIFY_CLIENT_ID`: Your Spotify Client ID
* `MCP_SPOTIFY_CLIENT_SECRET`: Your Spotify Client Secret

#### Example VS Code `settings.json` configuration:

```json
{
  "mcp.servers": {
    "spotify-tools": {
      "command": "python",
      "args": ["/path/to/spotify-tools/server.py"],
      "env": {
        "MCP_SPOTIFY_CLIENT_ID": "your_client_id",
        "MCP_SPOTIFY_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Option 2: Single JSON Environment Variable
Set the `MCP_SPOTIFY_CONFIG` environment variable with a JSON string:

```bash
export MCP_SPOTIFY_CONFIG='{"client_id":"your_client_id","client_secret":"your_client_secret"}'
```

### Option 3: Config File
Create a `config.json` file in the same directory as the server:

```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

## Getting Spotify API Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Create a new app
4. Copy the Client ID and Client Secret

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the server:

```bash
python server.py
```

## Available Tools

### Search and Discovery
- `search_spotify`: Search for content on Spotify
- `get_recommendations`: Get track recommendations
- `get_new_releases`: Get new album releases
- `get_featured_playlists`: Get featured playlists
- `get_browse_categories`: Get browse categories
- `get_category_playlists`: Get playlists from a category
- `get_available_genre_seeds`: Get available genres for recommendations

### Track Information
- `get_track_info`: Get detailed track information
- `get_multiple_tracks`: Get information for multiple tracks
- `get_track_audio_features`: Get audio features for a track
- `get_multiple_tracks_audio_features`: Get audio features for multiple tracks
- `get_track_audio_analysis`: Get detailed audio analysis for a track

### Album Information
- `get_album_info`: Get detailed album information
- `get_album_tracks`: Get tracks from an album

### Artist Information
- `get_artist_info`: Get detailed artist information
- `get_artist_albums`: Get albums by an artist
- `get_artist_top_tracks`: Get an artist's top tracks
- `get_related_artists`: Get artists related to an artist

### Playlist Information
- `get_playlist_info`: Get detailed playlist information
- `get_playlist_tracks`: Get tracks from a playlist

### Utility
- `show_version`: Show version and changelog information

## Authentication

The server uses Spotify's Client Credentials flow, which provides access to public data without requiring user authentication. This is perfect for read-only operations and metadata retrieval.

## Market Support

Most tools support a `market` parameter to get content specific to a particular country. Use ISO 3166-1 alpha-2 country codes (e.g., "US", "GB", "ES", "DE").

## Audio Features

The audio features include:
- **Acousticness**: Confidence measure of whether the track is acoustic
- **Danceability**: How suitable a track is for dancing
- **Energy**: Perceptual measure of intensity and power
- **Instrumentalness**: Predicts whether a track contains no vocals
- **Liveness**: Detects the presence of an audience in the recording
- **Loudness**: Overall loudness of a track in decibels (dB)
- **Speechiness**: Detects the presence of spoken words
- **Tempo**: Overall estimated tempo in beats per minute (BPM)
- **Valence**: Musical positiveness conveyed by a track
- **Popularity**: Popularity score between 0 and 100

## Limitations

- Read-only access (no playback control or user data modification)
- Rate limits apply as per Spotify API guidelines
- Requires active internet connection
- Some content may be region-restricted

## Error Handling

The server includes comprehensive error handling for:
- Authentication failures
- Invalid IDs or parameters
- Network connectivity issues
- Rate limiting
- Market restrictions

All errors are returned as descriptive strings to help with debugging.
