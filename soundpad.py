import eel
import time
import sys, os
import requests
from bs4 import BeautifulSoup
import json
import pyaudio
import pyaudio._portaudio as pa
import audio_metadata
from io import BytesIO
from youtubesearchpython import *
import pytube
import re
import subprocess
import threading
from datetime import timedelta
from fuzzywuzzy import process
from send2trash import send2trash


__version__ = '1.0.0'

# ---- Required Functions ----

def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(base_path, relative_path)

@eel.expose
def get_version():
	return __version__

youtube = re.compile(r'(https?://)?(www\.)?((youtube\.(com))/watch\?v=([-\w]+)|youtu\.be/([-\w]+))')

# Settings
INPUT_DEVICE = False
OUTPUT_DEVICE = None
PREVIEW_DEVICE = False
CHUNK_SIZE = 2048
permanent_delete = False
AUDIO_MAX_DUR = 30 # for youtube

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
				globals()[key] = val
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

	data = {
		"INPUT_DEVICE": make_dict(devices['input']).get(str(INPUT_DEVICE), False),
		"OUTPUT_DEVICE": make_dict(devices['output']).get(str(OUTPUT_DEVICE), None),
		"PREVIEW_DEVICE": PREVIEW_DEVICE,
		"CHUNK_SIZE": CHUNK_SIZE,
		"permanent_delete": permanent_delete,
		"AUDIO_MAX_DUR": AUDIO_MAX_DUR
	}
	with open(path, "w", encoding='utf-8') as file:
		file.write(json.dumps(data, indent=4, ensure_ascii=False))

# -------------------

@eel.expose
def change_input_device(new_device):
	global INPUT_DEVICE, stopRecording
	if new_device == "false":
		INPUT_DEVICE = False
	else:
		INPUT_DEVICE = int(new_device)
	stopRecording = True

@eel.expose
def change_output_device(new_device):
	global OUTPUT_DEVICE, stopRecording
	OUTPUT_DEVICE = int(new_device)
	stopRecording = True

@eel.expose
def change_setting(name, value):
	globals()[name] = value
	save_settings()

@eel.expose
def get_settings():
	return {
		"input_device": INPUT_DEVICE,
		"output_device": OUTPUT_DEVICE,
		"PREVIEW_DEVICE": PREVIEW_DEVICE,
		"permanent_delete": permanent_delete,
		"AUDIO_MAX_DUR": AUDIO_MAX_DUR,
		"CHUNK_SIZE": CHUNK_SIZE
	}


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
def search_youtube(text, limit=100, max_dur=AUDIO_MAX_DUR):
	if youtube.findall(text):
		return [get_yt_audio(text)]
	customSearch = CustomSearch(text, VideoDurationFilter.short, limit = limit)
	filtered_by_time = filter(lambda x: time_to_int(x['duration']) < max_dur, customSearch.result()['result'])
	new_arr = map(lambda x: {key: x[key] for key in ["title", "duration", "link"]}, filtered_by_time)
	return list(new_arr)


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
					  output_device_index=OUTPUT_DEVICE,
					  output=True)

		stream_preview = None
		if PREVIEW_DEVICE:
			stream_preview = p.open(format=pyaudio.paInt16,
					  channels=metadata.streaminfo.channels,
					  rate=metadata.streaminfo.sample_rate,
					  output=True)

		chunk = CHUNK_SIZE
		data = output_file.read(chunk)
		while data:
			if stopPlaying:
				break
			stream.write(data)
			if stream_preview:
				stream_preview.write(data)
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
	if INPUT_DEVICE != False:
		p = pyaudio.PyAudio()

		input_stream = p.open(format=pyaudio.paInt16,
					  channels=1,
					  rate=44100,
					  input_device_index=INPUT_DEVICE,
					  input=True)
		output_stream = p.open(format=pyaudio.paInt16,
					  channels=1,
					  rate=44100,
					  output_device_index=OUTPUT_DEVICE,
					  output=True)

		chunk = CHUNK_SIZE
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
		if permanent_delete:
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
