import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_track_metadata', methods=['POST'])
def get_track_metadata():
    """
    Retrieves metadata for a given Spotify track URL.
    """
    data = request.get_json()
    track_url = data.get('track_url')

    if not track_url:
        return jsonify({'error': 'Missing track_url'}), 400

    try:
        client_id = os.environ.get('SPOTIPY_CLIENT_ID')
        client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')

        if not client_id or not client_secret:
            return jsonify({'error': 'Missing Spotify API credentials'}), 500

        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        track = sp.track(track_url)

        metadata = {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'track_number': track['track_number'],
            'disc_number': track['disc_number'],
            'href': track['href'],
            'id': track['id'],
            'uri': track['uri']
        }

        return jsonify(metadata)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
