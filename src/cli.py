"""Command-line interface for Spotify Library Manager."""
import click
from pathlib import Path
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import config
from database import SpotifyDatabase
from spotify_client import SpotifyClient


@click.group()
def cli():
    """Spotify Library Manager - Search and manage your Spotify library locally."""
    pass


# Helpers
def _print_track_item(track: dict, db: SpotifyDatabase, dup_count: int | None = None):
    click.echo(f"🎵 {track.get('name','')}")
    click.echo(f"   👤 {track.get('artist','')}")
    click.echo(f"   💿 {track.get('album','')}")
    duration_ms = track.get('duration_ms') or 0
    duration_sec = duration_ms // 1000
    duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
    click.echo(f"   ⏱️  {duration_str}")
    # Track URL first
    if track.get('external_url'):
        click.echo(f"   🔗 {track['external_url']}")
    # Duplicates info (optional)
    if dup_count is not None:
        click.echo(f"   🔁 Duplicates: {dup_count} occurrence{'s' if dup_count != 1 else ''}")
    # Playlists containing this track
    playlists = db.get_playlists_for_track(track['id'])
    if playlists:
        label = "playlist" if len(playlists) == 1 else "playlists"
        click.echo(f"   📂 In {label}:")
        for p in playlists:
            click.echo(f"      • {p['name']}")
            if p.get('external_url'):
                click.echo(f"        🔗 {p['external_url']}")
    click.echo()


