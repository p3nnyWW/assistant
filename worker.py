import json
import wave
import pyaudio
import threading
from google.cloud import texttospeech

class PyAudioPlayer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.finished_signal = None

    def start(self):
        threading.Thread(target=self._play_audio, daemon=True).start()

    def _play_audio(self):
        with wave.open(self.file_path, 'rb') as wf:
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            stream.stop_stream()
            stream.close()
            p.terminate()
            self._on_audio_finished()

    def _on_audio_finished(self):
        if self.finished_signal:
            self.finished_signal()

    def set_finished_signal(self, signal_function):
        self.finished_signal = signal_function

class TextToSpeechWorker:
    def __init__(self, text, google_credentials_path, voice_name='en-US-Wavenet-D', language_code='en-US'):
        self.text = text
        self.google_credentials_path = google_credentials_path
        self.voice_name = voice_name
        self.language_code = language_code
        self.success_signal = None
        self.error_signal = None

    def run(self):
        client = texttospeech.TextToSpeechClient.from_service_account_json(self.google_credentials_path)
        synthesis_input = texttospeech.SynthesisInput(text=self.text)
        voice = texttospeech.VoiceSelectionParams(language_code=self.language_code, name=self.voice_name)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        try:
            self._save_audio_file(response.audio_content)
        except Exception as e:
            if self.error_signal:
                self.error_signal(f"Error saving audio file: {e}")

    def _save_audio_file(self, audio_content):
        file_path = "output.wav"
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_content)
        if self.success_signal:
            self.success_signal(file_path)

    def set_success_signal(self, signal_function):
        self.success_signal = signal_function

    def set_error_signal(self, signal_function):
        self.error_signal = signal_function

# Example usage
def play_response(file_path):
    player = PyAudioPlayer(file_path)
    player.start()

def handle_error(error_message):
    print(error_message)

tts_worker = TextToSpeechWorker("Hello world", "path/to/google_credentials.json")
tts_worker.set_success_signal(play_response)
tts_worker.set_error_signal(handle_error)
tts_worker.run()
