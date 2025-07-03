import customtkinter as ctk
import yt_dlp
from PIL import Image, ImageTk
import sqlite3
from tkinter import filedialog, messagebox
import requests
from io import BytesIO
import threading
import os
from datetime import datetime
import hashlib

# Light Theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class LoginWindow:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Video Downloader - Login")
        self.window.geometry("700x750")
        
        # Connect to SQLite
        self.conn = sqlite3.connect('youtube_downloader.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create users table if not exists
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            password TEXT)''')
        self.conn.commit()
        
        # UI Elements
        self.title_label = ctk.CTkLabel(self.window, text="YouTube Video Downloader", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=20)
        
        self.login_frame = ctk.CTkFrame(self.window)
        self.login_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.username_label = ctk.CTkLabel(self.login_frame, text="Username:")
        self.username_label.pack(pady=(10, 0))
        
        self.username_entry = ctk.CTkEntry(self.login_frame)
        self.username_entry.pack(pady=5)
        
        self.password_label = ctk.CTkLabel(self.login_frame, text="Password:")
        self.password_label.pack(pady=(10, 0))
        
        self.password_entry = ctk.CTkEntry(self.login_frame, show="*")
        self.password_entry.pack(pady=5)
        
        self.login_btn = ctk.CTkButton(self.login_frame, text="Login", command=self.login)
        self.login_btn.pack(pady=20)
        
        self.register_btn = ctk.CTkButton(self.login_frame, text="Register", command=self.show_register)
        self.register_btn.pack(pady=5)
        
        # Register Frame (hidden initially)
        self.register_frame = ctk.CTkFrame(self.window)
        
        self.reg_username_label = ctk.CTkLabel(self.register_frame, text="New Username:")
        self.reg_username_label.pack(pady=(10, 0))
        
        self.reg_username_entry = ctk.CTkEntry(self.register_frame)
        self.reg_username_entry.pack(pady=5)
        
        self.reg_password_label = ctk.CTkLabel(self.register_frame, text="New Password:")
        self.reg_password_label.pack(pady=(10, 0))
        
        self.reg_password_entry = ctk.CTkEntry(self.register_frame, show="*")
        self.reg_password_entry.pack(pady=5)
        
        self.confirm_password_label = ctk.CTkLabel(self.register_frame, text="Confirm Password:")
        self.confirm_password_label.pack(pady=(10, 0))
        
        self.confirm_password_entry = ctk.CTkEntry(self.register_frame, show="*")
        self.confirm_password_entry.pack(pady=5)
        
        self.register_submit_btn = ctk.CTkButton(self.register_frame, text="Submit", command=self.register)
        self.register_submit_btn.pack(pady=20)
        
        self.back_to_login_btn = ctk.CTkButton(self.register_frame, text="Back to Login", command=self.show_login)
        self.back_to_login_btn.pack(pady=5)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        hashed_password = self.hash_password(password)
        
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                           (username, hashed_password))
        user = self.cursor.fetchone()
        
        if user:
            self.window.destroy()
            app = YoutubeDownloader(username)
            app.run()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def show_register(self):
        self.login_frame.pack_forget()
        self.register_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.reg_username_entry.focus()
    
    def show_login(self):
        self.register_frame.pack_forget()
        self.login_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.username_entry.focus()
    
    def register(self):
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        hashed_password = self.hash_password(password)
        
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                              (username, hashed_password))
            self.conn.commit()
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login()
            # Clear registration fields
            self.reg_username_entry.delete(0, 'end')
            self.reg_password_entry.delete(0, 'end')
            self.confirm_password_entry.delete(0, 'end')
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
    
    def run(self):
        self.window.mainloop()

class YoutubeDownloader:
    def __init__(self, username):
        self.username = username
        self.window = ctk.CTk()
        self.window.title("YouTube Video Downloader")
        self.window.geometry("700x750")
        
        # Connect to SQLite
        self.conn = sqlite3.connect('youtube_downloader.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                               id INTEGER PRIMARY KEY AUTOINCREMENT, 
                               username TEXT,
                               url TEXT, 
                               title TEXT, 
                               timestamp TEXT)''')
        self.conn.commit()

        # Header Frame with Welcome message and Logout button
        self.header_frame = ctk.CTkFrame(self.window)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        
        self.welcome_label = ctk.CTkLabel(
            self.header_frame, 
            text=f"Welcome {username}", 
            font=("Arial", 14, "bold")
        )
        self.welcome_label.pack(side="left", padx=5)
        
        self.logout_btn = ctk.CTkButton(
            self.header_frame, 
            text="Logout", 
            command=self.logout,
            width=80,
            fg_color="red",
            hover_color="darkred"
        )
        self.logout_btn.pack(side="right", padx=5)

        # UI Elements
        self.url_entry = ctk.CTkEntry(self.window, width=400, placeholder_text="Enter YouTube URL or Playlist")
        self.url_entry.pack(pady=10)

        self.fetch_btn = ctk.CTkButton(self.window, text="Fetch Details", command=self.fetch_details, hover_color="darkred")
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
        self.resolution_drop = ctk.CTkComboBox(self.window, values=["144p", "240p", "360p", "480p", "720p", "1080p"], variable=self.resolution_var)
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

        # History Section
        self.clear_history_btn = ctk.CTkButton(self.window, text="Clear History", command=self.clear_history)
        self.clear_history_btn.pack(pady=5)
        
        self.history_label = ctk.CTkLabel(self.window, text="Download History")
        self.history_label.pack(pady=5)

        self.history_frame = ctk.CTkFrame(self.window, width=400, height=200)
        self.history_frame.pack(pady=5, padx=10, fill="both")

        self.load_history()

    def logout(self):
        self.conn.close()
        self.window.destroy()
        login = LoginWindow()
        login.run()

    def fetch_details(self):
        url = self.url_entry.get()
        if not url:
            self.info_text.set("Please enter a valid URL")
            return

        try:
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(url, download=False)

                title = info.get('title', 'Unknown Title')
                thumbnail_url = info.get('thumbnail', '')
                duration = info.get('duration', 0)  # Duration in seconds

                # Get selected format details
                resolution = self.resolution_var.get()
                audio_only = self.audio_var.get()
                
                selected_format = None
                for fmt in info.get('formats', []):
                    if audio_only and fmt.get('acodec') != 'none':
                        selected_format = fmt
                        break
                    elif fmt.get('height') == int(resolution[:-1]):
                        selected_format = fmt
                        break
                
                # Estimate file size
                file_size = "Unknown"
                if selected_format:
                    if 'filesize' in selected_format and selected_format['filesize']:
                        file_size = f"{round(selected_format['filesize'] / (1024 * 1024), 2)} MB"
                    elif 'tbr' in selected_format and selected_format['tbr']:  # Bitrate-based estimation
                        bitrate_mbps = selected_format['tbr'] / 1000  # Convert from Kbps to Mbps
                        file_size = f"{round((bitrate_mbps * duration) / 8, 2)} MB"

                # Save to SQLite
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute("INSERT INTO history (username, url, title, timestamp) VALUES (?, ?, ?, ?)",
                                    (self.username, url, title, timestamp))
                self.conn.commit()

                self.load_history()
                self.show_thumbnail(thumbnail_url)

                video_info = f"Title: {title}\nURL: {url}\nEstimated Size: {file_size}"
                self.info_text.set(video_info)
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
        except:
            self.thumbnail_label.configure(image='')

    def start_download(self):
        url = self.url_entry.get()
        if not url:
            self.info_text.set("Please enter a valid URL")
            return

        download_dir = filedialog.askdirectory()
        if not download_dir:
            return  # User canceled

        threading.Thread(target=self.download, args=(url, download_dir), daemon=True).start()

    def download(self, url, download_dir):
        try:
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

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0').strip('%')
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

    def load_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        self.cursor.execute("SELECT id, title, url, timestamp FROM history WHERE username = ? ORDER BY id DESC LIMIT 5", (self.username,))
        rows = self.cursor.fetchall()

        if not rows:
            label = ctk.CTkLabel(self.history_frame, text="No history found.", wraplength=350)
            label.pack(pady=2, anchor="w")
            return

        for sr_no, title, url, timestamp in rows:
            formatted_text = (f"Date-Time: {timestamp}\n"
                              f"Title: {title}\n"
                              f"URL: {url}\n"
                              f"{'-'*100}")
            label = ctk.CTkLabel(self.history_frame, text=formatted_text, wraplength=350, justify="left")
            label.pack(pady=5, anchor="w")

    def clear_history(self):
        self.cursor.execute("DELETE FROM history WHERE username = ?", (self.username,))
        self.conn.commit()
        self.load_history()

    def clear(self):
        self.url_entry.delete(0, 'end')
        self.info_text.set("Enter a YouTube URL to fetch details")
        self.thumbnail_label.configure(image='')
        self.progress_label.configure(text="Status: Waiting...")
        self.progress_bar.set(0)

    def run(self):
        self.window.mainloop()
        self.conn.close()

if __name__ == "__main__":
    login = LoginWindow()
    login.run()