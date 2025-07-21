import os
import re
import json
import base64
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime


def get_spotify_config() -> Dict[str, str]:
    """Retrieve the Spotify configuration from environment variable or config file."""
    # 1. Try JSON config in env var
    config_str = os.environ.get("MCP_SPOTIFY_CONFIG")
    if config_str:
        try:
            return json.loads(config_str)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in MCP_SPOTIFY_CONFIG: {e}")

    # 2. Try separate env vars
    client_id = os.environ.get("MCP_SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("MCP_SPOTIFY_CLIENT_SECRET")
    if client_id and client_secret:
        return {"client_id": client_id, "client_secret": client_secret}

    # 3. Try config file
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)

    raise Exception("No Spotify configuration found. Set MCP_SPOTIFY_CONFIG, MCP_SPOTIFY_CLIENT_ID and MCP_SPOTIFY_CLIENT_SECRET, or create config.json")


def read_file(path: str) -> str:
    """Read the contents of a file and return as string."""
    with open(path, "r") as f:
        return f.read()


def parse_changelog(changelog: str) -> List[Dict[str, Any]]:
    """Parse the changelog markdown into a structured list."""
    version_pattern = re.compile(r"^##+\s*\[?v?(\d+\.\d+\.\d+(?:-[^\]\s]+)?)\]?\s*-?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})?\s*$", re.MULTILINE)
    matches = list(version_pattern.finditer(changelog))
    changelog_entries = []
    for i, m in enumerate(matches):
        v = m.group(1)
        date = m.group(2) or None
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(changelog)
        section = changelog[start:end].strip()
        changes = {}
        type_pattern = re.compile(r"^###\s+([A-Za-z ]+)\s*$", re.MULTILINE)
        type_matches = list(type_pattern.finditer(section))
        for j, t in enumerate(type_matches):
            change_type = t.group(1).strip()
            t_start = t.end()
            t_end = type_matches[j+1].start() if j+1 < len(type_matches) else len(section)
            bullets = re.findall(r"^[-*]\s+(.*)$", section[t_start:t_end], re.MULTILINE)
            changes[change_type] = bullets
        changelog_entries.append({
            "version": v,
            "date": date,
            "changes": changes
        })
    return changelog_entries


