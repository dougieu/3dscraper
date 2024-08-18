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

class BitmojiCustomizer:
    def __init__(self, master):
        self.master = master
        self.master.title("Bitmoji Customizer")
        self.master.geometry("600x450")
        self.master.configure(bg="#ffffff")

        # Initialize token variable (this was missing before)
        self.token = tk.StringVar()

        # Set up styles
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Custom style for buttons
        self.style.configure("Custom.TButton", 
                             padding=10, 
                             font=("Helvetica", 12, "bold"), 
                             background="#4CAF50", 
                             foreground="white",
                             borderwidth=0,
                             relief="flat")

        # Button hover effect (changes background color on hover)
        self.style.map("Custom.TButton", 
                       background=[('active', '#45a049')])

        # Custom style for labels
        self.style.configure("Custom.TLabel", 
                             font=("Helvetica", 12, "bold"), 
                             background="#ffffff", 
                             foreground="#333333")

        # Custom style for entry boxes
        self.style.configure("Custom.TEntry", 
                             font=("Helvetica", 12), 
                             padding=5,
                             fieldbackground="#f0f0f0",
                             foreground="#333333")

        # Adding a shadow effect to the main frame
        self.main_frame = ttk.Frame(self.master, padding="20 20 20 20", style="Custom.TFrame")
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.create_widgets()

    def create_widgets(self):
        title_label = ttk.Label(self.main_frame, 
                                text="Bitmoji Customizer", 
                                font=("Helvetica", 24, "bold"), 
                                style="Custom.TLabel")
        title_label.pack(pady=(0, 20))

        token_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        token_frame.pack(fill=tk.X, pady=10)

        ttk.Label(token_frame, 
                  text="Enter Bitmoji Token:", 
                  style="Custom.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        self.token_entry = ttk.Entry(token_frame, 
                                     textvariable=self.token, 
                                     width=40, 
                                     style="Custom.TEntry")
        self.token_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Adding highlight effect when entry is focused
        self.token_entry.bind("<FocusIn>", lambda e: self.token_entry.configure(style="Focused.TEntry"))
        self.token_entry.bind("<FocusOut>", lambda e: self.token_entry.configure(style="Custom.TEntry"))

        ttk.Button(self.main_frame, 
                   text="Enter", 
                   command=self.on_enter, 
                   style="Custom.TButton").pack(pady=20)

    def on_enter(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter a valid token")
            return

        details = self.fetch_bitmoji_details(token)
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
        section_window.geometry("450x400")
        section_window.configure(bg="#ffffff")

        frame = ttk.Frame(section_window, padding="20 20 20 20", style="Custom.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, 
                  text="Select Bitmoji Section", 
                  font=("Helvetica", 18, "bold"), 
                  style="Custom.TLabel").pack(pady=(0, 20))

        ttk.Label(frame, 
                  text="Pick a section:", 
                  style="Custom.TLabel").pack(pady=5)

        section_var = tk.StringVar()
        section_combobox = ttk.Combobox(frame, 
                                        textvariable=section_var, 
                                        state="readonly", 
                                        style="Custom.TCombobox")
        section_combobox['values'] = ['hats', 'tops', 'bottoms', 'glasses', 'outerwear', 'outfits']
        section_combobox.pack(pady=10)

        ttk.Label(frame, 
                  text="Starting number:", 
                  style="Custom.TLabel").pack(pady=5)
        start_entry = ttk.Entry(frame, style="Custom.TEntry")
        start_entry.pack(pady=5)

        ttk.Label(frame, 
                  text="Ending number:", 
                  style="Custom.TLabel").pack(pady=5)
        end_entry = ttk.Entry(frame, style="Custom.TEntry")
        end_entry.pack(pady=5)

        ttk.Button(frame, 
                   text="Check", 
                   command=lambda: self.check_action(section_var.get(), start_entry.get(), end_entry.get(), token, details), 
                   style="Custom.TButton").pack(pady=20)

    def check_action(self, section, start, end, token, details):
        try:
            start = int(start)
            end = int(end)
            if not section or start < 0 or end < start:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid section and range")
            return

        self.fetch_and_display_images(token, details, section[:-1], start, end)

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
        await self.save_bitmoji(token, details, section, details['option_ids'][section])

        # Filter out None values
        valid_images = [img for img in images if img is not None]
        self.display_images(valid_images, token, details, section)

    async def fetch_single_image(self, session, token, details, section, value):
        # Remove outerwear if we're searching for tops
        original_outerwear = None
        if section == 'top':
            original_outerwear = details['option_ids'].get('outerwear')
            details['option_ids']['outerwear'] = 0  # Set outerwear to none

        saved = await self.save_bitmoji(token, details, section, value)
        
        # Restore original outerwear
        if original_outerwear is not None:
            details['option_ids']['outerwear'] = original_outerwear

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
                    messagebox.showerror("Error", f"Failed to save changes for {section} with value {value}: {await response.text()}")
                return await response.json()

    def display_images(self, images, token, details, section):
        if not images:
            messagebox.showinfo("No Images", "No valid images were found for the selected range.")
            return

        image_window = tk.Toplevel(self.master)
        image_window.title("Bitmoji Images")
        image_window.geometry("850x650")
        image_window.configure(bg="#ffffff")

        canvas = tk.Canvas(image_window, bg="#ffffff", highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(image_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        frame = ttk.Frame(canvas, style="Custom.TFrame")
        canvas.create_window((0, 0), window=frame, anchor="nw")

        row = 0
        col = 0
        for img_data, index in images:
            image = Image.open(io.BytesIO(img_data))
            image = image.resize((150, 150), Image.LANCZOS)  # Increased size and made square
            photo = ImageTk.PhotoImage(image)

            button = ttk.Button(frame, 
                                image=photo, 
                                text=f"Option {index}", 
                                compound="top", 
                                command=lambda idx=index: self.set_bitmoji_option(token, details, section, idx), 
                                style="Custom.TButton")
            button.photo = photo
            button.grid(row=row, column=col, padx=15, pady=15)

            col += 1
            if col == 4:  # 4 columns for better layout
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
