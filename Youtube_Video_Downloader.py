import os
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import yt_dlp
from moviepy import VideoFileClip, AudioFileClip

def check_tkinter():
    try:
        import tkinter
    except ModuleNotFoundError:
        raise ImportError("The 'tkinter' module is not available in this environment.")

check_tkinter()

def make_alpha_numeric(string):
    return ''.join(char for char in string if char.isalnum())

def extract_audio(file_path, output_path):
    try:
        try:
            video = VideoFileClip(file_path)
            audio = video.audio
            audio.write_audiofile(output_path)
            audio.close()
            video.close()
        except OSError:
            audio = AudioFileClip(file_path)
            audio.write_audiofile(output_path)
            audio.close()
    except Exception as e:
        messagebox.showerror("Error", f"Audio extraction failed: {str(e)}")

def download():
    link = url_entry.get()
    download_type = download_type_var.get()
    resolution = resolution_var.get()
    audio_only = audio_var.get()

    if not link:
        messagebox.showwarning("Input Error", "Please enter a valid YouTube URL!")
        return

    # 🔥 Modified line: Added resolution-based format selection
    format_option = 'bestaudio/best' if audio_only else f'bestvideo[height<={resolution.replace("p", "")}]+bestaudio/best'

    options = {
        'format': format_option,
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [lambda d: update_progress(d)],
    }

    folder_name = filedialog.askdirectory(title="Select Download Folder")
    if not folder_name:
        messagebox.showerror("Folder Error", "Please select a valid folder.")
        return

    options['outtmpl'] = os.path.join(folder_name, '%(title)s.%(ext)s')

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            file_path = ydl.prepare_filename(info_dict)

            if audio_only:
                audio_output = os.path.splitext(file_path)[0] + ".mp3"
                extract_audio(file_path, audio_output)
                os.remove(file_path)

        messagebox.showinfo("Success", "Download finished successfully! 🎉")
        progress_label.config(text="Download Complete! 🎉")

    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")

def update_progress(d):
    if d['status'] == 'downloading':
        try:
            percent = float(d['_percent_str'].strip('%').strip())
            progress_bar["value"] = percent
            progress_label.config(text=f"Downloading: {percent:.2f}%")
        except (ValueError, KeyError):
            progress_label.config(text="Downloading: Progress unknown")
    elif d['status'] == 'finished':
        progress_label.config(text="Download complete. Finalizing...")

window = tk.Tk()
window.title("YouTube Video Downloader")
window.geometry("600x400")
window.resizable(True, True)
window.configure(bg="#4CC9FE")

style = ttk.Style()
style.configure("TLabel", background="#4CC9FE", font=("Arial", 12, "bold"))
style.configure("TCheckbutton", background="#4CC9FE", font=("Arial", 12, "bold"))
style.configure("TButton", font=("Arial", 12, "bold"), foreground="black", background="red")
style.map("TButton", background=[("active", "#cc0000")])

entry_font = ("Arial", 12)

url_label = ttk.Label(window, text="Enter YouTube URL:")
url_label.pack(pady=10)

url_entry = ttk.Entry(window, width=50, font=entry_font)
url_entry.pack(pady=10)

download_type_var = tk.StringVar(value="Single Video")
download_type_label = ttk.Label(window, text="Select Download Type:")
download_type_label.pack(pady=5)

download_type_menu = ttk.Combobox(window, textvariable=download_type_var, 
                                values=["Single Video", "Playlist"], font=entry_font)
download_type_menu.pack(pady=5)

resolution_var = tk.StringVar(value="720p")
resolution_label = ttk.Label(window, text="Select Video Resolution:")
resolution_label.pack(pady=5)

resolution_menu = ttk.Combobox(window, textvariable=resolution_var, 
                             values=["2160p", "1440p", "1080p", "720p", "480p", 
                                    "360p", "240p", "144p"], font=entry_font)
resolution_menu.pack(pady=5)

audio_var = tk.BooleanVar()
audio_checkbox = ttk.Checkbutton(window, text="Download Audio Only (MP3)", 
                               variable=audio_var)
audio_checkbox.pack(pady=10)

download_button = ttk.Button(window, text="Download", command=download)
download_button.pack(pady=20)

progress_label = ttk.Label(window, text="Status: Waiting for input...")
progress_label.pack(pady=10)

progress_bar = ttk.Progressbar(window, orient="horizontal", 
                             length=400, mode="determinate")
progress_bar.pack(pady=10)

window.mainloop()