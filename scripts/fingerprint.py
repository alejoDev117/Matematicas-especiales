import numpy as np
from scipy.signal import find_peaks
from scripts.signal_processing import load_audio, apply_stft, apply_laplace_filter


def extract_fingerprints(audio_file, use_laplace=False):
    fs, data = load_audio(audio_file)

    if use_laplace:
        data = apply_laplace_filter(data)

    # Aumentamos n_fft para tener mucha más resolución en las frecuencias
    f, t, Sxx = apply_stft(data, fs, n_fft=4096)

    print(f"  Espectrograma: shape={Sxx.shape}, min={Sxx.min():.2f}, max={Sxx.max():.2f}")

    fingerprints = []

    # AJUSTE 1: Densidad máxima. Analizamos cada ventana de tiempo (step=1)
    step = 1

    # Guardaremos los picos encontrados para luego hacer parejas entre diferentes tiempos
    all_peaks = []

    for time_idx in range(0, Sxx.shape[1], step):
        col = Sxx[:, time_idx]

        # AJUSTE 2: Bajamos la prominencia (1.0) para que el micro capte más picos
        peaks, _ = find_peaks(col, prominence=0.5, distance=10)

        if len(peaks) > 0:
            # AJUSTE 3: ORDENAR POR INTENSIDAD.
            # Tomamos los picos con más energía (magnitud) en lugar de los primeros que aparezcan.
            peaks = peaks[np.argsort(col[peaks])][::-1]
            peaks = peaks[:6]  # Nos quedamos con los 6 más fuertes

            for p in peaks:
                # Guardamos: (frecuencia, tiempo_en_segundos)
                all_peaks.append((f[p], t[time_idx]))

    # AJUSTE 4: HASH RELATIVO (Target Zone)
    # En lugar de solo emparejar picos del mismo instante, buscamos picos futuros.
    # Esto genera el "delta_t" que hace que el hash sea único pero independiente del inicio.
    for i in range(len(all_peaks)):
        # Miramos los siguientes 10 picos encontrados (zona de búsqueda)
        for j in range(i + 1, min(i + 15, len(all_peaks))):
            f1, t1 = all_peaks[i]
            f2, t2 = all_peaks[j]

            delta_t = t2 - t1

            # Filtramos para que la distancia temporal no sea demasiado larga (max 2 seg)
            if 0.1 <= delta_t <= 2.0:
                # Creamos una llave única: (Freq1, Freq2, Tiempo_entre_ellas)
                # Redondeamos para dar margen al ruido
                hash_key = (
                    int(f1 / 10) * 10,
                    int(f2 / 10) * 10,
                    int(delta_t * 100)
                )
                # Guardamos el hash junto con el tiempo real de la canción (offset)
                fingerprints.append((hash_key, t1))

    print(f"  Picos totales: {len(all_peaks)} | Fingerprints generados: {len(fingerprints)}")
    return fingerprints