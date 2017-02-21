How to use (Windows):
1. Install python 2.7
://www.python.org/downloads/ython-levenshtein

2. You need to install pip
https://pip.pypa.io/en/stable/installing/

3. You need to add pip and python to your path

4. Run the setup.bat script in cmd.exe

5. Fill in the required information in settings.json (you can use the settings_schema.json see what's required). There's a few steps to get this information
	5.1. You need to create a spotify application to get the client_id, client_secret, redirect_url. You can get on here: https://developer.spotify.com/my-applications/#!/.
	     Then you go to "My Applications" and create and app. You can put anything for the redirect uri. I use "http://localhost:8888/callback".
	5.2. You can get the playlist id and username by going to a playlist on spotify. The url should be in this format: https://play.spotify.com/user/username/playlist/playlist_id.
	     You can grab that information and input it into the json
6. Run "python spotifytogoogle.py"
