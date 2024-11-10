#!/usr/bin/python3
import sys
sys.path.append('/usr/lib/python3/dist-packages')
sys.path.append('/home/fmeyer/venv/lib/python3.11/site-packages')
import cv2
import threading
import tkinter as tk
from PIL import Image, ImageTk
import paramiko
import ffmpeg
import pyaudio

RTSP_URL1 = 'rtsp://thingino:thingino@192.168.1.160:554/ch0'
RTSP_URL2 = 'rtsp://thingino:thingino@192.168.1.161:554/ch0'

# SSH configuration for each camera
CAM1_SSH = {
    "host": "cam1",
    "username": "root",
}
CAM2_SSH = {
    "host": "cam2",
    "username": "root",
}

# Define SSH commands for each direction
CAMERA_COMMANDS = {
    "up": ". ./camrc && moveY -120",
    "down": ". ./camrc && moveY 120",
    "left": ". ./camrc && moveX -120",
    "right": ". ./camrc && moveX 120",
    "center": ". ./camrc && moveHome"  # Center command
}

# Example list of additional commands for the dropdown
EXTRA_COMMANDS = {
    "IRLed OFF": "irled 0",
    "IRLed ON": "irled 1",
    "IRCut OFF": "ircut 0",
    "IRCut ON": "ircut 1",
    "Color": "color on",
    "BW": "color off",
    "None ": False
}

class VideoStream:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        if not self.cap.isOpened():
            print(f"Failed to open stream: {url}")
        self.frame = None
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=()).start()

    def update(self):
        while not self.stopped:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.frame = frame

    def get_frame(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()

class AudioStream:
    def __init__(self, url):
        self.url = url
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.stopped = False

    def start(self):
        self.stopped = False
        threading.Thread(target=self.play_audio).start()

    def play_audio(self):
        process = (
            ffmpeg.input(self.url)
            .output("pipe:", format="s16le", acodec="pcm_s16le", ac=1, ar="44100")
            .run_async(pipe_stdout=True)
        )
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)

        while not self.stopped:
            audio_data = process.stdout.read(4096)
            if audio_data:
                self.stream.write(audio_data)
            else:
                break

        process.stdout.close()
        self.stream.stop_stream()
        self.stream.close()

    def stop(self):
        self.stopped = True
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()


class VideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RTSP Stream Viewer with Controls")

        # Video streams
        self.stream1 = VideoStream(RTSP_URL1)
        self.stream2 = VideoStream(RTSP_URL2)
        self.stream1.start()
        self.stream2.start()
        # Start audio stream for camera 1
        self.audio_stream = AudioStream(RTSP_URL1)
        self.audio_stream.start()

        # Add Toggle Size and Quit buttons
        toggle_button = tk.Button(root, text="Toggle Size", command=self.toggle_size)
        toggle_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        self.full_size = False

        quit_button = tk.Button(root, text="Quit", command=self.on_closing)
        quit_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        # Display video streams
        self.label1 = tk.Label(root)
        self.label1.grid(row=1, column=0, columnspan=2)
        self.label1.bind("<Button-1>", lambda event: self.handle_click(event, CAM1_SSH, "cam1"))
        self.label1.bind("<Button-3>", lambda event: self.show_context_menu(event, CAM1_SSH))

        self.label2 = tk.Label(root)
        self.label2.grid(row=2, column=0, columnspan=2)
        self.label2.bind("<Button-1>", lambda event: self.handle_click(event, CAM2_SSH, "cam2"))
        self.label2.bind("<Button-3>", lambda event: self.show_context_menu(event, CAM2_SSH))

        # Dropdown menu for additional commands
        self.context_menu = tk.Menu(root, tearoff=0)
        for cmd_name in EXTRA_COMMANDS.keys():
            self.context_menu.add_command(
                label=cmd_name,
                command=lambda cmd=cmd_name: self.send_extra_command(CAM1_SSH, cmd)  # Use CAM1_SSH for demo; you can change it dynamically
            )

        # Update frames on the UI
        self.update_frame()

    def handle_click(self, event, ssh_info, cam_name):
        """Determine which region of the image was clicked and execute the corresponding command."""
        widget = event.widget
        width, height = widget.winfo_width(), widget.winfo_height()

        # Determine clicked region
        if event.x < width // 3:
            command = "left"
        elif event.x > 2 * width // 3:
            command = "right"
        elif event.y < height // 3:
            command = "up"
        elif event.y > 2 * height // 3:
            command = "down"
        else:
            command = "center"

        # Send the appropriate SSH command
        self.send_ssh_command(ssh_info, command)

    def show_context_menu(self, event, ssh_info):
        """Display the dropdown menu on right-click."""
        # Update commands for the specific camera if needed
        for cmd_name in EXTRA_COMMANDS.keys():
            self.context_menu.entryconfig(cmd_name, command=lambda cmd=cmd_name: self.send_extra_command(ssh_info, cmd))

        # Display the context menu
        self.context_menu.post(event.x_root, event.y_root)

    def send_ssh_command(self, ssh_info, direction):
        command = CAMERA_COMMANDS.get(direction)
        if command:
            self.execute_ssh_command(ssh_info, command)

    def send_extra_command(self, ssh_info, cmd_name):
        command = EXTRA_COMMANDS.get(cmd_name)
        if command:
            self.execute_ssh_command(ssh_info, command)

    def execute_ssh_command(self, ssh_info, command):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                hostname=ssh_info["host"],
                username=ssh_info["username"],
            )
            stdin, stdout, stderr = ssh_client.exec_command(command)
            print(stdout.read().decode())
            ssh_client.close()
        except Exception as e:
            print(f"Failed to send command {command} to {ssh_info['host']}: {e}")

    def update_frame(self):
        frame1 = self.stream1.get_frame()
        frame2 = self.stream2.get_frame()

        # Adjust frame sizes based on toggle
        if frame1 is not None:
            frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
            if not self.full_size:
                frame1 = cv2.resize(frame1, (frame1.shape[1] // 2, frame1.shape[0] // 2))
            frame1 = ImageTk.PhotoImage(Image.fromarray(frame1))
            self.label1.configure(image=frame1)
            self.label1.image = frame1

        if frame2 is not None:
            frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            if not self.full_size:
                frame2 = cv2.resize(frame2, (frame2.shape[1] // 2, frame2.shape[0] // 2))
            frame2 = ImageTk.PhotoImage(Image.fromarray(frame2))
            self.label2.configure(image=frame2)
            self.label2.image = frame2

        # Update at 2 FPS (500 ms)
        self.root.after(500, self.update_frame)

    def toggle_size(self):
        self.full_size = not self.full_size

    def on_closing(self):
        self.stream1.stop()
        self.stream2.stop()
        self.root.destroy()

# Run the application
root = tk.Tk()
app = VideoApp(root)
root.protocol("WM_DELETE_WINDOW", app.on_closing)
root.mainloop()

