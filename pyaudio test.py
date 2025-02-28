import pyaudio
import wave
import numpy as np
import queue
import threading
import time
import os

# Constants for audio processing
RATE = 48000  # Sample rate expected by Whisper
CHUNK = 1024  # Samples per buffer
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 1  # Mono audio for speech recognition
BUFFER_SECONDS = 2  # Process 2-second chunks for real-time performance

class AudioTranscriptionSystem:
    def __init__(self, input_device_index=None):
        """Initialize the audio transcription system.
        
        Args:
            input_device_index: Optional index of input device to use.
                                If None, system default is used.
        """
        self.audio_queue = queue.Queue()
        self.p = pyaudio.PyAudio()
        self.input_device_index = input_device_index
        self.running = False
        
    def list_input_devices(self):
        """List all available input devices to help with selection.
        
        Returns:
            Dictionary mapping device indices to device names.
        """
        info = {}
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # If it has input channels
                info[i] = device_info['name']
        return info
        
    def start_capture(self, duration=None):
        """Start audio capture in a separate thread.
        
        Args:
            duration: Optional duration in seconds to capture audio.
                     If None, captures until stop_capture is called.
        """
        self.running = True
        self.duration = duration
        self.start_time = time.time()
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_audio)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_audio)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def stop_capture(self):
        """Stop audio capture and processing."""
        self.running = False
        # Signal the process thread to finish
        if hasattr(self, 'audio_queue'):
            # Add a None item as sentinel to unblock the processing thread if it's waiting
            self.audio_queue.put(None)
        # Allow time for threads to recognize the running flag has changed
        time.sleep(0.5)
        # Join threads with longer timeout to ensure they exit
        if hasattr(self, 'capture_thread') and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        if hasattr(self, 'process_thread') and self.process_thread.is_alive():
            self.process_thread.join(timeout=2.0)
        self.p.terminate()
        
    def _capture_audio(self):
        """Continuously capture audio and add to queue."""
        # Open the audio stream
        stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK
        )
        
        # Calculate how many chunks make up our buffer size
        buffer_chunks = int(RATE / CHUNK * BUFFER_SECONDS)
        audio_buffer = []
        
        print("Starting audio capture...")
        
        try:
            while self.running:
                # Check if we've exceeded the requested duration
                if self.duration and (time.time() - self.start_time) > self.duration:
                    self.running = False
                    break
                
                # Read audio data from the stream
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_buffer.append(data)
                
                # When buffer reaches desired size, add to queue and reset
                if len(audio_buffer) >= buffer_chunks:
                    self.audio_queue.put(b''.join(audio_buffer))
                    audio_buffer = []  # Start a new buffer
                    
            # Add any remaining audio in buffer
            if audio_buffer:
                self.audio_queue.put(b''.join(audio_buffer))
                
        except Exception as e:
            print(f"Error during audio capture: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            print("Audio capture stopped.")
    
    def _process_audio(self):
        """Process audio chunks from queue and save to WAV file."""
        # Create a list to store all audio chunks
        all_audio_chunks = []
        
        print("Starting audio processing...")
        
        try:
            while self.running or not self.audio_queue.empty():
                try:
                    # Get audio data from queue with timeout
                    audio_data = self.audio_queue.get(timeout=1)
                    
                    # Check if this is our sentinel value
                    if audio_data is None:
                        self.audio_queue.task_done()
                        break
                        
                    # Add to our collection of all chunks
                    all_audio_chunks.append(audio_data)
                    
                    # Here you would normally send to Whisper and then Zoom
                    # For now, we're just collecting the audio
                    if self.running:  # Only print if still running
                        print(f"Processed audio chunk of {len(audio_data)} bytes")
                    
                    # Mark task as done
                    self.audio_queue.task_done()
                    
                except queue.Empty:
                    # No data available, just continue
                    continue
                    
            # After all audio is collected, save to WAV file
            if all_audio_chunks:
                output_path = "output.wav"
                with wave.open(output_path, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(self.p.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(all_audio_chunks))
                
                print(f"Saved audio to {os.path.abspath(output_path)}")
                
        except Exception as e:
            if self.running:  # Only print if still running
                print(f"Error during audio processing: {e}")
            
        if self.running:  # Only print if still running
            print("Audio processing completed.")

# Example usage
if __name__ == "__main__":
    audio_system = None
    try:
        # Create the audio system
        audio_system = AudioTranscriptionSystem()
        
        # List available input devices
        devices = audio_system.list_input_devices()
        print("Available input devices:")
        for idx, name in devices.items():              
            print(f"{idx}: {name}")
            
        # Select a specific device
        device_index = int(input("Enter the number of the device to use: "))
        audio_system = AudioTranscriptionSystem(input_device_index=device_index)
        
        # Start capture for 5 seconds
        duration = 10
        print(f"Recording {duration} seconds of audio...")
        audio_system.start_capture(duration=duration)
        
        # Wait for the recording to complete
        start_time = time.time()
        while audio_system.running:
            elapsed = time.time() - start_time
            remaining = max(0, duration - elapsed)
            print(f"\rRecording: {elapsed:.1f}s / {duration}s (remaining: {remaining:.1f}s)", end="")
            time.sleep(0.1)
        
        print("\nRecording complete. Processing audio...")
        
        # Ensure proper shutdown
        audio_system.stop_capture()
        
        print("Done! Check output.wav for the recorded audio.")
        
    except KeyboardInterrupt:
        print("\nRecording interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Always ensure we stop the system properly
        if audio_system is not None:
            audio_system.stop_capture()