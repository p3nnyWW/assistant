from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit, QTextEdit, QFileDialog, QComboBox
import sys
import requests
import sounddevice as sd
import numpy as np
import threading

class TranscriptionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Transcription")
        self.setGeometry(100, 100, 800, 600)

        self.recording = False
        self.audio_data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setup_audio_input_widgets(layout)
        self.setup_language_widgets(layout)
        self.setup_transcription_widgets(layout)
        self.setup_translation_widget(layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def setup_audio_input_widgets(self, layout):
        self.audio_input_label = QLabel("Select Audio Input:")
        self.audio_input_dropdown = QComboBox()
        self.audio_input_dropdown.addItem("File", "file")
        self.audio_input_dropdown.addItem("Microphone", "microphone")
        self.audio_input_dropdown.currentIndexChanged.connect(self.on_audio_input_change)

        self.audio_file_path_label = QLabel("Audio File Path:")
        self.audio_file_path_input = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)

        self.start_recording_button = QPushButton("Start Recording")
        self.start_recording_button.clicked.connect(self.start_recording)
        self.stop_recording_button = QPushButton("Stop Recording")
        self.stop_recording_button.clicked.connect(self.stop_recording)

        layout.addWidget(self.audio_input_label)
        layout.addWidget(self.audio_input_dropdown)
        layout.addWidget(self.audio_file_path_label)
        layout.addWidget(self.audio_file_path_input)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.start_recording_button)
        layout.addWidget(self.stop_recording_button)

        self.audio_file_path_label.hide()
        self.audio_file_path_input.hide()
        self.browse_button.hide()
        self.start_recording_button.hide()
        self.stop_recording_button.hide()

    def setup_language_widgets(self, layout):
        self.language_label = QLabel("Select Language:")
        self.language_dropdown = QComboBox()
        self._populate_languages()

        layout.addWidget(self.language_label)
        layout.addWidget(self.language_dropdown)

    def setup_transcription_widgets(self, layout):
        self.transcribe_button = QPushButton("Transcribe")
        self.transcribe_button.clicked.connect(self.transcribe_audio)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        layout.addWidget(self.transcribe_button)
        layout.addWidget(self.result_text)

    def setup_translation_widget(self, layout):
        self.translate_button = QPushButton("Translate to Spanish")
        self.translate_button.clicked.connect(self.translate_text)

        layout.addWidget(self.translate_button)

    def _populate_languages(self):
        languages = {
            "en-US": "English (United States)",
            "es-ES": "Spanish (Spain)",
            "fr-FR": "French (France)",
            # Add other languages and their codes here
        }
        for code, name in languages.items():
            self.language_dropdown.addItem(name, code)

    def on_audio_input_change(self):
        if self.audio_input_dropdown.currentData() == "file":
            self.audio_file_path_label.show()
            self.audio_file_path_input.show()
            self.browse_button.show()
            self.start_recording_button.hide()
            self.stop_recording_button.hide()
        elif self.audio_input_dropdown.currentData() == "microphone":
            self.audio_file_path_label.hide()
            self.audio_file_path_input.hide()
            self.browse_button.hide()
            self.start_recording_button.show()
            self.stop_recording_button.show()

    def start_recording(self):
        self.recording = True
        self.result_text.setText("Recording...")
        self.audio_data = []
        threading.Thread(target=self.record_audio, daemon=True).start()

    def stop_recording(self):
        self.recording = False
        self.result_text.setText("Recording stopped.")

    def record_audio(self):
        with sd.InputStream(callback=self.audio_callback):
            while self.recording:
                sd.sleep(1000)

    def audio_callback(self, indata, frames, time, status):
        self.audio_data.append(indata.copy())

    def browse_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.audio_file_path_input.setText(file_path)

    def transcribe_audio(self, selected_language_code, audio_input_source, audio_source=None):
        """
        Transcribe audio from a file or microphone.

        :param selected_language_code: The language code for transcription.
        :param audio_input_source: The source of the audio ('file' or 'microphone').
        :param audio_source: The path to the audio file, if the source is a file.
        """

        if audio_input_source == "file":
            if audio_source is None:
                self.result_text.setText("Error: No file path provided for transcription.")
                return

            self.result_text.setText(f"Transcribing file: {audio_source}\nLanguage: {selected_language_code}")
        elif audio_input_source == "microphone":
            self.result_text.setText("Recording from microphone...")
        else:
            self.result_text.setText("Error: Invalid audio input source.")

    def translate_text(self):
        text_to_translate = self.result_text.toPlainText()
        try:
            response = requests.post("http://127.0.0.1:7060/translate",
                                     json={"text": text_to_translate, "target_language": "es"})
            if response.status_code == 200:
                translated_text = response.json().get("translated_text", "")
                self.result_text.setText(translated_text)
            else:
                self.result_text.setText(f"Error in translation: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.result_text.setText(f"Request Error: {e}")

# Run the application
app = QApplication(sys.argv)
main_window = TranscriptionApp()
main_window.show()
sys.exit(app.exec())