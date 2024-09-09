import pyaudio
import wave
import os
import threading
import queue

# Set the audio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

# Set the data directory
DATA_DIR = "data"

# Create the data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Create a queue to store the audio data
audio_queue = queue.Queue()

# Flag to indicate recording status
recording = True

def record_audio():
    global recording

    # Create a PyAudio object
    audio = pyaudio.PyAudio()

    # Open the microphone stream
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording started. Press 'stop' to stop recording.")

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

# Start the recording thread
recording_thread = threading.Thread(target=record_audio)
recording_thread.start()

# Wait for the 'stop' command
while True:
    command = input().lower()
    if command == 'stop':
        recording = False
        break

# Wait for the recording thread to finish
recording_thread.join()