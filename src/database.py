"""Database operations using TinyDB."""
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))
import config


class SpotifyDatabase:
    """Manages local storage of Spotify library data."""
    
    def __init__(self, db_path: Path = config.DB_PATH):
        """Initialize database connection with write caching for performance."""
        self.db = TinyDB(str(db_path), storage=CachingMiddleware(JSONStorage))
        self.tracks = self.db.table('tracks')
        self.playlists = self.db.table('playlists')
        self.playlist_tracks = self.db.table('playlist_tracks')
        self.saved_tracks = self.db.table('saved_tracks')
        
    def clear_all(self):
        """Clear all data from the database."""
        self.tracks.truncate()
        self.playlists.truncate()
        self.playlist_tracks.truncate()
        self.saved_tracks.truncate()
    
    # Utility counters/maintenance
    def get_playlist_track_count(self, playlist_id: str) -> int:
        """Return number of track relationships for a playlist."""
        PlaylistTrack = Query()
        return len(self.playlist_tracks.search(PlaylistTrack.playlist_id == playlist_id))

    def clear_playlist_tracks(self, playlist_id: str):
        """Remove all track relationships for a playlist."""
        PlaylistTrack = Query()
        self.playlist_tracks.remove(PlaylistTrack.playlist_id == playlist_id)

    def get_saved_tracks_count(self) -> int:
        """Return number of saved/liked tracks."""
        return len(self.saved_tracks)

    def clear_saved_tracks(self):
        """Remove all saved/liked track entries."""
        self.saved_tracks.truncate()
    
    # Track operations
    def insert_track(self, track_data: Dict):
        """Insert or update a track."""
        Track = Query()
        existing = self.tracks.get(Track.id == track_data['id'])
        if existing:
            self.tracks.update(track_data, Track.id == track_data['id'])
        else:
            self.tracks.insert(track_data)
    
    def get_track(self, track_id: str) -> Optional[Dict]:
        """Get a track by ID."""
        Track = Query()
        return self.tracks.get(Track.id == track_id)
    
    def search_tracks(self, query: str) -> List[Dict]:
        """Search tracks by name, artist, or album."""
        Track = Query()
        query_lower = query.lower()
        
        results = self.tracks.search(
            (Track.name.test(lambda v: query_lower in v.lower())) |
            (Track.artist.test(lambda v: query_lower in v.lower())) |
            (Track.album.test(lambda v: query_lower in v.lower()))
        )
        return results
    
    def get_all_tracks(self) -> List[Dict]:
        """Get all tracks."""
        return self.tracks.all()
    
    # Playlist operations
    def insert_playlist(self, playlist_data: Dict):
        """Insert or update a playlist."""
        Playlist = Query()
        existing = self.playlists.get(Playlist.id == playlist_data['id'])
        if existing:
            self.playlists.update(playlist_data, Playlist.id == playlist_data['id'])
        else:
            self.playlists.insert(playlist_data)
    
    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """Get a playlist by ID."""
        Playlist = Query()
        return self.playlists.get(Playlist.id == playlist_id)
    
    def get_all_playlists(self) -> List[Dict]:
        """Get all playlists."""
        return self.playlists.all()
    
    def set_playlist_snapshot(self, playlist_id: str, snapshot_id: str):
        """Update only the snapshot_id for a playlist after successful sync."""
        Playlist = Query()
        self.playlists.update({'snapshot_id': snapshot_id}, Playlist.id == playlist_id)
    
    # Playlist-Track relationship operations
    def add_track_to_playlist(self, playlist_id: str, track_id: str, position: int):
        """Add a track to a playlist."""
        PlaylistTrack = Query()
        existing = self.playlist_tracks.get(
            (PlaylistTrack.playlist_id == playlist_id) & 
            (PlaylistTrack.track_id == track_id)
        )
        if not existing:
            self.playlist_tracks.insert({
                'playlist_id': playlist_id,
                'track_id': track_id,
                'position': position
            })
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get all tracks in a playlist."""
        PlaylistTrack = Query()
        relationships = self.playlist_tracks.search(
            PlaylistTrack.playlist_id == playlist_id
        )
        
        # Sort by position and get full track data
        relationships.sort(key=lambda x: x['position'])
        tracks = []
        for rel in relationships:
            track = self.get_track(rel['track_id'])
            if track:
                tracks.append(track)
        return tracks

    def get_playlists_for_track(self, track_id: str) -> List[Dict]:
        """Get all playlists that contain a given track, ordered by position."""
        PlaylistTrack = Query()
        relationships = self.playlist_tracks.search(
            PlaylistTrack.track_id == track_id
        )
        # Group by playlist, track order by position within each
        relationships.sort(key=lambda x: (x['playlist_id'], x['position']))
        playlists = []
        seen = set()
        for rel in relationships:
            pid = rel['playlist_id']
            if pid in seen:
                continue
            pl = self.get_playlist(pid)
            if pl:
                playlists.append(pl)
                seen.add(pid)
        return playlists
    
    # Saved tracks operations
    def add_saved_track(self, track_id: str, added_at: str):
        """Add a track to saved/liked tracks."""
        SavedTrack = Query()
        existing = self.saved_tracks.get(SavedTrack.track_id == track_id)
        if not existing:
            self.saved_tracks.insert({
                'track_id': track_id,
                'added_at': added_at
            })
    
    def get_saved_tracks(self) -> List[Dict]:
        """Get all saved/liked tracks."""
        saved = self.saved_tracks.all()
        tracks = []
        for s in saved:
            track = self.get_track(s['track_id'])
            if track:
                track['added_at'] = s['added_at']
                tracks.append(track)
        return tracks
    
    # Statistics
    def get_stats(self) -> Dict:
        """Get library statistics."""
        return {
            'total_tracks': len(self.tracks),
            'total_playlists': len(self.playlists),
            'saved_tracks': len(self.saved_tracks)
        }
    
    def close(self):
        """Close database connection."""
        self.db.close()
