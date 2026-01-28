import tkinter as tk
import time
import threading
import pystray
from PIL import Image, ImageDraw

# ================= THEME =================
DARK_BG = "#0F0F0F"
DARK_MAIN = "#E0E0E0"
DARK_SUB = "#AAAAAA"

LIGHT_BG = "#F5F5F5"
LIGHT_MAIN = "#1A1A1A"
LIGHT_SUB = "#666666"

TRANSPARENT_ALPHA = 0.92
# ========================================

is_dark = True
mode = "clock"  # clock | stopwatch | timer
running = False
stopwatch_time = 0.0
timer_seconds = 0

tray_icon = None

# ---------- Tray icon ----------
def create_image():
    img = Image.new("RGB", (64, 64), (0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), outline="white", width=4)
    d.line((32, 32, 32, 16), fill="white", width=3)
    d.line((32, 32, 44, 32), fill="white", width=3)
    return img

# ---------- Tray functions ----------
def restore_from_tray(icon=None, item=None):
    root.after(0, lambda: [
        root.deiconify(),
        root.lift(),
        root.focus_force(),
        root.attributes("-alpha", TRANSPARENT_ALPHA)
    ])

def minimize_to_tray():
    root.withdraw()  

def quit_app(icon=None, item=None):
    global running
    running = False
    if tray_icon:
        tray_icon.stop()
    root.after(0, root.destroy)

def setup_tray():
    global tray_icon
    if tray_icon:
        return
    tray_icon = pystray.Icon(
        "desktop-clock",
        create_image(),
        "Desktop Clock",
        pystray.Menu(
            pystray.MenuItem("Show Clock", restore_from_tray),
            pystray.MenuItem("Quit", quit_app)
        )
    )
    tray_icon.run_detached()  

# ---------- CORE ----------
def update_clock():
    if mode == "clock" and root.winfo_exists():
        time_label.config(text=time.strftime("%H:%M"))
        sub_label.config(text=time.strftime("%a, %d %b %Y"))
    if root.winfo_exists():
        root.after(1000, update_clock)

def toggle_theme(event=None):
    global is_dark
    is_dark = not is_dark
    bg = LIGHT_BG if is_dark else DARK_BG
    main = LIGHT_MAIN if is_dark else DARK_MAIN
    sub = LIGHT_SUB if is_dark else DARK_SUB

    root.config(bg=bg)
    container.config(bg=bg)
    time_label.config(bg=bg, fg=main)
    sub_label.config(bg=bg, fg=sub)
    control_label.config(bg=bg, fg=sub)

# ---------- MODES ----------
def update_control_label():
    if mode == "clock":
        control_label.config(text="Double-click = Theme • Right-click = Next mode")
    else:
        control_label.config(text="Left-click = Start / Stop • Right-click = Reset")

def switch_mode(event=None):
    global mode, running, stopwatch_time, timer_seconds
    running = False
    stopwatch_time = 0.0
    timer_seconds = 0
    if mode == "clock":
        mode = "stopwatch"
        time_label.config(text="00:00.0")
        sub_label.config(text="Stopwatch")
    elif mode == "stopwatch":
        mode = "timer"
        time_label.config(text="05:00")
        sub_label.config(text="Timer • 5 min")
    else:
        mode = "clock"
    update_control_label()

# ---------- STOPWATCH ----------
def stopwatch_loop():
    global stopwatch_time
    while running and mode == "stopwatch" and root.winfo_exists():
        stopwatch_time += 0.1
        m = int(stopwatch_time // 60)
        s = stopwatch_time % 60
        time_label.config(text=f"{m:02d}:{s:05.1f}")
        time.sleep(0.1)

# ---------- TIMER ----------
def timer_loop():
    global timer_seconds, running
    while running and timer_seconds > 0 and mode == "timer" and root.winfo_exists():
        m, s = divmod(timer_seconds, 60)
        time_label.config(text=f"{m:02d}:{s:02d}")
        time.sleep(1)
        timer_seconds -= 1
    if timer_seconds <= 0 and mode == "timer" and running:
        time_label.config(text="⏰ FINISH!")
        running = False

# ---------- INPUT ----------
def on_left_click(event):
    global running, timer_seconds
    if mode == "clock":
        return
    running = not running
    if running:
        if mode == "stopwatch":
            threading.Thread(target=stopwatch_loop, daemon=True).start()
        elif mode == "timer":
            if timer_seconds == 0:
                timer_seconds = 300
            threading.Thread(target=timer_loop, daemon=True).start()
    update_control_label()

def on_right_click(event):
    global running, stopwatch_time, timer_seconds
    running = False
    if mode == "clock":
        switch_mode()
    else:
        stopwatch_time = 0.0
        timer_seconds = 0
        time_label.config(text="00:00.0" if mode == "stopwatch" else "05:00")
    update_control_label()

# ---------- WINDOW ----------
root = tk.Tk()
root.geometry("280x220")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", TRANSPARENT_ALPHA)
root.config(bg=DARK_BG)

# Drag
def start_drag(e):
    root.x, root.y = e.x, e.y

def drag(e):
    root.geometry(f"+{root.winfo_x() + e.x - root.x}+{root.winfo_y() + e.y - root.y}")

root.bind("<ButtonPress-1>", start_drag)
root.bind("<B1-Motion>", drag)

# Close → minimize to tray
def on_close():
    minimize_to_tray()

root.protocol("WM_DELETE_WINDOW", on_close)

container = tk.Frame(root, bg=DARK_BG)
container.pack(expand=True, fill="both", padx=14, pady=14)

# Buttons bar
btn_frame = tk.Frame(container, bg=DARK_BG)
btn_frame.pack(fill="x", pady=(4,6))

# − = ซ่อนไป tray (เสถียร ไม่ error)
tk.Button(btn_frame, text="−", font=("Segoe UI", 12, "bold"),
          bg=DARK_BG, fg="#FFBD2E", bd=0,
          command=minimize_to_tray).pack(side="right", padx=4)

# × = ปิดโปรแกรมจริง ๆ
tk.Button(btn_frame, text="×", font=("Segoe UI", 12, "bold"),
          bg=DARK_BG, fg="#FF5F56", bd=0,
          command=quit_app).pack(side="right")

# ↻ = เปลี่ยนโหมด
tk.Button(btn_frame, text="↻", font=("Segoe UI", 11),
          bg=DARK_BG, fg=DARK_SUB, bd=0, command=switch_mode).pack(side="left", padx=4)

time_label = tk.Label(container, font=("Segoe UI", 46, "bold"), bg=DARK_BG, fg=DARK_MAIN)
time_label.pack(pady=(0,0))

sub_label = tk.Label(container, font=("Segoe UI", 12), bg=DARK_BG, fg=DARK_SUB)
sub_label.pack(pady=(0,4))

control_label = tk.Label(container, font=("Segoe UI", 9), bg=DARK_BG, fg=DARK_SUB)
control_label.pack(pady=6)

# Gestures
root.bind("<Double-Button-1>", toggle_theme)
root.bind("<Button-3>", on_right_click)

for w in (time_label, sub_label, control_label, container):
    w.bind("<Button-1>", on_left_click)

# Hotkeys
root.bind("<Escape>", lambda e: quit_app())
root.bind("<Control-q>", lambda e: quit_app())

update_control_label()
update_clock()

# Start tray
threading.Thread(target=setup_tray, daemon=True).start()

root.mainloop()