class SpotifyAPI:
    """Spotify API client for read-only operations."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Spotify using Client Credentials flow."""
        auth_url = "https://accounts.spotify.com/api/token"
        
        # Create base64 encoded client credentials
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("ascii")
        auth_base64 = base64.b64encode(auth_bytes).decode("ascii")
        
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an authenticated request to the Spotify API."""
        if not self.access_token:
            self._authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 401:
            # Token expired, re-authenticate
            self._authenticate()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.get(url, headers=headers, params=params)
        
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, search_type: str = "track", limit: int = 20, offset: int = 0, market: str = "US") -> Dict[str, Any]:
        """Search for tracks, albums, artists, or playlists."""
        params = {
            "q": query,
            "type": search_type,
            "limit": min(limit, 50),
            "offset": offset,
            "market": market
        }
        return self._make_request("search", params)
    
    def get_track(self, track_id: str, market: str = "US") -> Dict[str, Any]:
        """Get detailed information about a track."""
        params = {"market": market}
        return self._make_request(f"tracks/{track_id}", params)
    
    def get_tracks(self, track_ids: List[str], market: str = "US") -> Dict[str, Any]:
        """Get detailed information about multiple tracks."""
        params = {
            "ids": ",".join(track_ids[:50]),  # Limit to 50 tracks
            "market": market
        }
        return self._make_request("tracks", params)
    
    def get_album(self, album_id: str, market: str = "US") -> Dict[str, Any]:
        """Get detailed information about an album."""
        params = {"market": market}
        return self._make_request(f"albums/{album_id}", params)
    
    def get_album_tracks(self, album_id: str, limit: int = 20, offset: int = 0, market: str = "US") -> Dict[str, Any]:
        """Get tracks from an album."""
        params = {
            "limit": min(limit, 50),
            "offset": offset,
            "market": market
        }
        return self._make_request(f"albums/{album_id}/tracks", params)
    
    def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """Get detailed information about an artist."""
        return self._make_request(f"artists/{artist_id}")
    
    def get_artist_albums(self, artist_id: str, include_groups: str = "album", limit: int = 20, offset: int = 0, market: str = "US") -> Dict[str, Any]:
        """Get albums by an artist."""
        params = {
            "include_groups": include_groups,
            "limit": min(limit, 50),
            "offset": offset,
            "market": market
        }
        return self._make_request(f"artists/{artist_id}/albums", params)
    
    def get_artist_top_tracks(self, artist_id: str, market: str = "US") -> Dict[str, Any]:
        """Get an artist's top tracks."""
        params = {"market": market}
        return self._make_request(f"artists/{artist_id}/top-tracks", params)
    
    def get_related_artists(self, artist_id: str) -> Dict[str, Any]:
        """Get artists related to a given artist."""
        return self._make_request(f"artists/{artist_id}/related-artists")
    
    def get_playlist(self, playlist_id: str, market: str = "US") -> Dict[str, Any]:
        """Get detailed information about a playlist."""
        params = {"market": market}
        return self._make_request(f"playlists/{playlist_id}", params)
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 20, offset: int = 0, market: str = "US") -> Dict[str, Any]:
        """Get tracks from a playlist."""
        params = {
            "limit": min(limit, 50),
            "offset": offset,
            "market": market
        }
        return self._make_request(f"playlists/{playlist_id}/tracks", params)
    
    def get_audio_features(self, track_id: str) -> Dict[str, Any]:
        """Get audio features for a track."""
        return self._make_request(f"audio-features/{track_id}")
    
    def get_audio_features_multiple(self, track_ids: List[str]) -> Dict[str, Any]:
        """Get audio features for multiple tracks."""
        params = {"ids": ",".join(track_ids[:100])}  # Limit to 100 tracks
        return self._make_request("audio-features", params)
    
    def get_audio_analysis(self, track_id: str) -> Dict[str, Any]:
        """Get detailed audio analysis for a track."""
        return self._make_request(f"audio-analysis/{track_id}")
    
    def get_genre_seeds(self) -> Dict[str, Any]:
        """Get available genre seeds for recommendations."""
        return self._make_request("recommendations/available-genre-seeds")
    
    def get_recommendations(self, seed_artists: List[str] = None, seed_genres: List[str] = None, 
                          seed_tracks: List[str] = None, limit: int = 20, market: str = "US", **audio_features) -> Dict[str, Any]:
        """Get track recommendations."""
        params = {
            "limit": min(limit, 100),
            "market": market
        }
        
        if seed_artists:
            params["seed_artists"] = ",".join(seed_artists[:5])
        if seed_genres:
            params["seed_genres"] = ",".join(seed_genres[:5])
        if seed_tracks:
            params["seed_tracks"] = ",".join(seed_tracks[:5])
        
        # Add audio feature parameters
        for key, value in audio_features.items():
            if key.startswith(("min_", "max_", "target_")) and value is not None:
                params[key] = value
        
        return self._make_request("recommendations", params)
    
    def get_new_releases(self, limit: int = 20, offset: int = 0, country: str = "US") -> Dict[str, Any]:
        """Get new album releases."""
        params = {
            "limit": min(limit, 50),
            "offset": offset,
            "country": country
        }
        return self._make_request("browse/new-releases", params)
    
    def get_featured_playlists(self, limit: int = 20, offset: int = 0, country: str = "US") -> Dict[str, Any]:
        """Get featured playlists."""
        params = {
            "limit": min(limit, 50),
            "offset": offset,
            "country": country
        }
        return self._make_request("browse/featured-playlists", params)
    
    def get_categories(self, limit: int = 20, offset: int = 0, country: str = "US", locale: str = "en_US") -> Dict[str, Any]:
        """Get browse categories."""
        params = {
            "limit": min(limit, 50),
            "offset": offset,
            "country": country,
            "locale": locale
        }
        return self._make_request("browse/categories", params)
    
    def get_category_playlists(self, category_id: str, limit: int = 20, offset: int = 0, country: str = "US") -> Dict[str, Any]:
        """Get playlists from a specific category."""
        params = {
            "limit": min(limit, 50),
            "offset": offset,
            "country": country
        }
        return self._make_request(f"browse/categories/{category_id}/playlists", params)


# Initialize the MCP server
mcp = FastMCP("Spotify Tools")

# Global Spotify API client
spotify_client = None


def get_spotify_client():
    """Get or create the Spotify API client."""
    global spotify_client
    if spotify_client is None:
        config = get_spotify_config()
        spotify_client = SpotifyAPI(config["client_id"], config["client_secret"])
    return spotify_client


@mcp.tool()
def show_version() -> str:
    """Show the current version and changelog for the spotify-tools MCP server."""
    try:
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        changelog_path = os.path.join(os.path.dirname(__file__), "CHANGELOG.md")
        
        version = read_file(version_path).strip() if os.path.exists(version_path) else "unknown"
        changelog = read_file(changelog_path) if os.path.exists(changelog_path) else "No changelog available"
        
        changelog_data = parse_changelog(changelog)
        
        return json.dumps({
            "version": version,
            "changelog": changelog_data
        }, indent=2)
    except Exception as e:
        return f"Error reading version info: {str(e)}"


