import eel
import time
import sys, os
import requests
import copy
from bs4 import BeautifulSoup
import json
from json_minify import json_minify
import pyaudio
import pyaudio._portaudio as pa
import audio_metadata
from io import BytesIO
import pytube
import re
import subprocess
import threading
import numpy as np
from datetime import timedelta
from fuzzywuzzy import process
from send2trash import send2trash
import webbrowser


__version__ = '2.0.0'

# ---- Required Functions ----

def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(base_path, relative_path)

@eel.expose
def get_version():
	return __version__

@eel.expose
def get_translation(code):
	tr_file = os.path.join(resource_path("web"), "locales", code + ".json")
	if os.path.exists(tr_file):
		with open(tr_file, 'r', encoding="utf-8") as file:
			string = json_minify(file.read()) # remove comments

			# remove coma at the end of json
			regex = r'''(?<=[}\]"']),(?!\s*[{["'])'''
			string = re.sub(regex, "", string, 0)

			output = json.loads(string)
			return output
	return

youtube = re.compile(r'(https?://)?(www\.)?((youtube\.(com))/watch\?v=([-\w]+)|youtu\.be/([-\w]+))')

# Settings
SETTINGS = {
	"INPUT_DEVICE": False,
	"OUTPUT_DEVICE": None,
	"PREVIEW_DEVICE": True,
	"CHUNK_SIZE": 2048,
	"permanent_delete": False,
	"AUDIO_MAX_DUR": 30, # for youtube
}
VOLUME = 1.0

# ----- subprocess settings -----
startupinfo = None
if os.name == 'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

# --- Settings Functions ----
@eel.expose
def get_audio_devices():
	p = pyaudio.PyAudio()
	info = p.get_host_api_info_by_index(0)
	numdevices = info.get('deviceCount', 0)
	input_dev = []
	output_dev = []
	for i in range(0, numdevices):
		device = p.get_device_info_by_host_api_device_index(0, i)
		dammit = pa.get_device_info(device["index"]).name
		try:
			decoded = dammit.decode('utf-8')
		except UnicodeDecodeError:
			decoded = dammit.decode(os.device_encoding(0))
		device["name"] = decoded
		if device.get('maxInputChannels', 0) > 0:
			input_dev.append({key: device[key] for key in ["index", "name"]})
		if device.get('maxOutputChannels', 0) > 0:
			output_dev.append({key: device[key] for key in ["index", "name"]})
	return {"input": input_dev, "output": output_dev}


# ----- Settings Functions -------
def load_settings():
	global SETTINGS
	path = os.path.join(os.getcwd(), "settings.json")
	if os.path.exists(path):
		devices = get_audio_devices()
		def make_dict(arr):
			devices_dict = {}
			for i in arr:
				devices_dict[i['name']] = i['index']
			return devices_dict

		with open(path, "r", encoding='utf-8') as file:
			data = json.loads(file.read())
			for key, val in data.items():
				if key == "INPUT_DEVICE" and val != False:
					val = make_dict(devices['input']).get(val)
				elif key == "OUTPUT_DEVICE" and val != False:
					val = make_dict(devices['output']).get(val)
				SETTINGS[key] = val
load_settings()

@eel.expose
def save_settings():
	path = os.path.join(os.getcwd(), "settings.json")
	devices = get_audio_devices()
	def make_dict(arr):
		devices_dict = {}
		for i in arr:
			devices_dict[str(i['index'])] = i['name']
		return devices_dict

	data = copy.deepcopy(SETTINGS)
	data["INPUT_DEVICE"] = make_dict(devices['input']).get(str(SETTINGS["INPUT_DEVICE"]), False)
	data["OUTPUT_DEVICE"] = make_dict(devices['output']).get(str(SETTINGS["OUTPUT_DEVICE"]), False)
	with open(path, "w", encoding='utf-8') as file:
		file.write(json.dumps(data, indent=4, ensure_ascii=False))

# -------------------

@eel.expose
def change_input_device(new_device):
	global SETTINGS, stopRecording
	if new_device == "false":
		SETTINGS["INPUT_DEVICE"] = False
	else:
		SETTINGS["INPUT_DEVICE"] = int(new_device)
	stopRecording = True

@eel.expose
def change_output_device(new_device):
	global SETTINGS, stopRecording
	SETTINGS["OUTPUT_DEVICE"] = int(new_device)
	stopRecording = True

@eel.expose
def change_setting(name, value):
	global SETTINGS
	SETTINGS[name] = value
	save_settings()

@eel.expose
def get_settings():
	return SETTINGS

# -------------------

@eel.expose
def get_local_themes():
	path = os.path.join(os.getcwd(), "themes")
	if os.path.exists(path):
		onlyfiles = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
		styleshits = list(filter(lambda x: x.endswith(".css"), onlyfiles))
		themes = []
		for file in styleshits:
			with open(file, encoding="utf-8") as f:
				text = f.read()
			arr = text.strip("/*").split("*/")
			if len(arr) > 1:
				try:
					config = json.loads(arr[0])
				except:
					continue

				config["css"] = text
				themes.append(config)
		return themes				
	return []

