"""
The Python script to get podcast data from given sites and organize it into .csv table
"""
from datetime import date
from typing import Tuple

import scrapetube
from pytube import YouTube


def get_video_data(sources: dict, last_download: date) -> dict:
	"""
	Function to get video's data

	:param sources: Dictionary of channels' urls
	:param last_download: Date of last download
	:return: Dictionary with the channel's name as a key, and list of videos (YouTube objects) as a value
	"""
	url_prefix = "https://www.youtube.com/watch?v="
	videos = {k: [] for k in sources.keys()}
	for ch, url in sources.items():
		vid = scrapetube.get_channel(channel_url=url)
		for v in vid:
			video_url = url_prefix + v["videoId"]
			video = YouTube(video_url)
			publish_day = video.publish_date
			y, m, d = tuple(str(publish_day).split()[0].split('-'))
			publish_day = date(int(y), int(m), int(d))
			if publish_day < last_download:
				break
			videos[ch].append(video)
	return videos


def load_podcast_sources(podcast_sources: str):
	"""
	Function to load podcast sources

	:param podcast_sources: name of the csv file
	:return: list of tuples “podcast_name“, “url“
	"""
	with open(podcast_sources, encoding='utf-8') as f:
		f.readline()
		data = f.readlines()
		data = {el[0]: el[1] for el in [line.strip().split(',') for line in data]}
		return data


def load_internal_data() -> Tuple[date]:
	"""
	Function to load data from previous downloads. If no file found, assumes it's the first time.

	:return: Tuple of that data
	"""
	try:
		with open("internal_data.txt") as f:
			data = f.readlines()
			data = [line.strip().split() for line in data]
			last_download = date(*[int(i) for i in data[0]])
	except Exception:
		last_download = date.today()
	return last_download,


def save_data(videos: dict) -> None:
	"""
	Function to save data to .csv file

	:param videos: Videos to be saved
	"""
	today = date.today()
	with open("output.csv", 'w', encoding='utf-8') as f:
		for ch, vid in videos.items():
			for v in vid:
				y, m, d = tuple(str(v.publish_date).split()[0].split('-'))
				upload_date = date(int(y), int(m), int(d))
				title = v.title.split('|')[0]
				f.write(f"{ch},{title},{upload_date},{today},0:0:{v.length},0\n")
	with open("internal_data.txt", 'w') as f:
		f.write(f"{today.year} {today.month} {today.day}")


def main() -> None:
	"""
	Main function of the script
	"""
	podcast_sources = "podcast_sources.csv"

	sources = load_podcast_sources(podcast_sources)
	last_download, = load_internal_data()
	videos = get_video_data(sources, last_download)
	save_data(videos)


if __name__ == '__main__':
	main()
