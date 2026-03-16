import numpy as np
import librosa
from scipy.signal import spectrogram


def load_audio(file_path):
    """Carga audio (MP3, WAV, etc.) usando librosa - muy confiable."""
    try:
        # mono=True fuerza a mono, sr=None mantiene sample rate original
        data, fs = librosa.load(file_path, mono=True, sr=None)
        # Normalizar
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data = data.astype(np.float32) / max_val
        else:
            data = data.astype(np.float32)
        print(f"Cargado: {file_path} | fs={fs} | duración={len(data)/fs:.1f} seg")
        return fs, data
    except Exception as e:
        print(f"Error cargando {file_path}: {e}")
        raise


def apply_stft(data, fs, n_fft=2048):
    """Aplica STFT (basado en FFT) para obtener espectrograma."""
    f, t, Sxx = spectrogram(data, fs=fs, nperseg=n_fft, noverlap=n_fft // 2)
    Sxx = np.log(Sxx + 1e-10)  # Escala logarítmica
    return f, t, Sxx


def apply_laplace_filter(data):
    """Filtro aproximado de Laplace (segunda derivada). Opcional."""
    return np.diff(data, n=2)