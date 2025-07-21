# Spotify Tools MCP

This MCP server provides tools to interact with the Spotify API.

## Endpoints

### `/get_track_metadata`

Retrieves metadata for a given Spotify track URL.

**Method:** `POST`

**Body:**

```json
{
  "track_url": "YOUR_SPOTIFY_TRACK_URL"
}
```

**Environment Variables:**

*   `SPOTIPY_CLIENT_ID`: Your Spotify application client ID.
*   `SPOTIPY_CLIENT_SECRET`: Your Spotify application client secret.

**Example Usage:**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"track_url": "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"}' http://localhost:5000/get_track_metadata
```
