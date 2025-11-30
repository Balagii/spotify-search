"""Spotify API client wrapper."""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional
import config


class SpotifyClient:
    """Wrapper for Spotify API operations."""
    
    def __init__(self):
        """Initialize Spotify client with OAuth."""
        if not config.validate_config():
            raise ValueError(
                "Spotify credentials not configured. "
                "Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET "
                "in your .env file"
            )
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config.SPOTIPY_CLIENT_ID,
            client_secret=config.SPOTIPY_CLIENT_SECRET,
            redirect_uri=config.SPOTIPY_REDIRECT_URI,
            scope=config.SPOTIFY_SCOPE,
            cache_path=".cache"
        ))
    
    def get_current_user(self) -> Dict:
        """Get current user information."""
        return self.sp.current_user()
    
    def extract_track_data(self, track: Dict) -> Optional[Dict]:
        """Extract relevant track data from Spotify track object."""
        if not track:
            return None
        # Skip local/unavailable tracks that lack a Spotify ID
        if not track.get('id'):
            return None
        artists = track.get('artists') or []
        artist_names = [a.get('name') for a in artists if a and a.get('name')]
        artist_str = ', '.join(artist_names) if artist_names else 'Unknown Artist'
        album_obj = track.get('album') or {}
        album_name = album_obj.get('name') or ''
        
        return {
            'id': track['id'],
            'name': track.get('name') or '',
            'artist': artist_str,
            'album': album_name,
            'duration_ms': track.get('duration_ms') or 0,
            'popularity': track.get('popularity', 0),
            'explicit': track.get('explicit', False),
            'uri': track.get('uri') or '',
            'external_url': (track.get('external_urls') or {}).get('spotify', ''),
            'preview_url': track.get('preview_url', ''),
            'release_date': album_obj.get('release_date', ''),
        }
    
    def get_saved_tracks(self, progress_callback=None) -> List[Dict]:
        """Get all saved/liked tracks from user's library."""
        tracks = []
        offset = 0
        limit = 50
        page = 0
        pages_total = None
        
        while True:
            results = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
            page += 1
            if pages_total is None:
                total = results.get('total', 0) or 0
                pages_total = max(1, (total + limit - 1) // limit)
            
            if not results['items']:
                break
            
            for item in results['items']:
                track_data = self.extract_track_data(item['track'])
                if track_data:
                    track_data['added_at'] = item['added_at']
                    tracks.append(track_data)
            
            if progress_callback and pages_total is not None:
                progress_callback(page, pages_total)
            
            if not results['next']:
                break
            
            offset += limit
        
        # Ensure final progress reaches 100%
        if progress_callback and pages_total is not None:
            progress_callback(pages_total, pages_total)
        return tracks

    def get_saved_tracks_total(self) -> int:
        """Get total count of saved/liked tracks without fetching all pages."""
        results = self.sp.current_user_saved_tracks(limit=1)
        return results.get('total', 0)
    
    def get_user_playlists(self, progress_callback=None) -> List[Dict]:
        """Get all user playlists."""
        playlists = []
        offset = 0
        limit = 50
        page = 0
        pages_total = None
        
        while True:
            results = self.sp.current_user_playlists(limit=limit, offset=offset)
            page += 1
            if pages_total is None:
                total = results.get('total', 0) or 0
                pages_total = max(1, (total + limit - 1) // limit)
            
            if not results['items']:
                break
            
            for item in results['items']:
                playlist_data = {
                    'id': item['id'],
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'owner': item.get('owner', {}).get('display_name') or item.get('owner', {}).get('id', 'Unknown'),
                    'public': item.get('public', False),
                    'collaborative': item.get('collaborative', False),
                    'tracks_total': item['tracks']['total'],
                    'snapshot_id': item.get('snapshot_id', ''),
                    'uri': item['uri'],
                    'external_url': item['external_urls'].get('spotify', ''),
                }
                playlists.append(playlist_data)
            
            if progress_callback and pages_total is not None:
                progress_callback(page, pages_total)
            
            if not results['next']:
                break
            
            offset += limit
        
        if progress_callback and pages_total is not None:
            progress_callback(pages_total, pages_total)
        return playlists
    
    def get_playlist_tracks(self, playlist_id: str, progress_callback=None) -> List[tuple]:
        """
        Get all tracks from a playlist.
        Returns list of tuples: (track_data, position)
        """
        tracks = []
        offset = 0
        limit = 100
        position = 0
        page = 0
        pages_total = None
        
        while True:
            results = self.sp.playlist_tracks(
                playlist_id, 
                limit=limit, 
                offset=offset,
                fields='items(track(id,name,artists,album,duration_ms,popularity,explicit,uri,external_urls,preview_url)),next,total'
            )
            page += 1
            if pages_total is None:
                total = results.get('total', 0) or 0
                pages_total = max(1, (total + limit - 1) // limit)
            
            if not results['items']:
                break
            
            for item in results['items']:
                if item['track']:  # Sometimes tracks can be None (deleted/unavailable)
                    track_data = self.extract_track_data(item['track'])
                    if track_data:
                        tracks.append((track_data, position))
                        position += 1
            
            if progress_callback and pages_total is not None:
                progress_callback(page, pages_total)
            
            if not results['next']:
                break
            
            offset += limit
        
        # Ensure final progress reaches 100%
        if progress_callback and pages_total is not None:
            progress_callback(pages_total, pages_total)
        return tracks
