import subprocess
import sys
from tkinter import messagebox
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from pytubefix import Playlist, YouTube
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading
import os

class VideoInfo:
    def __init__(self, url, title, duration, thumbnail_url, size):
        self.url = url
        self.title = title
        self.duration = duration
        self.thumbnail_url = thumbnail_url
        self.size = size

class YouTubeDownloader:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title('YouTube Downloader')
        self.app.geometry("600x500")
        self.app._set_appearance_mode("dark")       
        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_rowconfigure(1, weight=1)

        self.videos = []
        self.download_path = ""
        self.current_download = 0
        self.total_downloads = 0

        self.create_widgets()
    
    def show_error(self, message):
        messagebox.showerror("Error", message)

    def create_widgets(self):
        self.url_frame = ctk.CTkFrame(self.app)
        self.url_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.url_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text='Please Enter the URL')
        self.url_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        self.search_button = ctk.CTkButton(self.url_frame, text='Search', fg_color='red',hover_color='dark red', command=self.fetch_info, width=100)
        self.search_button.grid(row=0, column=1, padx=(5, 10), pady=10)

        self.video_display_frame = ctk.CTkScrollableFrame(self.app, width=580, height=400)
        self.video_display_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.download_frame = ctk.CTkFrame(self.app)
        self.download_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.download_frame.grid_columnconfigure(1, weight=1)

        self.progress_label = ctk.CTkLabel(self.download_frame, text="0 / 0 videos")
        self.progress_label.grid(row=0, column=0, padx=(5, 10), pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.download_frame,progress_color='red', width=200)
        self.progress_bar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.progress_bar.set(0)

        self.percentage_label = ctk.CTkLabel(self.download_frame, text="0%")
        self.percentage_label.grid(row=0, column=2, padx=(10, 5), pady=5)

        self.download_button = ctk.CTkButton(self.download_frame, text='Download',fg_color='red',hover_color='dark red', command=self.start_download, width=100)
        self.download_button.grid(row=0, column=3, padx=(5, 10), pady=5)

    def get_video_info(self, url):
        try:
            yt = YouTube(url)
            title = yt.title
            duration = yt.length
            thumbnail_url = yt.thumbnail_url
            size = round((yt.streams.get_highest_resolution(progressive=False).filesize / (1024 * 1024)) + (yt.streams.get_audio_only().filesize / (1024 * 1024)), 2) 
            return VideoInfo(url, title, duration, thumbnail_url, size)
        except Exception as e:
            self.show_error(f"Error retrieving video info: {e}")
            return None

    def display_video_info(self, video_info):
        subframe = ctk.CTkFrame(master=self.video_display_frame)
        subframe.pack(pady=10, fill='x', padx=10)
        subframe.grid_columnconfigure(1, weight=1)

        response = requests.get(video_info.thumbnail_url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img = img.resize((150, 100))
        thumbnail_img = ImageTk.PhotoImage(img)

        thumbnail_label = ctk.CTkLabel(master=subframe, image=thumbnail_img, text="")
        thumbnail_label.image = thumbnail_img
        thumbnail_label.grid(row=0, column=0, rowspan=3, padx=(0, 10), pady=10)

        title_label = ctk.CTkLabel(master=subframe, text=f"Title: {video_info.title}", anchor="w", wraplength=350)
        title_label.grid(row=0, column=1, sticky="w")

        minutes, seconds = divmod(video_info.duration, 60)
        hours, minutes = divmod(minutes, 60)
        duration_formatted = f"Duration: {int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        duration_label = ctk.CTkLabel(master=subframe, text=duration_formatted, anchor="w")
        duration_label.grid(row=1, column=1, sticky="w")

        size_label = ctk.CTkLabel(master=subframe, text=f"Size: {video_info.size} MB", anchor="w")
        size_label.grid(row=2, column=1, sticky="w")

    def process_url(self, url):
        if 'playlist' in url:
            pl = Playlist(url)
            for video_url in pl.video_urls:
                video_info = self.get_video_info(video_url)
                if video_info:
                    self.videos.append(video_info)
        else:
            video_info = self.get_video_info(url)
            if video_info:
                self.videos.append(video_info)

    def show_loading(self, show=True):
        for widget in self.video_display_frame.winfo_children():
            widget.destroy()
        if show:
            loading_label = ctk.CTkLabel(self.video_display_frame, text="Loading...", font=("Arial", 16))
            loading_label.pack(pady=20)

    def fetch_info(self):
        url = self.url_entry.get()
        self.show_loading()
        self.videos.clear()
        
        def task():
            try:
                self.process_url(url)
            finally:
                self.app.after(0, self.display_all_videos)

        threading.Thread(target=task, daemon=True).start()

    def display_all_videos(self):
        self.show_loading(False)
        for video_info in self.videos:
            self.display_video_info(video_info)

    def choose_download_path(self):
        self.download_path = filedialog.askdirectory()
        return self.download_path
    
    def get_resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def start_download(self):
        if not self.choose_download_path():
            return

        self.current_download = 0
        self.total_downloads = len(self.videos)
        self.update_progress_ui(0)
        self.download_button.configure(state="disabled")

        def download_task():
            for video_info in self.videos:
                self.download_video(video_info)
                self.current_download += 1
                self.app.after(0, lambda: self.update_progress_ui(0))
            self.app.after(0, lambda: self.download_button.configure(state="normal"))

        threading.Thread(target=download_task, daemon=True).start()

    def download_video(self, video_info):
        try:
            yt = YouTube(video_info.url, on_progress_callback=self.on_progress)
            
            # Get the highest quality video stream (without audio)
            video_stream = yt.streams.get_highest_resolution(progressive=False)
            
            # Get the highest quality audio stream
            audio_stream = yt.streams.get_audio_only()
            
            if not video_stream or not audio_stream:
                self.show_error(f"No suitable streams found for {video_info.title}")
                return

            # Set the current file size for progress calculation
            self.current_file_size = video_stream.filesize + audio_stream.filesize

            # Download video
            video_filename = f"{video_info.title}_video.mp4"
            video_path = os.path.join(self.download_path, video_filename)
            video_stream.download(output_path=self.download_path, filename=video_filename)

            # Download audio
            audio_filename = f"{video_info.title}_audio.mp4"
            audio_path = os.path.join(self.download_path, audio_filename)
            audio_stream.download(output_path=self.download_path, filename=audio_filename)

            # Combine video and audio using ffmpeg
            output_filename = f"{video_info.title}.mp4"
            output_path = os.path.join(self.download_path, output_filename)
            
            ffmpeg_path = self.get_resource_path(os.path.join('data', 'ffmpeg.exe'))            
            ffmpeg_command = f"{ffmpeg_path} -i \"{video_path}\" -i \"{audio_path}\" -c:v copy -c:a aac \"{output_path}\" "
            subprocess.run(ffmpeg_command, shell=True, check=True)

            # Remove the separate video and audio files
            os.remove(video_path)
            os.remove(audio_path)

            print(f"Successfully downloaded and combined: {video_info.title}")

        except Exception as e:
            self.show_error(f"Error downloading {video_info.title}: {e}")

    def on_progress(self, stream, chunk, bytes_remaining):
        bytes_downloaded = self.current_file_size - bytes_remaining
        percentage = (bytes_downloaded / self.current_file_size) * 100
        self.app.after(0, lambda: self.update_progress_ui(percentage))

    def update_progress_ui(self, percentage):
        self.progress_label.configure(text=f"{self.current_download} / {self.total_downloads} videos")
        self.progress_bar.set(percentage / 100)
        self.percentage_label.configure(text=f"{percentage:.1f}%")

    def start_download(self):
        if not self.choose_download_path():
            return

        self.current_download = 0
        self.total_downloads = len(self.videos)
        self.update_progress_ui(0)
        self.download_button.configure(state="disabled")

        def download_task():
            for video_info in self.videos:
                self.download_video(video_info)
                self.current_download += 1
                self.app.after(0, lambda: self.update_progress_ui(0))
            self.app.after(0, lambda: self.download_button.configure(state="normal"))

        threading.Thread(target=download_task, daemon=True).start()

    def run(self):           
        icon_path = self.get_resource_path('icon.ico')
        try:
            self.app.iconbitmap(icon_path)
        except tk.TclError:
            self.show_error(f"Failed to set icon: {icon_path}")
        
        self.app.mainloop()

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.run()