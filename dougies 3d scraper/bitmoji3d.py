import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
import json
import io
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from ttkbootstrap import Style

class BitmojiCustomizer:
    def __init__(self, master):
        self.master = master
        self.master.title("Bitmoji Customizer")
        self.master.geometry("800x600")
        
        # Apply ttkbootstrap theme
        self.style = Style(theme="darkly")
        
        self.token = tk.StringVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame(self.master, padding="40")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(self.main_frame, 
                                text="Bitmoji Customizer", 
                                font=("Roboto", 36, "bold"),
                                bootstyle="inverse-primary")
        title_label.pack(pady=(0, 30))
        
        # Token entry frame
        token_frame = ttk.Frame(self.main_frame)
        token_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(token_frame, 
                  text="Enter Bitmoji Token:", 
                  font=("Roboto", 14)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.token_entry = ttk.Entry(token_frame, 
                                     textvariable=self.token, 
                                     width=40, 
                                     font=("Roboto", 14))
        self.token_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Enter button
        enter_button = ttk.Button(self.main_frame, 
                                  text="Enter", 
                                  command=self.on_enter,
                                  bootstyle="success-outline",
                                  width=20)
        enter_button.pack(pady=30)
        
        # Add hover effect to button
        enter_button.bind("<Enter>", lambda e: enter_button.configure(bootstyle="success"))
        enter_button.bind("<Leave>", lambda e: enter_button.configure(bootstyle="success-outline"))
        
    def on_enter(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter a valid token")
            return
        
        # Show loading animation
        self.show_loading_animation()
        
        # Fetch Bitmoji details in a separate thread
        self.master.after(100, lambda: self.threaded_fetch_details(token))
        
    def show_loading_animation(self):
        self.loading_window = tk.Toplevel(self.master)
        self.loading_window.title("Loading")
        self.loading_window.geometry("300x100")
        self.loading_window.transient(self.master)
        self.loading_window.grab_set()
        
        loading_label = ttk.Label(self.loading_window, 
                                  text="Fetching Bitmoji details...", 
                                  font=("Roboto", 14))
        loading_label.pack(pady=20)
        
        progress_bar = ttk.Progressbar(self.loading_window, 
                                       mode="indeterminate", 
                                       length=200)
        progress_bar.pack(pady=10)
        progress_bar.start()
        
    def threaded_fetch_details(self, token):
        details = self.fetch_bitmoji_details(token)
        self.loading_window.destroy()
        
        if details:
            self.open_section_selection_window(token, details)
        
    def fetch_bitmoji_details(self, token):
        url = "https://us-east-1-bitmoji.api.snapchat.com/api/avatar-builder-v3/avatar"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US",
            "Bitmoji-Token": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            print(f"Fetched Bitmoji details: {response.status_code}")
            return response.json()
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch Bitmoji details: {str(e)}")
            return None

    def open_section_selection_window(self, token, details):
        section_window = tk.Toplevel(self.master)
        section_window.title("Bitmoji Section Selection")
        section_window.geometry("600x500")
        
        frame = ttk.Frame(section_window, padding="40")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, 
                  text="Select Bitmoji Section", 
                  font=("Roboto", 24, "bold"),
                  bootstyle="inverse-primary").pack(pady=(0, 30))
        
        ttk.Label(frame, 
                  text="Pick a section:", 
                  font=("Roboto", 14)).pack(pady=10)
        
        section_var = tk.StringVar()
        section_combobox = ttk.Combobox(frame, 
                                        textvariable=section_var, 
                                        state="readonly",
                                        values=['hat', 'top', 'bottom', 'glasses', 'outerwear', 'outfit'],
                                        font=("Roboto", 14))
        section_combobox.pack(pady=10)
        
        ttk.Label(frame, 
                  text="Starting number:", 
                  font=("Roboto", 14)).pack(pady=10)
        start_entry = ttk.Entry(frame, font=("Roboto", 14))
        start_entry.pack(pady=5)
        
        ttk.Label(frame, 
                  text="Ending number:", 
                  font=("Roboto", 14)).pack(pady=10)
        end_entry = ttk.Entry(frame, font=("Roboto", 14))
        end_entry.pack(pady=5)
        
        check_button = ttk.Button(frame, 
                                  text="Check", 
                                  command=lambda: self.check_action(section_var.get(), start_entry.get(), end_entry.get(), token, details),
                                  bootstyle="primary-outline",
                                  width=20)
        check_button.pack(pady=30)
        
        # Add hover effect to button
        check_button.bind("<Enter>", lambda e: check_button.configure(bootstyle="primary"))
        check_button.bind("<Leave>", lambda e: check_button.configure(bootstyle="primary-outline"))
        
    def check_action(self, section, start, end, token, details):
        try:
            start = int(start)
            end = int(end)
            if not section or start < 0 or end < start:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid section and range")
            return

        self.fetch_and_display_images(token, details, section, start, end)

    def fetch_and_display_images(self, token, details, section, start, end):
        asyncio.run(self.async_fetch_and_display_images(token, details, section, start, end))

    async def async_fetch_and_display_images(self, token, details, section, start, end):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(start, end + 1):
                task = asyncio.create_task(self.fetch_single_image(session, token, details, section, i))
                tasks.append(task)
                await asyncio.sleep(0.5)  # Delay between requests

            images = await asyncio.gather(*tasks)

        # Restore original Bitmoji
        if section in details['option_ids']:
            await self.save_bitmoji(token, details, section, details['option_ids'][section])
        else:
            print(f"Warning: '{section}' not found in option_ids")

        # Filter out None values
        valid_images = [img for img in images if img is not None]
        self.display_images(valid_images, token, details, section)

    async def fetch_single_image(self, session, token, details, section, value):
        # Remove outerwear if we're searching for tops
        original_outerwear = None
        if section == 'top':
            original_outerwear = details['option_ids'].get('outerwear')
            details['option_ids']['outerwear'] = 0  # Set outerwear to none

        try:
            saved = await self.save_bitmoji(token, details, section, value)
            
            # Restore original outerwear
            if original_outerwear is not None:
                details['option_ids']['outerwear'] = original_outerwear

            if saved is None or 'id' not in saved:
                print(f"Error: 'id' not found in saved response for {section} with value {value}")
                return None

            avatar_id, session_id = saved['id'].split('_')
            session_id = str(int(session_id.split('-')[0]) + 1)
            url = f"https://images.bitmoji.com/3d/avatar/30817224-{avatar_id}_{session_id}-v1.webp?ua=2"

            async with session.get(url) as response:
                if response.status == 200:
                    img_data = await response.read()
                    return (img_data, value)
                else:
                    print(f"Failed to fetch image for option {value}: {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching image for {section} with value {value}: {str(e)}")
            return None

    async def save_bitmoji(self, token, details, section, value):
        url = "https://us-east-1-bitmoji.api.snapchat.com/api/avatar-builder-v3/avatar"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Bitmoji-Token": token,
            "User-Agent": "Mozilla/5.0"
        }
        data = {
            "gender": details["gender"],
            "style": details["style"],
            "mode": "edit",
            "option_ids": details["option_ids"].copy()
        }
        data["option_ids"][section] = value

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                print(f"Saved Bitmoji changes for {section} with value {value}: {response.status}")
                if response.status == 400:
                    error_text = await response.text()
                    print(f"Error saving changes for {section} with value {value}: {error_text}")
                    return None
                return await response.json()

    def display_images(self, images, token, details, section):
        if not images:
            messagebox.showinfo("No Images", "No valid images were found for the selected range.")
            return
        
        image_window = tk.Toplevel(self.master)
        image_window.title("Bitmoji Images")
        image_window.geometry("900x700")
        
        canvas = tk.Canvas(image_window, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(image_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        
        row = 0
        col = 0
        for img_data, index in images:
            image = Image.open(io.BytesIO(img_data))
            image = image.resize((180, 180), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            button = ttk.Button(frame, 
                                image=photo, 
                                text=f"Option {index}", 
                                compound="top", 
                                command=lambda idx=index: self.set_bitmoji_option(token, details, section, idx),
                                bootstyle="light-outline")
            button.photo = photo
            button.grid(row=row, column=col, padx=20, pady=20)
            
            # Add hover effect to button
            button.bind("<Enter>", lambda e, b=button: b.configure(bootstyle="light"))
            button.bind("<Leave>", lambda e, b=button: b.configure(bootstyle="light-outline"))
            
            col += 1
            if col == 4:
                col = 0
                row += 1
        
        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.configure(yscrollcommand=scrollbar.set)
        
    def set_bitmoji_option(self, token, details, section, value):
        asyncio.run(self.save_bitmoji(token, details, section, value))
        messagebox.showinfo("Success", f"Bitmoji updated with option {value} for {section}.")

def main():
    root = tk.Tk()
    app = BitmojiCustomizer(root)
    root.mainloop()

if __name__ == '__main__':
    main()
