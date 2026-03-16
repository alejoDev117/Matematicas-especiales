import numpy as np
from scipy.signal import find_peaks
from scripts.signal_processing import load_audio, apply_stft, apply_laplace_filter  # Importa el servicio matemático


def extract_fingerprints(audio_file, use_laplace=False):
    fs, data = load_audio(audio_file)

    if use_laplace:
        data = apply_laplace_filter(data)

    f, t, Sxx = apply_stft(data, fs, n_fft=4096)  # Más resolución freq, menos tiempo

    print(f"  Espectrograma: shape={Sxx.shape}, min={Sxx.min():.2f}, max={Sxx.max():.2f}")

    fingerprints = []
    total_peaks = 0

    step = 10  # Procesar solo cada 10 ventanas temporales
    for time_idx in range(0, Sxx.shape[1], step):
        col = Sxx[:, time_idx]

        # Muy restrictivo: solo picos fuertes
        peaks, props = find_peaks(col, prominence=5.0, distance=20)  # prominence alto!

        if len(peaks) > 0:
            # Tomamos máximo 4 picos (los primeros que detecta, suelen ser los más fuertes)
            peaks = peaks[:4]  # simple slice en vez de ordenar por height
            peak_freqs = f[peaks]
            peak_time = t[time_idx]

            total_peaks += len(peaks)

            # Pares entre estos pocos picos
            for i in range(len(peak_freqs)):
                for j in range(i + 1, len(peak_freqs)):
                    freq1 = int(round(peak_freqs[i] / 10)) * 10
                    freq2 = int(round(peak_freqs[j] / 10)) * 10
                    delta_t = int(peak_time * 10)  # redondeo en tiempo
                    hash_key = (freq1, freq2, delta_t)
                    fingerprints.append((hash_key, peak_time))

    print(f"  Picos seleccionados: {total_peaks} | Fingerprints generados: {len(fingerprints)}")
    return fingerprints