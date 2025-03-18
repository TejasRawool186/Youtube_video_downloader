import customtkinter as ctk
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading
import yt_dlp
import os
from tkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class YoutubeDownloader:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Downloader")
        self.window.geometry("500x600")
        
        # URL Entry
        self.url_entry = ctk.CTkEntry(self.window, width=400, placeholder_text="Enter YouTube URL or Playlist")
        self.url_entry.pack(pady=10)
        
        # UI elements
        self.fetch_btn = ctk.CTkButton(self.window, text="Fetch Details", command=self.fetch_details)
        self.fetch_btn.pack(pady=5)
        
        self.info_text = ctk.StringVar(value="Enter a YouTube URL to fetch details")
        self.info_label = ctk.CTkLabel(self.window, textvariable=self.info_text, wraplength=400)
        self.info_label.pack(pady=5)
        
        self.thumbnail_label = ctk.CTkLabel(self.window, text="")
        self.thumbnail_label.pack()
        
        self.audio_var = ctk.BooleanVar(value=False)
        self.audio_check = ctk.CTkCheckBox(self.window, text="Audio Only", variable=self.audio_var)
        self.audio_check.pack(pady=5)
        
        self.resolution_var = ctk.StringVar(value="720p")
        self.resolution_drop = ctk.CTkComboBox(self.window, 
                                            values=["144p", "240p", "360p", "480p", "720p", "1080p"],
                                            variable=self.resolution_var)
        self.resolution_drop.pack(pady=5)
        
        self.download_btn = ctk.CTkButton(self.window, text="Download", command=self.start_download)
        self.download_btn.pack(pady=5)
        
        self.progress_label = ctk.CTkLabel(self.window, text="Status: Waiting...")
        self.progress_label.pack()
        
        self.progress_bar = ctk.CTkProgressBar(self.window)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill='x', padx=20, pady=5)
        
        self.clear_btn = ctk.CTkButton(self.window, text="Clear", command=self.clear)
        self.clear_btn.pack(pady=5)
        
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.progress_hook],
        }

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip('%')
            try:
                progress = float(percent)/100
                self.window.after(0, self.update_progress, progress, percent)
            except:
                pass
        elif d['status'] == 'finished':
            self.window.after(0, self.complete_download)

    def update_progress(self, progress, percent):
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Downloading: {percent}%")

    def complete_download(self):
        self.progress_label.configure(text="Download complete!")
        self.progress_bar.set(1.0)

    def fetch_details(self):
        url = self.url_entry.get()
        if not url:
            self.info_text.set("Please enter a valid URL")
            return
            
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:  # Playlist
                    playlist_info = f"Playlist: {info['title']}\nVideos: {len(info['entries'])}"
                    self.info_text.set(playlist_info)
                    if info['entries']:
                        self.show_thumbnail(info['entries'][0]['thumbnail'])
                else:  # Single video
                    video_info = (f"Title: {info['title']}\n"
                                f"Channel: {info['uploader']}\n"
                                f"Duration: {info['duration_string']}")
                    self.info_text.set(video_info)
                    self.show_thumbnail(info['thumbnail'])
                    
        except Exception as e:
            self.info_text.set(f"Error: {str(e)}")
            
    def show_thumbnail(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img = img.resize((200, 150), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.thumbnail_label.configure(image=img_tk)
                self.thumbnail_label.image = img_tk
        except Exception as e:
            self.thumbnail_label.configure(image='')

    def start_download(self):
        url = self.url_entry.get()
        if not url:
            self.info_text.set("Please enter a valid URL")
            return
        
        # Ask for download directory
        download_dir = filedialog.askdirectory()
        if not download_dir:
            return  # User canceled
        
        threading.Thread(target=self.download, args=(url, download_dir), daemon=True).start()
        
    def download(self, url, download_dir):
        try:
            # Create directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            
            options = {
                'format': self.get_format(),
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'noplaylist': False,
                'ignoreerrors': True
            }
            
            with yt_dlp.YoutubeDL(options) as ydl:
                self.window.after(0, self.update_progress, 0, "0%")
                ydl.download([url])
                
        except Exception as e:
            self.window.after(0, lambda: self.info_text.set(f"Download error: {str(e)}"))
        
    def get_format(self):
        if self.audio_var.get():
            return 'bestaudio/best'
        resolution = self.resolution_var.get()
        return f'bestvideo[height<={resolution[:-1]}]+bestaudio/best[height<={resolution[:-1]}]'
        
    def clear(self):
        self.url_entry.delete(0, 'end')
        self.info_text.set("Enter a YouTube URL to fetch details")
        self.thumbnail_label.configure(image='')
        self.progress_label.configure(text="Status: Waiting...")
        self.progress_bar.set(0)
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = YoutubeDownloader()
    app.run()