@cli.command()
def sync_diff():
    """Sync only differences: skip playlists with matching track counts."""
    click.echo("🔄 Sync (difference mode)\n")

    if not config.validate_config():
        click.echo("❌ Spotify credentials not configured!")
        click.echo("   Run 'python src/cli.py setup' first")
        sys.exit(1)

    exit_code = 0
    db = None
    try:
        client = SpotifyClient()
        db = SpotifyDatabase()

        user = client.get_current_user()
        click.echo(f"👤 User: {user['display_name']}\n")

        # Saved tracks diff
        click.echo("📀 Checking saved/liked tracks...")
        remote_total = client.get_saved_tracks_total()
        local_total = db.get_saved_tracks_count()
        click.echo(f"   • Remote: {remote_total} • Local: {local_total}")
        if remote_total != local_total:
            click.echo("   ↻ Updating saved tracks...")
            with click.progressbar(length=100, label='   Saved tracks (fetch)') as bar:
                last = {'count': 0}
                def track_progress(current, total):
                    bar.length = total
                    delta = max(0, current - last['count'])
                    if delta:
                        bar.update(delta)
                        last['count'] = current
                saved_tracks = client.get_saved_tracks(progress_callback=track_progress)
            # Replace local saved tracks
            db.clear_saved_tracks()
            with click.progressbar(length=len(saved_tracks), label='   Saved tracks (write)') as wbar:
                for t in saved_tracks:
                    added_at = t.pop('added_at')
                    db.insert_track(t)
                    db.add_saved_track(t['id'], added_at)
                    wbar.update(1)
            click.echo(f"   ✅ Saved tracks updated: {len(saved_tracks)}")
        else:
            click.echo("   ✅ Up-to-date, skipping saved tracks")

        # Playlists diff
        click.echo("\n📝 Fetching playlists list...")
        with click.progressbar(length=100, label='Playlists') as pbar:
            last = {'count': 0, 'len': 100}
            def playlist_progress(current, total):
                if total != last['len']:
                    pbar.length = total
                    pbar.update(0)
                    last['len'] = total
                delta = max(0, current - last['count'])
                pbar.update(delta)
                last['count'] = current
            playlists = client.get_user_playlists(progress_callback=playlist_progress)
            if last['count'] < pbar.length:
                pbar.update(pbar.length - last['count'])

        click.echo(f"   ✅ Found {len(playlists)} playlists\n")

        updated = 0
        skipped = 0
        for i, playlist in enumerate(playlists, 1):
            local_pl = db.get_playlist(playlist['id'])
            # Prefer snapshot_id comparison; fallback to count when snapshot missing
            if local_pl and local_pl.get('snapshot_id') and playlist.get('snapshot_id'):
                if local_pl['snapshot_id'] == playlist['snapshot_id']:
                    skipped += 1
                    continue
            else:
                local_count = db.get_playlist_track_count(playlist['id'])
                if local_count == playlist['tracks_total'] and local_pl:
                    skipped += 1
                    continue

            click.echo(f"📂 [{i}/{len(playlists)}] {playlist['name']} ({playlist['tracks_total']} tracks)")
            # Insert/update playlist metadata without snapshot first
            pl_no_snap = dict(playlist)
            pl_no_snap.pop('snapshot_id', None)
            db.insert_playlist(pl_no_snap)
            if playlist['tracks_total'] > 0:
                with click.progressbar(length=playlist['tracks_total'], label='   Fetching tracks') as bar:
                    last = {'count': 0, 'len': playlist['tracks_total']}
                    def track_progress(current, total):
                        if total != last['len']:
                            bar.length = total
                            bar.update(0)
                            last['len'] = total
                        delta = max(0, current - last['count'])
                        bar.update(delta)
                        last['count'] = current
                    
                    playlist_tracks = client.get_playlist_tracks(playlist['id'], progress_callback=track_progress)
                    if last['count'] < bar.length:
                        bar.update(bar.length - last['count'])
                # Replace local relationships for this playlist
                db.clear_playlist_tracks(playlist['id'])
                with click.progressbar(length=len(playlist_tracks), label='   Saving to database') as save_bar:
                    for track_data, position in playlist_tracks:
                        db.insert_track(track_data)
                        db.add_track_to_playlist(playlist['id'], track_data['id'], position)
                        save_bar.update(1)
                    if save_bar.pos < save_bar.length:
                        save_bar.update(save_bar.length - save_bar.pos)
            # Commit snapshot only after successful save
            if playlist.get('snapshot_id'):
                db.set_playlist_snapshot(playlist['id'], playlist['snapshot_id'])
            updated += 1

        click.echo("\n" + "="*50)
        click.echo("✅ Diff sync completed!")
        click.echo("="*50)
        click.echo(f"   • Playlists updated: {updated}")
        click.echo(f"   • Playlists skipped: {skipped}")

    except Exception as e:
        click.echo(f"\n❌ Diff sync failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        if db is not None:
            db.close()
        sys.exit(exit_code)
def setup():
    """Setup Spotify API credentials."""
    click.echo("🎵 Spotify Library Manager Setup\n")
    
    # Check if .env exists
    env_file = Path(".env")
    if env_file.exists():
        click.echo("⚠️  .env file already exists!")
        if not click.confirm("Do you want to update it?"):
            return
    
    click.echo("\n📝 You need to create a Spotify App to get credentials:")
    click.echo("   1. Go to https://developer.spotify.com/dashboard/applications")
    click.echo("   2. Click 'Create an App'")
    click.echo("   3. Fill in the details and create the app")
    click.echo("   4. In your app settings, add redirect URI: http://127.0.0.1:8000/callback")
    click.echo("   5. Copy your Client ID and Client Secret\n")
    
    client_id = click.prompt("Enter your Spotify Client ID", type=str)
    client_secret = click.prompt("Enter your Spotify Client Secret", type=str, hide_input=True)
    redirect_uri = click.prompt(
        "Enter your Redirect URI", 
        type=str, 
        default="http://127.0.0.1:8000/callback"
    )
    
    # Write to .env file
    with open(".env", "w") as f:
        f.write(f"SPOTIPY_CLIENT_ID={client_id}\n")
        f.write(f"SPOTIPY_CLIENT_SECRET={client_secret}\n")
        f.write(f"SPOTIPY_REDIRECT_URI={redirect_uri}\n")
    
    click.echo("\n✅ Configuration saved to .env file!")
    click.echo("🚀 Run 'python src/cli.py sync' to download your library")


@cli.command()
def auth():
    """Authenticate with Spotify (opens browser)."""
    click.echo("🔐 Authenticating with Spotify...\n")
    
    if not config.validate_config():
        click.echo("❌ Spotify credentials not configured!")
        click.echo("   Run 'python src/cli.py setup' first")
        return
    
    try:
        client = SpotifyClient()
        user = client.get_current_user()
        click.echo(f"✅ Successfully authenticated as: {user['display_name']}")
        click.echo(f"   Email: {user.get('email', 'N/A')}")
        click.echo(f"   Country: {user.get('country', 'N/A')}")
    except Exception as e:
        click.echo(f"❌ Authentication failed: {str(e)}")


@cli.command()
@click.option('--clear', is_flag=True, help='Clear existing data before syncing')
def sync(clear):
    """Download and sync your entire Spotify library."""
    click.echo("🔄 Syncing Spotify library...\n")
    
    if not config.validate_config():
        click.echo("❌ Spotify credentials not configured!")
        click.echo("   Run 'python src/cli.py setup' first")
        sys.exit(1)
    
    exit_code = 0
    db = None
    try:
        # Initialize clients
        client = SpotifyClient()
        db = SpotifyDatabase()
        
        # Clear database if requested
        if clear:
            click.echo("🗑️  Clearing existing data...")
            db.clear_all()
        
        # Get user info
        user = client.get_current_user()
        click.echo(f"👤 User: {user['display_name']}\n")
        
        # Sync saved tracks
        click.echo("📀 Fetching saved/liked tracks...")
        with click.progressbar(length=100, label='Saved tracks') as bar:
            last = {'count': 0, 'len': 100}
            def track_progress(current, total):
                if total != last['len']:
                    bar.length = total
                    bar.update(0)  # force redraw when total changes
                    last['len'] = total
                delta = max(0, current - last['count'])
                bar.update(delta)
                last['count'] = current

            saved_tracks = client.get_saved_tracks(progress_callback=track_progress)
            # Force bar to complete visually
            if last['count'] < bar.length:
                bar.update(bar.length - last['count'])
        
        click.echo(f"   💾 Saving {len(saved_tracks)} tracks to database...")
        with click.progressbar(length=len(saved_tracks), label='   Writing to database') as bar:
            for track in saved_tracks:
                added_at = track.pop('added_at')
                db.insert_track(track)
                db.add_saved_track(track['id'], added_at)
                bar.update(1)
        
        click.echo(f"   ✅ Saved {len(saved_tracks)} liked tracks\n")
        
        # Sync playlists
        click.echo("📝 Fetching playlists...")
        with click.progressbar(length=100, label='Playlists') as bar:
            last = {'count': 0, 'len': 100}
            def playlist_progress(current, total):
                if total != last['len']:
                    bar.length = total
                    bar.update(0)
                    last['len'] = total
                delta = max(0, current - last['count'])
                bar.update(delta)
                last['count'] = current

            playlists = client.get_user_playlists(progress_callback=playlist_progress)
            if last['count'] < bar.length:
                bar.update(bar.length - last['count'])
        
        click.echo(f"   ✅ Found {len(playlists)} playlists\n")
        
        # Sync each playlist's tracks
        for i, playlist in enumerate(playlists, 1):
            click.echo(f"📂 [{i}/{len(playlists)}] {playlist['name']} ({playlist['tracks_total']} tracks)")
            
            # Save playlist info
            # Insert without committing snapshot yet
            pl_no_snap = dict(playlist)
            pl_no_snap.pop('snapshot_id', None)
            db.insert_playlist(pl_no_snap)
            
            # Get playlist tracks
            if playlist['tracks_total'] > 0:
                with click.progressbar(
                    length=playlist['tracks_total'], 
                    label='   Fetching tracks'
                ) as bar:
                    last = {'count': 0, 'len': playlist['tracks_total']}
                    def track_progress(current, total):
                        if total != last['len']:
                            bar.length = total
                            bar.update(0)
                            last['len'] = total
                        delta = max(0, current - last['count'])
                        bar.update(delta)
                        last['count'] = current

                    playlist_tracks = client.get_playlist_tracks(
                        playlist['id'], 
                        progress_callback=track_progress
                    )
                    if last['count'] < bar.length:
                        bar.update(bar.length - last['count'])
                
                # Save tracks and relationships
                with click.progressbar(length=len(playlist_tracks), label='   Saving to database') as save_bar:
                    for track_data, position in playlist_tracks:
                        db.insert_track(track_data)
                        db.add_track_to_playlist(playlist['id'], track_data['id'], position)
                        save_bar.update(1)
                    if save_bar.pos < save_bar.length:
                        save_bar.update(save_bar.length - save_bar.pos)
            
            # Commit snapshot only after successful save
            if playlist.get('snapshot_id'):
                db.set_playlist_snapshot(playlist['id'], playlist['snapshot_id'])
        
        # Show statistics
        stats = db.get_stats()
        click.echo("\n" + "="*50)
        click.echo("✅ Sync completed successfully!")
        click.echo("="*50)
        click.echo(f"📊 Statistics:")
        click.echo(f"   • Total unique tracks: {stats['total_tracks']}")
        click.echo(f"   • Saved/liked tracks: {stats['saved_tracks']}")
        click.echo(f"   • Total playlists: {stats['total_playlists']}")
        
        
    except Exception as e:
        click.echo(f"\n❌ Sync failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        if db is not None:
            db.close()
        sys.exit(exit_code)


@cli.command()
@click.argument('query')
@click.option('--limit', default=20, help='Maximum number of results to show')
def search(query, limit):
    """Search for tracks in your local library."""
    db = SpotifyDatabase()
    
    click.echo(f"🔍 Searching for: '{query}'\n")
    
    results = db.search_tracks(query)
    
    if not results:
        click.echo("❌ No results found")
        db.close()
        return
    
    click.echo(f"✅ Found {len(results)} result(s)\n")
    
    # Display results
    for i, track in enumerate(results[:limit], 1):
        click.echo(f"{i}.")
        _print_track_item(track, db)
    
    if len(results) > limit:
        click.echo(f"... and {len(results) - limit} more results")
    
    db.close()


@cli.command()
@click.option('--playlist', help='Show tracks from a specific playlist')
def list(playlist):
    """List all playlists or tracks in a playlist."""
    db = SpotifyDatabase()
    
    if playlist:
        # Search for playlist by name
        playlists = db.get_all_playlists()
        matching_playlists = [
            p for p in playlists 
            if playlist.lower() in p['name'].lower()
        ]
        
        if not matching_playlists:
            click.echo(f"❌ No playlist found matching '{playlist}'")
            db.close()
            return
        
        # If multiple matches, show them
        if len(matching_playlists) > 1:
            click.echo(f"Multiple playlists found:")
            for i, p in enumerate(matching_playlists, 1):
                click.echo(f"{i}. {p['name']} ({p['tracks_total']} tracks)")
            choice = click.prompt("Select playlist number", type=int)
            selected_playlist = matching_playlists[choice - 1]
        else:
            selected_playlist = matching_playlists[0]
        
        # Show playlist tracks
        click.echo(f"\n📂 {selected_playlist['name']}")
        click.echo(f"   {selected_playlist['description']}")
        click.echo(f"   👤 By: {selected_playlist['owner']}")
        click.echo(f"   🎵 {selected_playlist['tracks_total']} tracks\n")
        
        tracks = db.get_playlist_tracks(selected_playlist['id'])
        for i, track in enumerate(tracks, 1):
            click.echo(f"{i:3d}. {track['name']} - {track['artist']}")
    
    else:
        # List all playlists
        playlists = db.get_all_playlists()
        
        if not playlists:
            click.echo("❌ No playlists found. Run 'sync' first.")
            db.close()
            return
        
        click.echo(f"📚 Your Playlists ({len(playlists)} total)\n")
        
        for i, playlist in enumerate(playlists, 1):
            icon = "🔓" if playlist['public'] else "🔒"
            collab = " [Collaborative]" if playlist['collaborative'] else ""
            click.echo(f"{i:3d}. {icon} {playlist['name']}{collab}")
            click.echo(f"      👤 {playlist['owner']} • 🎵 {playlist['tracks_total']} tracks")
    
    db.close()


@cli.command()
def stats():
    """Show library statistics."""
    db = SpotifyDatabase()
    
    stats = db.get_stats()
    
    click.echo("\n" + "="*50)
    click.echo("📊 Your Spotify Library Statistics")
    click.echo("="*50)
    click.echo(f"  🎵 Total unique tracks:     {stats['total_tracks']:,}")
    click.echo(f"  ❤️  Saved/liked tracks:     {stats['saved_tracks']:,}")
    click.echo(f"  📂 Total playlists:         {stats['total_playlists']:,}")
    click.echo("="*50)
    
    # Additional stats
    all_tracks = db.get_all_tracks()
    if all_tracks:
        total_duration_ms = sum(t['duration_ms'] for t in all_tracks)
        total_hours = total_duration_ms / (1000 * 60 * 60)
        click.echo(f"  ⏱️  Total listening time:   {total_hours:.1f} hours")
        
        # Most common artists
        artists = {}
        for track in all_tracks:
            for artist in track['artist'].split(', '):
                artists[artist] = artists.get(artist, 0) + 1
        
        top_artists = sorted(artists.items(), key=lambda x: x[1], reverse=True)[:5]
        click.echo("\n  🎤 Top Artists:")
        for artist, count in top_artists:
            click.echo(f"     {artist}: {count} tracks")
    
    click.echo()
    db.close()


@cli.command(name="clear-auth")
@click.option('--dry-run', is_flag=True, help='Show auth cache files that would be removed')
def clear_auth(dry_run):
    """Remove cached Spotify OAuth tokens (.auth-cache*; legacy .cache*)."""
    patterns = [
        ".auth-cache", ".auth-cache-*", ".auth-cache.*",
        ".cache", ".cache-*", ".cache.*",  # legacy
    ]
    root = Path('.')
    to_remove = []
    for pat in patterns:
        to_remove.extend(root.glob(pat))

    # De-duplicate
    files = []
    seen = set()
    for p in to_remove:
        if p.resolve() not in seen:
            files.append(p)
            seen.add(p.resolve())

    if not files:
        click.echo("✅ No cache files found.")
        return

    click.echo("🧹 Cache files:")
    for f in files:
        click.echo(f"   • {f}")

    if dry_run:
        click.echo("\nDRY RUN: No files were deleted.")
        return

    errors = 0
    for f in files:
        try:
            if f.is_dir():
                # Defensive: token cache is typically a file, but handle dir
                for child in f.rglob('*'):
                    try:
                        if child.is_file():
                            child.unlink()
                    except Exception:
                        errors += 1
                try:
                    f.rmdir()
                except Exception:
                    errors += 1
            else:
                f.unlink()
        except Exception:
            errors += 1

    if errors:
        click.echo(f"⚠️  Completed with {errors} error(s). Some files may remain.")
    else:
        click.echo("✅ Cache cleared.")

@cli.command()
@click.option('--limit', default=5, show_default=True, help='Maximum number of duplicate entries to show')
def duplicates(limit):
    """List duplicate tracks across playlists, ordered by occurrences desc."""
    db = SpotifyDatabase()

    # Count occurrences of each track across all playlist relationships
    rels = db.playlist_tracks.all()
    if not rels:
        click.echo("❌ No playlist data found. Run 'sync' first.")
        db.close()
        return

    counts = {}
    for rel in rels:
        tid = rel.get('track_id')
        if not tid:
            continue
        counts[tid] = counts.get(tid, 0) + 1

    # Build list of (track, count) where count > 1
    dupes = []
    for tid, cnt in counts.items():
        if cnt > 1:
            t = db.get_track(tid)
            if t:
                dupes.append((t, cnt))

    if not dupes:
        click.echo("✅ No duplicates found across playlists.")
        db.close()
        return

    # Sort by count desc, then by track name
    dupes.sort(key=lambda x: (-x[1], x[0].get('name',''))) 

    click.echo(f"📋 Top duplicates (showing up to {limit}):\n")
    for idx, (track, cnt) in enumerate(dupes[:limit], 1):
        click.echo(f"{idx}.")
        _print_track_item(track, db, dup_count=cnt)

    db.close()


if __name__ == '__main__':
    cli()