@mcp.tool()
def search_spotify(query: str, search_type: str = "track", limit: int = 20, offset: int = 0, market: str = "US") -> str:
    """
    Search for content on Spotify.
    
    Args:
        query: Search query string
        search_type: Type of content to search for (track, album, artist, playlist, show, episode)
        limit: Number of results to return (max 50)
        offset: Offset for pagination
        market: Market/country code (e.g., US, GB, ES)
    """
    try:
        client = get_spotify_client()
        result = client.search(query, search_type, limit, offset, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching Spotify: {str(e)}"


@mcp.tool()
def get_track_info(track_id: str, market: str = "US") -> str:
    """
    Get detailed information about a specific track.
    
    Args:
        track_id: Spotify track ID
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        result = client.get_track(track_id, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting track info: {str(e)}"


@mcp.tool()
def get_multiple_tracks(track_ids: str, market: str = "US") -> str:
    """
    Get detailed information about multiple tracks.
    
    Args:
        track_ids: Comma-separated list of Spotify track IDs (max 50)
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        ids_list = [tid.strip() for tid in track_ids.split(",")]
        result = client.get_tracks(ids_list, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting tracks info: {str(e)}"


@mcp.tool()
def get_album_info(album_id: str, market: str = "US") -> str:
    """
    Get detailed information about a specific album.
    
    Args:
        album_id: Spotify album ID
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        result = client.get_album(album_id, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting album info: {str(e)}"


@mcp.tool()
def get_album_tracks(album_id: str, limit: int = 20, offset: int = 0, market: str = "US") -> str:
    """
    Get tracks from a specific album.
    
    Args:
        album_id: Spotify album ID
        limit: Number of tracks to return (max 50)
        offset: Offset for pagination
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        result = client.get_album_tracks(album_id, limit, offset, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting album tracks: {str(e)}"


@mcp.tool()
def get_artist_info(artist_id: str) -> str:
    """
    Get detailed information about a specific artist.
    
    Args:
        artist_id: Spotify artist ID
    """
    try:
        client = get_spotify_client()
        result = client.get_artist(artist_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting artist info: {str(e)}"


@mcp.tool()
def get_artist_albums(artist_id: str, include_groups: str = "album", limit: int = 20, offset: int = 0, market: str = "US") -> str:
    """
    Get albums by a specific artist.
    
    Args:
        artist_id: Spotify artist ID
        include_groups: Album types to include (album, single, appears_on, compilation)
        limit: Number of albums to return (max 50)
        offset: Offset for pagination
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        result = client.get_artist_albums(artist_id, include_groups, limit, offset, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting artist albums: {str(e)}"


@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US") -> str:
    """
    Get an artist's top tracks.
    
    Args:
        artist_id: Spotify artist ID
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        result = client.get_artist_top_tracks(artist_id, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting artist top tracks: {str(e)}"


@mcp.tool()
def get_related_artists(artist_id: str) -> str:
    """
    Get artists related to a specific artist.
    
    Args:
        artist_id: Spotify artist ID
    """
    try:
        client = get_spotify_client()
        result = client.get_related_artists(artist_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting related artists: {str(e)}"


@mcp.tool()
def get_playlist_info(playlist_id: str, market: str = "US") -> str:
    """
    Get detailed information about a specific playlist.
    
    Args:
        playlist_id: Spotify playlist ID
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        result = client.get_playlist(playlist_id, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting playlist info: {str(e)}"


@mcp.tool()
def get_playlist_tracks(playlist_id: str, limit: int = 20, offset: int = 0, market: str = "US") -> str:
    """
    Get tracks from a specific playlist.
    
    Args:
        playlist_id: Spotify playlist ID
        limit: Number of tracks to return (max 50)
        offset: Offset for pagination
        market: Market/country code
    """
    try:
        client = get_spotify_client()
        result = client.get_playlist_tracks(playlist_id, limit, offset, market)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting playlist tracks: {str(e)}"


@mcp.tool()
def get_track_audio_features(track_id: str) -> str:
    """
    Get audio features for a specific track (danceability, energy, tempo, etc.).
    
    Args:
        track_id: Spotify track ID
    """
    try:
        client = get_spotify_client()
        result = client.get_audio_features(track_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting audio features: {str(e)}"


@mcp.tool()
def get_multiple_tracks_audio_features(track_ids: str) -> str:
    """
    Get audio features for multiple tracks.
    
    Args:
        track_ids: Comma-separated list of Spotify track IDs (max 100)
    """
    try:
        client = get_spotify_client()
        ids_list = [tid.strip() for tid in track_ids.split(",")]
        result = client.get_audio_features_multiple(ids_list)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting audio features: {str(e)}"


@mcp.tool()
def get_track_audio_analysis(track_id: str) -> str:
    """
    Get detailed audio analysis for a specific track.
    
    Args:
        track_id: Spotify track ID
    """
    try:
        client = get_spotify_client()
        result = client.get_audio_analysis(track_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting audio analysis: {str(e)}"


@mcp.tool()
def get_available_genre_seeds() -> str:
    """Get available genre seeds for recommendations."""
    try:
        client = get_spotify_client()
        result = client.get_genre_seeds()
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting genre seeds: {str(e)}"


@mcp.tool()
def get_recommendations(seed_artists: str = "", seed_genres: str = "", seed_tracks: str = "", 
                       limit: int = 20, market: str = "US", min_acousticness: Optional[float] = None,
                       max_acousticness: Optional[float] = None, target_acousticness: Optional[float] = None,
                       min_danceability: Optional[float] = None, max_danceability: Optional[float] = None,
                       target_danceability: Optional[float] = None, min_energy: Optional[float] = None,
                       max_energy: Optional[float] = None, target_energy: Optional[float] = None,
                       min_instrumentalness: Optional[float] = None, max_instrumentalness: Optional[float] = None,
                       target_instrumentalness: Optional[float] = None, min_liveness: Optional[float] = None,
                       max_liveness: Optional[float] = None, target_liveness: Optional[float] = None,
                       min_loudness: Optional[float] = None, max_loudness: Optional[float] = None,
                       target_loudness: Optional[float] = None, min_speechiness: Optional[float] = None,
                       max_speechiness: Optional[float] = None, target_speechiness: Optional[float] = None,
                       min_tempo: Optional[float] = None, max_tempo: Optional[float] = None,
                       target_tempo: Optional[float] = None, min_valence: Optional[float] = None,
                       max_valence: Optional[float] = None, target_valence: Optional[float] = None,
                       min_popularity: Optional[int] = None, max_popularity: Optional[int] = None,
                       target_popularity: Optional[int] = None) -> str:
    """
    Get track recommendations based on seed data and audio features.
    
    Args:
        seed_artists: Comma-separated list of artist IDs (max 5)
        seed_genres: Comma-separated list of genre names (max 5)
        seed_tracks: Comma-separated list of track IDs (max 5)
        limit: Number of recommendations to return (max 100)
        market: Market/country code
        min_acousticness: Minimum acousticness (0.0 to 1.0)
        max_acousticness: Maximum acousticness (0.0 to 1.0)
        target_acousticness: Target acousticness (0.0 to 1.0)
        ... (similar parameters for other audio features)
    """
    try:
        client = get_spotify_client()
        
        # Parse comma-separated values
        artists = [a.strip() for a in seed_artists.split(",") if a.strip()] if seed_artists else []
        genres = [g.strip() for g in seed_genres.split(",") if g.strip()] if seed_genres else []
        tracks = [t.strip() for t in seed_tracks.split(",") if t.strip()] if seed_tracks else []
        
        # Build audio features parameters
        audio_features = {}
        for param_name, param_value in locals().items():
            if param_name.startswith(("min_", "max_", "target_")) and param_value is not None:
                audio_features[param_name] = param_value
        
        result = client.get_recommendations(
            seed_artists=artists,
            seed_genres=genres,
            seed_tracks=tracks,
            limit=limit,
            market=market,
            **audio_features
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting recommendations: {str(e)}"


@mcp.tool()
def get_new_releases(limit: int = 20, offset: int = 0, country: str = "US") -> str:
    """
    Get new album releases.
    
    Args:
        limit: Number of albums to return (max 50)
        offset: Offset for pagination
        country: Country code
    """
    try:
        client = get_spotify_client()
        result = client.get_new_releases(limit, offset, country)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting new releases: {str(e)}"


@mcp.tool()
def get_featured_playlists(limit: int = 20, offset: int = 0, country: str = "US") -> str:
    """
    Get featured playlists.
    
    Args:
        limit: Number of playlists to return (max 50)
        offset: Offset for pagination
        country: Country code
    """
    try:
        client = get_spotify_client()
        result = client.get_featured_playlists(limit, offset, country)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting featured playlists: {str(e)}"


@mcp.tool()
def get_browse_categories(limit: int = 20, offset: int = 0, country: str = "US", locale: str = "en_US") -> str:
    """
    Get browse categories.
    
    Args:
        limit: Number of categories to return (max 50)
        offset: Offset for pagination
        country: Country code
        locale: Locale code
    """
    try:
        client = get_spotify_client()
        result = client.get_categories(limit, offset, country, locale)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting browse categories: {str(e)}"


@mcp.tool()
def get_category_playlists(category_id: str, limit: int = 20, offset: int = 0, country: str = "US") -> str:
    """
    Get playlists from a specific category.
    
    Args:
        category_id: Category ID
        limit: Number of playlists to return (max 50)
        offset: Offset for pagination
        country: Country code
    """
    try:
        client = get_spotify_client()
        result = client.get_category_playlists(category_id, limit, offset, country)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting category playlists: {str(e)}"


if __name__ == "__main__":
    mcp.run()
