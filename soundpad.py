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


__version__ = '0.1.0'

# ---- Required Functions ----

def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(base_path, relative_path)

@eel.expose
def get_version():
	return __version__


CHUNK_SIZE = 2048
permanent_delete = False


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

INPUT_DEVICE = False
OUTPUT_DEVICE = None
PREVIEW_DEVICE = True

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
def toggle_preview(value):
	global PREVIEW_DEVICE
	PREVIEW_DEVICE = value


# --- Search Functions ----
def time_to_int(time_str):
	minutes_str, seconds_str = time_str.split(":")
	minutes = int(minutes_str)
	seconds = int(seconds_str)
	total_seconds = 60 * minutes + seconds
	return total_seconds

def get_yt_audio(link):
	yt = pytube.YouTube(link)
	stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
	return stream.url

@eel.expose
def search_youtube(text, limit=100, max_dur=30):
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
			"duration": '{:02}:{:02}'.format(*divmod(x.get("duration"), 60)),
			"link": f'https://api.meowpad.me/v1/download/{x.get("slug").strip("/")}'
		}, tracks)

		buttonList.extend(tracks)
	return buttonList



@eel.expose
def search_favorites(text):
	def get_durration(f):
		metadata = audio_metadata.load(f)
		return round(metadata.streaminfo.duration)
	folder = os.path.join(os.getcwd(), "downloads")
	files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
	if text:
		filtered = process.extractBests(text, files, score_cutoff=60, limit=10)
		files = list(map(lambda x: x[0], filtered))

	files = map(lambda x: {
			"title": os.path.splitext(x)[0],
			"duration": '{:02}:{:02}'.format(*divmod(get_durration(os.path.join(folder, x)), 60)),
			"link": os.path.join(folder, x),
			"local": True
		}, files)
	return list(files)
# ----------------------------


# --- Play Functions ---------
stopPlaying = False
@eel.expose
def play_sound(file, identifier=None):
	global stopPlaying
	output_file = BytesIO()
	command = ['ffmpeg', '-i', 'pipe:', '-f', 'wav', '-']
	proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate(input=file.read())
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
	youtube = re.compile(r'(https?://)?(www\.)?((youtube\.(com))/watch\?v=([-\w]+)|youtu\.be/([-\w]+))')
	youtubemode = False
	if youtube.findall(url):
		def convert_youtube(link):
			url = get_yt_audio(link)
			r = requests.get(url)
			f = BytesIO(r.content)
			if save:
				save_file(f, filename)
			else:
				play_sound(f, link)
		threading.Thread(target=convert_youtube, args=(url,), daemon=True).start()
	else:
		if os.path.isfile(url):
			with open(url, "rb") as file:
				f = BytesIO(file.read())
		else:
			r = requests.get(url)
			f = BytesIO(r.content)
		if save:
			save_file(f, filename)
		else:
			threading.Thread(target=play_sound, args=(f, url), daemon=True).start()
	
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
def save_file(file, filename):
	folder = os.path.join(os.getcwd(), "downloads")
	if not os.path.exists(folder):
		os.mkdir(folder)
	target = os.path.join(folder, filename)
	def generate_new_file_name(fname):
		if os.path.exists(fname):
			name, extension = os.path.splitext(fname)
			new_name = name + "_1" + extension
			return generate_new_file_name(new_name)
		return fname
	target = generate_new_file_name(target)

	command = ['ffmpeg', '-i', 'pipe:', "-acodec", "copy", '-f', 'mp3', target]
	proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = proc.communicate(input=file.read())
	if proc.returncode != 0:
		print(stderr)


@eel.expose
def save_sound(url, filename):
	play_sound_url(url, save=True, filename=filename + ".mp3")

@eel.expose
def delete_sound(url):
	if os.path.exists(url):
		if permanent_delete:
			os.remove(url)
		else:
			send2trash(url)


eel.init(resource_path("web"))

browsers = ['chrome', 'edge', 'default']
for browser in browsers:
	try:
		threading.Thread(target=listen_micro, daemon=True).start()
		eel.start("main.html", mode=browser)
		break
	except Exception:
		print(f"Failed to launch the app using {browser.title()} browser")
