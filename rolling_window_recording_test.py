import pyaudio
import wave
import os
import threading
import queue
import customtkinter as ctk
from openai import OpenAI
from prompts import whisper_prompt, gpt_system_prompt

# Set the audio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 30

# Set the data directory
DATA_DIR = "data"

# Create the data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    
# Create a queue to store the audio data
audio_queue = queue.Queue()

# Flag to indicate recording status
recording = True

# Global variable for transcript textbox
transcript_textbox = None
def record_audio():
    global recording

    # Create a PyAudio object
    audio = pyaudio.PyAudio()

    # Open the microphone stream
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording started.")

    while recording:
        # Read audio data from the microphone
        data = stream.read(CHUNK)

        # Add the audio data to the queue
        audio_queue.put(data)

        # If the queue size exceeds the desired recording duration, remove the oldest data
        if audio_queue.qsize() > RATE / CHUNK * RECORD_SECONDS:
            audio_queue.get()

    print("Recording stopped.")

    # Close the microphone stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded audio to a file
    save_audio()

def save_audio():
    # Create a unique filename for the audio file
    filename = os.path.join(DATA_DIR, "recording.wav")

    # Create a new wave file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pyaudio.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    # Write the audio data from the queue to the file
    while not audio_queue.empty():
        data = audio_queue.get()
        wf.writeframes(data)

    # Close the wave file
    wf.close()

    print(f"Audio saved as {filename}")

def stop_recording():
    global recording
    recording = False

def transcribe_audio(transcript_textbox):
    # Get the latest recorded audio file
    audio_file_path = os.path.join(DATA_DIR, "recording.wav")

    # Open the audio file
    audio_file = open(audio_file_path, "rb")

    # Create an OpenAI client
    client = OpenAI()

    # Transcribe the audio using the Whisper API
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ru",  # Russian language (ISO-639-1 format)
        prompt=whisper_prompt,  # Guiding prompt for transcription
        temperature=0.2
    )
    
    transcribed_text = transcript.text
    
    # Display the transcribed text in the transcript textbox
    transcript_textbox.delete("1.0", ctk.END)
    transcript_textbox.insert("1.0", transcribed_text)
    
def ask_gpt(prompt, transcribed_text, response_textbox):
    # Create an OpenAI client
    client = OpenAI()

    # Send the transcription to ChatGPT
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcribed_text}
        ]
    )

    # Get the ChatGPT response
    gpt_answer = completion.choices[0].message.content

    # Display the GPT response in the response textbox
    response_textbox.delete("1.0", ctk.END)
    response_textbox.insert("1.0", gpt_answer)

    return gpt_answer

def create_ui_components(root):
    global transcript_textbox, response_textbox
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root.title("Live Call Aide")
    root.configure(bg='#252422')
    root.geometry("1000x600")

    font_size = 20

    # Configure grid weights for adaptive resizing
    root.grid_rowconfigure(0, weight=8)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_columnconfigure(0, weight=35)
    root.grid_columnconfigure(1, weight=65)

    transcript_textbox = ctk.CTkTextbox(root, font=("Arial", font_size), text_color='#FFFCF2', wrap="word")
    transcript_textbox.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")

    response_textbox = ctk.CTkTextbox(root, font=("Arial", font_size), text_color='#639cdc', wrap="word")
    response_textbox.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

    freeze_button = ctk.CTkButton(root, text="Stop", command=stop_recording)
    freeze_button.grid(row=1, column=1, padx=10, pady=3, sticky="nsew")

    transcript_button = ctk.CTkButton(root, text="Transcribe", command=lambda: transcribe_audio(transcript_textbox))
    transcript_button.grid(row=1, column=0, padx=10, pady=3, sticky="nsew")

    ask_gpt_button = ctk.CTkButton(root, text="Ask GPT", command=lambda: ask_gpt(gpt_system_prompt, transcript_textbox.get("1.0", ctk.END), response_textbox))
    ask_gpt_button.grid(row=2, column=0, padx=10, pady=3, sticky="nsew")

# Create the main window
root = ctk.CTk()

# Create the UI components
create_ui_components(root)

# Start the recording thread
recording_thread = threading.Thread(target=record_audio)
recording_thread.start()

# Run the GUI event loop
root.mainloop()

# Wait for the recording thread to finish
recording_thread.join()