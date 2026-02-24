import pymem
import customtkinter as ctk
import threading
import time
import json
import os
import datetime
from tkinter import messagebox
import sys

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

CONFIG_FILE = "config.json"
freeze_flag = False

# ================== LOGGING ==================
def log_message(msg):
    if console_box.winfo_exists():
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        console_box.insert("end", timestamp + msg + "\n")
        console_box.see("end")

def clear_console():
    if console_box.winfo_exists():
        console_box.delete("1.0", "end")
        console_box.insert("end", "Console cleared...\n")

# ================== POINTER RESOLVE ==================
def resolve_pointer(pm, base, offsets):
    addr = base
    for off in offsets:
        addr = pm.read_int(addr + off)
    return addr

# ================== FREEZE THREAD ==================
def freeze_value(pm, address):
    global freeze_flag
    while freeze_flag:
        try:
            pm.write_int(address, int(entry_set.get()))
            log_message(f"Freeze: wrote {entry_set.get()} to {hex(address)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            log_message(f"Freeze error: {e}")
            freeze_flag = False
        time.sleep(0.1)

# ================== MAIN LOGIC ==================
def apply_value():
    global freeze_flag
    try:
        process = entry_process.get()
        pm = pymem.Pymem(process)
        log_message(f"Opened process: {process}")

        if checkbox_pointer.get():
            base = pm.process_base.lpBaseOfDll
            offsets = [int(x.strip(), 16) for x in entry_offsets.get().split(",")]
            address = resolve_pointer(pm, base, offsets)
            log_message(f"Using pointer, resolved address = {hex(address)}")
        else:
            address = int(entry_address.get(), 16)
            log_message(f"Using direct address: {hex(address)}")

        value = int(entry_set.get())
        pm.write_int(address, value)
        log_message(f"Wrote value {value} to {hex(address)}")

        if checkbox_freeze.get() and not freeze_flag:
            freeze_flag = True
            threading.Thread(
                target=freeze_value,
                args=(pm, address),
                daemon=True
            ).start()
            log_message("Freeze enabled")
        elif not checkbox_freeze.get():
            freeze_flag = False
            log_message("Freeze disabled")

        label_status.configure(text="✔ Value applied", text_color="lime")

    except Exception as e:
        freeze_flag = False
        messagebox.showerror("Error", str(e))
        log_message(f"Error: {e}")

# ================== SLIDER ==================
def slider_changed(val):
    entry_set.delete(0, "end")
    entry_set.insert(0, str(int(val)))
    log_message(f"Slider changed: {int(val)}")

# ================== SAVE / LOAD ==================
def save_config():
    data = {
        "process": entry_process.get(),
        "address": entry_address.get(),
        "offsets": entry_offsets.get()
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)
    label_status.configure(text="✔ Config saved", text_color="cyan")
    log_message("Config saved")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        entry_process.delete(0, "end")
        entry_process.insert(0, data.get("process", ""))
        entry_address.delete(0, "end")
        entry_address.insert(0, data.get("address", ""))
        entry_offsets.delete(0, "end")
        entry_offsets.insert(0, data.get("offsets", ""))
        log_message("Config loaded")

# ================== LICENSE WINDOW ==================
VALID_LICENSES = ["9F8A-23BC-77DE-AB12-XY99", "7H6K-55LM-88PQ-ZZ11-XY22", "A1B2-C3D4-E5F6-G7H8-I9J0"]
license_verified = False

def check_license():
    global license_verified
    code = entry_license.get().strip()
    if code in VALID_LICENSES:
        license_verified = True
        license_win.destroy()
    else:
        messagebox.showerror("Invalid", "License code is not correct!")

license_win = ctk.CTk()
license_win.title("License Verification")
license_win.geometry("300x150")
ctk.CTkLabel(license_win, text="Enter License Code:", font=("Consolas", 14)).pack(pady=10)
entry_license = ctk.CTkEntry(license_win, width=200)
entry_license.pack(pady=5)
ctk.CTkButton(license_win, text="Verify", command=check_license).pack(pady=10)

def on_close():
    license_win.destroy()

license_win.protocol("WM_DELETE_WINDOW", on_close)
license_win.mainloop()

if not license_verified:
    sys.exit()

# ================== SPLASH ==================
splash = ctk.CTk()
splash.overrideredirect(True)
splash.geometry("300x150+600+300")
ctk.CTkLabel(
    splash,
    text="MEMORY EDITOR",
    font=("Consolas", 24, "bold"),
    text_color="#00ffcc"
).pack(expand=True)

def close_splash():
    if splash.winfo_exists():
        splash.destroy()

splash.after(1500, close_splash)
splash.mainloop()

# ================== UI ==================
app = ctk.CTk()
app.title("Memory Editor Pro")
app.geometry("600x500")
app.resizable(False, False)

# Đặt icon cho cửa sổ từ file icon.ico
app.iconbitmap("icon.ico")

main_frame = ctk.CTkScrollableFrame(app, width=580, height=480)
main_frame.pack(pady=10, fill="both", expand=True)
ctk.CTkLabel(
    main_frame,
    text="MEMORY EDITOR PRO",
    font=("Consolas", 26, "bold"),
    text_color="#00ffcc"
).pack(pady=15)
entry_process = ctk.CTkEntry(main_frame, width=320)
entry_process.pack(pady=5)
entry_process.insert(0, "Process name")
entry_address = ctk.CTkEntry(main_frame, width=320)
entry_address.pack(pady=5)
entry_address.insert(0, "Value address (hex)")

checkbox_pointer = ctk.CTkCheckBox(main_frame, text="Use Pointer")
checkbox_pointer.pack(pady=5)

entry_offsets = ctk.CTkEntry(main_frame, width=320)
entry_offsets.pack(pady=5)
entry_offsets.insert(0, "Offsets (hex, e.g. 0x10,0x20)")

entry_set = ctk.CTkEntry(main_frame, width=200)
entry_set.pack(pady=10)
entry_set.insert(0, "0")

slider = ctk.CTkSlider(
    main_frame,
    from_=0,
    to=99999,
    command=slider_changed,
    width=320
)
slider.pack(pady=10)

checkbox_freeze = ctk.CTkCheckBox(main_frame, text="Freeze value ❄️")
checkbox_freeze.pack(pady=10)

ctk.CTkButton(
    main_frame,
    text="APPLY",
    height=40,
    width=220,
    font=("Consolas", 16, "bold"),
    command=apply_value
).pack(pady=15)

ctk.CTkButton(main_frame, text="Save Config", command=save_config).pack()
ctk.CTkButton(main_frame, text="Load Config", command=load_config).pack(pady=5)

label_status = ctk.CTkLabel(main_frame, text="Waiting...", font=("Consolas", 14))
label_status.pack(pady=10)

console_box = ctk.CTkTextbox(main_frame, width=540, height=120)
console_box.pack(pady=10)
console_box.insert("end", "Console log started...\n")

ctk.CTkButton(main_frame, text="Clear Console", command=clear_console).pack(pady=5)

load_config()
app.mainloop()
