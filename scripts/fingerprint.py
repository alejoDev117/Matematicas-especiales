import numpy as np
from scipy.signal import find_peaks
from scripts.signal_processing import load_audio, apply_stft, apply_laplace_filter  # Importa el servicio matemático

def extract_fingerprints(audio_file, use_laplace=False):
    """Extrae fingerprints: picos del espectrograma y hashes de pares."""
    fs, data = load_audio(audio_file)
    if use_laplace:
        data = apply_laplace_filter(data)  # Opcional: aplica filtro Laplace
    f, t, Sxx = apply_stft(data, fs)  # Usa STFT del servicio

    # Encuentra picos en el espectrograma (alta energía)
    fingerprints = []
    for time_idx in range(Sxx.shape[1]):  # Por columna de tiempo
        col = Sxx[:, time_idx]
        peaks, _ = find_peaks(col, prominence=1)  # Picos con prominencia mínima
        peak_freqs = f[peaks]  # Frecuencias de picos
        peak_time = t[time_idx]  # Tiempo actual

        # Crea hashes de pares de picos (para robustez)
        for i in range(len(peak_freqs)):
            for j in range(i + 1, min(i + 10, len(peak_freqs))):  # Pares cercanos
                freq1, freq2 = peak_freqs[i], peak_freqs[j]
                delta_t = peak_time - peak_time  # Delta=0 ya que misma columna; ajusta si usas ventanas
                hash_key = (int(freq1), int(freq2), int(delta_t * 100))  # Hash simple como tuple
                fingerprints.append((hash_key, peak_time))  # (hash, offset)

    return fingerprints