@eel.expose
def get_web_themes():
	url = "https://api.github.com/repos/SuperZombi/soundpad-online/git/trees/main?recursive=1"
	r = requests.get(url)
	data = r.json().get("tree")
	filtered = list(filter(lambda x: "github/themes" in x["path"] and x['path'].endswith(".css"), data))
	root_path = "https://raw.githubusercontent.com/SuperZombi/soundpad-online/main/"
	themes = []
	for i in filtered:
		path = os.path.join(root_path, i["path"])
		os.path.basename(path)

		rq = requests.get(path)
		text = rq.text
		arr = text.strip("/*").split("*/")
		if len(arr) > 1:
			try:
				config = json.loads(arr[0])
			except:
				continue

		config["css"] = text
		themes.append(config)
	return themes

@eel.expose
def open_themes_dir():
	url = "https://github.com/SuperZombi/soundpad-online/tree/main/github/themes"
	webbrowser.open_new(url)

	path = os.path.join(os.getcwd(), "themes")
	if not os.path.exists(path):
		os.mkdir(path)
	os.system(f'explorer "{path}"')

# -------------------

# --- Search Functions ----
def time_to_int(time_str):
	minutes_str, seconds_str = time_str.split(":")
	minutes = int(minutes_str)
	seconds = int(seconds_str)
	total_seconds = 60 * minutes + seconds
	return total_seconds

def int_to_time(integer):
	return '{:02}:{:02}'.format(*divmod(integer, 60))

def get_durration(f):
	metadata = audio_metadata.load(f)
	return round(metadata.streaminfo.duration)

def get_yt_audio(link):
	yt = pytube.YouTube(link)
	stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
	return {"title": yt.title, "duration": int_to_time(yt.length), "link": stream.url}
	

@eel.expose
def search_youtube(text, max_dur=SETTINGS["AUDIO_MAX_DUR"]):
	if youtube.findall(text):
		return [get_yt_audio(text)]
	arr = []
	s = pytube.Search(text)
	for vid in s.results:
		try:
			if vid.length <= max_dur:
				arr.append({
					'title': vid.title,
					'link': vid.watch_url,
					'duration': int_to_time(vid.length)
				})
		except TypeError: None
	return arr


@eel.expose
def search_myinstants(text, limit=1):
	buttonList = []
	for i in range(1, limit+1):
		r = requests.get(f'http://www.myinstants.com/search/?name={text.replace(" ", "+")}&page={i}')
		soup = BeautifulSoup(r.text, 'html.parser')
		for link in soup.find_all("div", class_="instant"):
			buttonName = link.a.text
			buttonUrl = link.find("button", class_="small-button")
			s = buttonUrl['onclick']
			buttonUrl = s.partition("('")[-1].rpartition("')")[0]
			link = "http://www.myinstants.com/" + buttonUrl.split(",")[0].strip("'/")
			button = {
				"title": buttonName,
				"link": link
			}
			buttonList.append(button)

	return buttonList

@eel.expose
def search_zvukogram(text):
	r = requests.get(f'http://zvukogram.com/?r=search&s={text.replace(" ", "+")}')
	soup = BeautifulSoup(r.text, 'html.parser')
	array = []
	for link in soup.find_all("div", class_="onetrack"):
		name = link.find("div", class_="waveTitle").text
		time = link.find("div", class_="waveTime").text
		url = "http://zvukogram.com/" + link['data-track'].strip("/")
		array.append({"title": name, "link": url, "duration": time})
	return array


@eel.expose
def search_meowpad(text, limit=1):
	buttonList = []
	total_pages = 1
	for i in range(1, limit+1):
		if i > total_pages:
			break
		HEADERS = {'meowpad-locale': 'ru-ru'}
		r = requests.get(f'https://api.meowpad.me/v2/sounds/search?q={text.replace(" ", "%20")}&page={i}', headers=HEADERS)
		answer = r.json()
		total_pages = answer['meta']['totalPages']
		tracks = answer['sounds']
		tracks = map(lambda x: {
			"title": x.get("title"),
			"duration": int_to_time(x.get("duration")),
			"link": f'https://api.meowpad.me/v1/download/{x.get("slug").strip("/")}'
		}, tracks)

		buttonList.extend(tracks)
	return buttonList



@eel.expose
def search_favorites(text):
	folder = os.path.join(os.getcwd(), "downloads")
	if not os.path.exists(folder):
		return []
	files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
	if text:
		filtered = process.extractBests(text, files, score_cutoff=60, limit=10)
		files = list(map(lambda x: x[0], filtered))

	files = map(lambda x: {
			"title": os.path.splitext(x)[0],
			"duration": int_to_time(get_durration(os.path.join(folder, x))),
			"link": os.path.join(folder, x),
			"local": True
		}, files)
	return list(files)
# ----------------------------


