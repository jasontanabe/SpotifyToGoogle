import sys
import spotipy
import gmusicapi
import json
import jsonschema
import base64
import getpass
import traceback
import codecs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from gmusicapi import Mobileclient
from spotipy.oauth2 import SpotifyClientCredentials

def main():
  sys.stdout = codecs.getwriter('utf8')(sys.stdout)
  sys.stderr = codecs.getwriter('utf8')(sys.stderr)

  with open('settings.json') as f:
    settings = json.load(f)

  with open('settings_schema.json') as f:
    schema = json.load(f)

  try:
    jsonschema.validate(settings, schema)
  except:
    print traceback.format_exc()
    return

  client_id = settings['client_id']
  client_secret = settings['client_secret']
  redirect_url = settings['redirect_url']
  gmusic_login = settings['gmusic_login']

  if 'gmusic_pw' not in settings:
    gmusic_pw = getpass.getpass('Enter your google music password (you only need to do this once): ')
  else:
    gmusic_pw = base64.b64decode(settings['gmusic_pw'])
  
  # client credentials flow
  print 'Logging into Spotify'
  client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
  sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

  # gmusic controller
  print 'logging into Google music'
  gmusic = Mobileclient()
  logged_in = gmusic.login(gmusic_login, gmusic_pw, Mobileclient.FROM_MAC_ADDRESS) 
  if logged_in:
    settings['gmusic_pw'] = base64.b64encode(gmusic_pw)
    with open('settings.json', 'w') as f:
      json.dump(settings, f, sort_keys=True, indent=2, separators=(',', ': '))
  else:
    print 'Unable to login, check credentials'
    return

  all_gmusic_playlists = gmusic.get_all_playlists()
  errors = []
  for playlist_settings in settings['playlists']:
    # get all names and artists from the particular playlists
    username = playlist_settings['username']
    tid = playlist_settings['id']
    playlist = sp.user_playlist(username, tid)
    print 'Found spotify playlist: ' + playlist['name']
    playlist_name = 'Spotify ' + playlist['name']
    spotify_tracks = playlist['tracks']['items']
    song_names = [t['track']['name'] for t in spotify_tracks]
    artists = [t['track']['artists'][0]['name'] for t in spotify_tracks]
    if (len(artists) != len(song_names)):
      print 'Error: can\'t match up all songs to artists'
      return
    spotify_tracks = zip(song_names, artists)

    # delete existing playlists we imported
    for playlist in all_gmusic_playlists:
      if playlist['name'] == playlist_name:
        gmusic.delete_playlist(playlist['id'])

    print 'Creating Google music playlist: ' + playlist_name
    g_playlist = gmusic.create_playlist(playlist_name)
    for spotify_track in spotify_tracks:
      try:
        spotify_song_name = spotify_track[0]
        spotify_artist_name = spotify_track[1]
        songs = gmusic.search(spotify_song_name + ' ' + spotify_artist_name)['song_hits']
      
        found_song = False
        # if we found a song match
        if (len(songs) > 0):
          for song in songs:
            found_song_name = song['track']['title']
            found_song_artist = song['track']['albumArtist']
            fuzz_ratio_name = fuzz.partial_ratio(found_song_name, spotify_song_name) 
            fuzz_ratio_artist = fuzz.partial_ratio(found_song_artist, spotify_artist_name) 
            # check that it's a close match to what we are looking for
            if (fuzz_ratio_name + fuzz_ratio_artist > 70):
              print 'Adding: ' + spotify_song_name  + ', ' + spotify_artist_name
              gmusic.add_songs_to_playlist(g_playlist, song['track']['storeId'])
              found_song = True
              break

          if not found_song:
            error = 'FuzzRatio not in threshold|spotify: ' + spotify_song_name + ',' + spotify_artist_name +\
                    '|gmusic: ' + found_song_name + ',' + found_song_artist
            print error
            errors.append(error)
        else:
          error = 'Unable to add, song: ' + spotify_song_name + ', artist: ' + spotify_artist_name
          print error
          errors.append(error)
      except:     
        error = traceback.format_exc()
        print error
        errors.append(error)
 

  with codecs.open('errors.log', 'w', 'utf-8') as f:
    for error in errors:
      f.write(error + '\n')


if __name__ == "__main__":
  main()
