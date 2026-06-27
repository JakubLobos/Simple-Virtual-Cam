import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import platform
import os
import imageio
import pyvirtualcam

SYSTEM = platform.system()

def get_backend():
    if SYSTEM in ("Windows", "Darwin"):
        return "obs"
    return "v4l2loopback"

def format_size(path):
    try:
        size = os.path.getsize(path)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"
    except Exception:
        return ""

def get_video_info(path):
    try:
        reader = imageio.get_reader(path)
        meta = reader.get_meta_data()
        reader.close()
    except Exception:
        return None
    w, h = meta.get("size", (0, 0))
    fps = meta.get("fps", 0)
    duration = meta.get("duration", 0)
    mins = int(duration // 60)
    secs = int(duration % 60)
    return {"res": f"{w}×{h}", "fps": f"{fps:.0f} fps", "dur": f"{mins}:{secs:02d}", "size": format_size(path)}


BG       = "#0f1117"
SURFACE  = "#1a1d27"
SURFACE2 = "#22263a"
BORDER   = "#2e3350"
TEXT     = "#e8eaf6"
MUTED    = "#6b7280"
ACCENT   = "#6366f1"
ACCENT_H = "#818cf8"
SUCCESS  = "#22c55e"
DANGER   = "#ef4444"


class VirtualCamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VirtualCam")
        self.root.geometry("460x520")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.video_path = None
        self.running = False
        self.thread = None
        self._dot_count = 0
        self._dot_job = None

        self._build_ui()

    def _build_ui(self):
        root = self.root

        # Header
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=28, pady=(28, 0))

        tk.Label(header, text="VirtualCam", font=("Segoe UI", 22, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Stream any video as a webcam",
                 font=("Segoe UI", 11), bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 0))

        # Divider
        tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=20)

        # Drop zone / file picker
        self.drop_frame = tk.Frame(root, bg=SURFACE, highlightbackground=BORDER,
                                   highlightthickness=1)
        self.drop_frame.pack(fill="x", padx=28, pady=(0, 16))

        self.drop_inner = tk.Frame(self.drop_frame, bg=SURFACE)
        self.drop_inner.pack(fill="x", padx=20, pady=20)

        self.file_icon = tk.Label(self.drop_inner, text="⬜", font=("Segoe UI", 28),
                                  bg=SURFACE, fg=MUTED)
        self.file_icon.pack()

        self.file_label = tk.Label(self.drop_inner, text="No file selected",
                                   font=("Segoe UI", 13, "bold"), bg=SURFACE, fg=TEXT)
        self.file_label.pack(pady=(6, 2))

        self.file_meta = tk.Label(self.drop_inner, text="MP4, AVI, MOV, MKV, WEBM",
                                  font=("Segoe UI", 10), bg=SURFACE, fg=MUTED)
        self.file_meta.pack()

        btn_frame = tk.Frame(self.drop_inner, bg=SURFACE)
        btn_frame.pack(pady=(14, 0))

        self.pick_btn = tk.Button(btn_frame, text="Choose file",
                                  font=("Segoe UI", 10), bg=SURFACE2, fg=TEXT,
                                  activebackground=BORDER, activeforeground=TEXT,
                                  relief="flat", padx=18, pady=7, cursor="hand2",
                                  command=self.choose_file,
                                  highlightbackground=BORDER, highlightthickness=1)
        self.pick_btn.pack()

        # Info cards
        self.cards_frame = tk.Frame(root, bg=BG)
        self.cards_frame.pack(fill="x", padx=28, pady=(0, 16))

        self.card_res  = self._info_card(self.cards_frame, "Resolution", "—")
        self.card_fps  = self._info_card(self.cards_frame, "FPS", "—")
        self.card_dur  = self._info_card(self.cards_frame, "Duration", "—")
        self.card_size = self._info_card(self.cards_frame, "Size", "—")

        for card in (self.card_res, self.card_fps, self.card_dur, self.card_size):
            card[0].pack(side="left", expand=True, fill="both", padx=(0, 8))
        self.card_size[0].pack(side="left", expand=True, fill="both", padx=0)

        # Stream button
        self.stream_btn = tk.Button(root, text="▶   Start streaming",
                                    font=("Segoe UI", 13, "bold"),
                                    bg=ACCENT, fg="white",
                                    activebackground=ACCENT_H, activeforeground="white",
                                    relief="flat", padx=0, pady=14, cursor="hand2",
                                    command=self.toggle)
        self.stream_btn.pack(fill="x", padx=28, pady=(0, 16))

        # Status bar
        status_bar = tk.Frame(root, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        status_bar.pack(fill="x", padx=28, pady=(0, 28))

        self.status_dot = tk.Label(status_bar, text="●", font=("Segoe UI", 10),
                                   bg=SURFACE, fg=MUTED)
        self.status_dot.pack(side="left", padx=(14, 6), pady=10)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status_bar, textvariable=self.status_var,
                 font=("Segoe UI", 10), bg=SURFACE, fg=MUTED).pack(side="left", pady=10)

        self.device_var = tk.StringVar(value="")
        tk.Label(status_bar, textvariable=self.device_var,
                 font=("Segoe UI", 10, "bold"), bg=SURFACE, fg=ACCENT).pack(side="right", padx=14, pady=10)

    def _info_card(self, parent, label, value):
        frame = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(frame, text=label, font=("Segoe UI", 9), bg=SURFACE, fg=MUTED).pack(pady=(10, 2))
        val_lbl = tk.Label(frame, text=value, font=("Segoe UI", 11, "bold"), bg=SURFACE, fg=TEXT)
        val_lbl.pack(pady=(0, 10))
        return frame, val_lbl

    def _set_card(self, card, value):
        card[1].config(text=value)

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Choose video file",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"), ("All files", "*.*")]
        )
        if not path:
            return
        self.video_path = path
        name = os.path.basename(path)
        self.file_label.config(text=name if len(name) <= 36 else name[:33] + "…")
        self.file_icon.config(text="🎬", fg=ACCENT)
        self.file_meta.config(text="Video file loaded")

        info = get_video_info(path)
        if info:
            self._set_card(self.card_res,  info["res"])
            self._set_card(self.card_fps,  info["fps"])
            self._set_card(self.card_dur,  info["dur"])
            self._set_card(self.card_size, info["size"])

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if not self.video_path:
            messagebox.showwarning("No file", "Choose a video file first.")
            return
        self.running = True
        self.stream_btn.config(text="⏹   Stop streaming", bg=DANGER, activebackground="#dc2626")
        self.status_dot.config(fg=SUCCESS)
        self.status_var.set("Starting")
        self._animate_dots()
        self.thread = threading.Thread(target=self.stream_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self._dot_job:
            self.root.after_cancel(self._dot_job)
            self._dot_job = None
        self.stream_btn.config(text="▶   Start streaming", bg=ACCENT, activebackground=ACCENT_H)
        self.status_dot.config(fg=MUTED)
        self.status_var.set("Stopped")
        self.device_var.set("")

    def _animate_dots(self):
        if not self.running:
            return
        dots = "." * (self._dot_count % 4)
        current = self.status_var.get().rstrip(".")
        if current in ("Starting", "Streaming"):
            pass
        self._dot_count += 1
        self._dot_job = self.root.after(500, self._animate_dots)

    def stream_loop(self):
        backend = get_backend()
        try:
            reader = imageio.get_reader(self.video_path)
            meta = reader.get_meta_data()
            reader.close()
            width, height = meta.get("size")
            fps = meta.get("fps") or 30
        except Exception:
            self.root.after(0, lambda: messagebox.showerror("Error", "Cannot open video file."))
            self.root.after(0, self.stop)
            return

        try:
            with pyvirtualcam.Camera(width=width, height=height, fps=fps, backend=backend) as cam:
                device = cam.device
                self.root.after(0, lambda: self.status_var.set("Streaming"))
                self.root.after(0, lambda: self.device_var.set(device))
                while self.running:
                    reader = imageio.get_reader(self.video_path)
                    for frame in reader:
                        if not self.running:
                            break
                        if frame.shape[-1] == 4:
                            frame = frame[:, :, :3]
                        cam.send(frame)
                        cam.sleep_until_next_frame()
                    reader.close()
        except Exception as e:
            hints = {
                "Linux":  "Install v4l2loopback:\n  sudo apt install v4l2loopback-dkms\n  sudo modprobe v4l2loopback",
                "Darwin": "Install OBS Studio and start Virtual Camera once from OBS to register the driver.",
                "Windows":"Make sure OBS Studio is installed (the driver must be present).",
            }
            hint = hints.get(SYSTEM, "")
            msg = f"{e}\n\n{hint}"
            self.root.after(0, lambda: messagebox.showerror("Driver error", msg))
            self.root.after(0, self.stop)

    def on_close(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualCamApp(root)
    root.mainloop()
