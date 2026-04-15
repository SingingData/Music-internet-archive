import librosa
import soundfile as sf
import matplotlib.pyplot as plt
import numpy as np

# Load (supports WAV, MP3, etc. via soundfile or librosa)
audio_path = "your_club_recording.wav"
y, sr = librosa.load(audio_path, sr=None)  # Keep original sample rate
print(f"Duration: {len(y)/sr:.2f}s | Sample rate: {sr} Hz | Channels: {y.ndim}")

# Waveform + spectrogram
plt.figure(figsize=(12, 8))
plt.subplot(2,1,1)
librosa.display.waveshow(y, sr=sr)
plt.title("Waveform")
plt.subplot(2,1,2)
D = librosa.stft(y)
librosa.display.specshow(librosa.amplitude_to_db(np.abs(D), ref=np.max),
                         y_axis='log', x_axis='time', sr=sr, cmap='magma')
plt.title("Spectrogram (look for noise floor, reverb tails, bass buildup)")
plt.colorbar(format='%+2.0f dB')
plt.tight_layout()
plt.show()

# Optional: save a trimmed/clean section for reference
sf.write("original_trim.wav", y[:int(30*sr)], sr)  # first 30s