# --- Play Functions ---------
stopPlaying = False
@eel.expose
def play_sound(url, identifier=None):
	global stopPlaying
	output_file = BytesIO()
	command = ['ffmpeg', '-i', url, '-f', 'wav', '-']
	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
	stdout, stderr = proc.communicate()
	if proc.returncode != 0:
		print(stderr)
	else:
		output_file.write(stdout)
		output_file.seek(0)

		p = pyaudio.PyAudio()
		metadata = audio_metadata.loads(output_file.read())
		if identifier:
			eel.getSoundDuration(identifier, metadata.streaminfo.duration)()
		output_file.seek(0)
		stream = p.open(format=pyaudio.paInt16,
					  channels=metadata.streaminfo.channels,
					  rate=metadata.streaminfo.sample_rate,
					  output_device_index=SETTINGS["OUTPUT_DEVICE"],
					  output=True)

		stream_preview = None
		if SETTINGS["PREVIEW_DEVICE"]:
			stream_preview = p.open(format=pyaudio.paInt16,
					  channels=metadata.streaminfo.channels,
					  rate=metadata.streaminfo.sample_rate,
					  output=True)

		chunk = SETTINGS["CHUNK_SIZE"]
		data = output_file.read(chunk)
		while data:
			if stopPlaying:
				break

			datachuck = np.frombuffer(data, np.int16)
			datachuck = datachuck * VOLUME
			datachuck = datachuck.astype(np.int16)
			datachuck = datachuck.tobytes()

			stream.write(datachuck)
			if stream_preview:
				stream_preview.write(datachuck)
			data = output_file.read(chunk)

		stream.stop_stream()
		stream.close()
		if stream_preview:
			stream_preview.stop_stream()
			stream_preview.close()
		p.terminate()
		stopPlaying = False

@eel.expose
def stop_play():
	global stopPlaying
	stopPlaying = True

@eel.expose
def change_volume(vol):
	global VOLUME
	VOLUME = vol

@eel.expose
def play_sound_url(url, save=False, filename=None):
	youtubemode = False
	if youtube.findall(url):
		def convert_youtube(link):
			url = get_yt_audio(link)["link"]
			if save:
				save_file(url, filename)
			else:
				play_sound(url, link)
		threading.Thread(target=convert_youtube, args=(url,), daemon=True).start()
	else:
		if save:
			save_file(url, filename)
		else:
			threading.Thread(target=play_sound, args=(url, url), daemon=True).start()
	
# -----------------------------
# --- Microphone Function ----
stopRecording = False
def listen_micro():
	global stopRecording
	if SETTINGS["INPUT_DEVICE"] != False:
		p = pyaudio.PyAudio()

		input_stream = p.open(format=pyaudio.paInt16,
					  channels=1,
					  rate=44100,
					  input_device_index=SETTINGS["INPUT_DEVICE"],
					  input=True)
		output_stream = p.open(format=pyaudio.paInt16,
					  channels=1,
					  rate=44100,
					  output_device_index=SETTINGS["OUTPUT_DEVICE"],
					  output=True)

		chunk = SETTINGS["CHUNK_SIZE"]
		input_stream.start_stream()
		while input_stream.is_active():
			data = input_stream.read(chunk)
			output_stream.write(data)
			if stopRecording:
				stopRecording = False
				break

		input_stream.stop_stream()
		input_stream.close()
		output_stream.stop_stream()
		output_stream.close()
		p.terminate()
	else:
		while not stopRecording:
			time.sleep(1)
			if stopRecording:
				stopRecording = False
				break
	threading.Thread(target=listen_micro, daemon=True).start()

# -----------------------------
# --- Storage Functions ------
def save_file(url, filename):
	folder = os.path.join(os.getcwd(), "downloads")
	if not os.path.exists(folder):
		os.mkdir(folder)
	filename = re.sub(r'(?u)[^-\w. ]', '', filename) + ".mp3"
	target = os.path.join(folder, filename)
	def generate_new_file_name(fname):
		if os.path.exists(fname):
			name, extension = os.path.splitext(fname)
			new_name = name + "_1" + extension
			return generate_new_file_name(new_name)
		return fname
	target = generate_new_file_name(target)
	command = ['ffmpeg', '-i', url, "-acodec", "mp3", "-b:a", "128k", '-f', 'mp3', target]
	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
	stdout, stderr = proc.communicate()
	if proc.returncode != 0:
		print(stderr)


@eel.expose
def save_sound(url, filename):
	play_sound_url(url, save=True, filename=filename)

@eel.expose
def delete_sound(url):
	if os.path.exists(url):
		if SETTINGS["permanent_delete"]:
			os.remove(url)
		else:
			send2trash(url)

# -------------------------

eel.init(resource_path("web"))

browsers = ['chrome', 'edge', 'default']
for browser in browsers:
	try:
		threading.Thread(target=listen_micro, daemon=True).start()
		eel.start("main.html", mode=browser)
		break
	except Exception:
		print(f"Failed to launch the app using {browser.title()} browser")
