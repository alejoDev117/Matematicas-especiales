import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram
import torchaudio  # Agrega este import al principio

def load_audio(file_path):
    """Carga audio (WAV o MP3) y lo normaliza a mono."""
    waveform, fs = torchaudio.load(file_path)  # Soporta MP3, WAV, etc.
    if waveform.shape[0] > 1:  # Multi-channel a mono
        waveform = waveform.mean(dim=0)
    data = waveform.squeeze().numpy()  # A NumPy array
    data = data / np.max(np.abs(data))  # Normalizar
    return fs, data

def apply_stft(data, fs, n_fft=2048):
    """Aplica STFT (basado en FFT) para obtener espectrograma."""
    f, t, Sxx = spectrogram(data, fs=fs, nperseg=n_fft, noverlap=n_fft//2)
    Sxx = np.log(Sxx + 1e-10)  # Escala logarítmica para estabilidad
    return f, t, Sxx

def apply_laplace_filter(data):
    """Filtro aproximado de Laplace (segunda derivada para enfatizar cambios). Opcional."""
    return np.diff(data, n=2)