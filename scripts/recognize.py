import pyaudio
import wave
import os
import pickle
import numpy as np
from collections import defaultdict
from scripts.fingerprint import extract_fingerprints
from scripts.signal_processing import apply_cleaning  # Importamos tu nueva función de limpieza


def load_db(db_path='data/db.pkl'):
    if not os.path.exists(db_path):
        raise ValueError("La base de datos no existe. Ejecuta la opción 1 primero.")
    with open(db_path, 'rb') as f:
        return pickle.load(f)


def find_matches(sample_fingerprints, db):
    """
    Busca coincidencias usando un histograma de offsets.
    Esto asegura que los hashes coincidan en el MISMO ORDEN TEMPORAL.
    """
    # histograms[cancion][desfase] = cuenta
    histograms = defaultdict(lambda: defaultdict(int))

    for sample_hash, sample_offset in sample_fingerprints:
        if sample_hash in db:
            for song, db_offset in db[sample_hash]:
                # Calculamos la diferencia de tiempo entre el micro y la DB
                delta_offset = round(db_offset - sample_offset, 1)
                histograms[song][delta_offset] += 1

    if not histograms:
        return "Desconocida (Sin coincidencias)"

    best_song = "Desconocida"
    max_score = 0

    # Buscamos la canción que tenga el pico más alto en su histograma
    for song, offsets in histograms.items():
        # El score es el máximo de coincidencias que comparten un mismo desfase temporal
        current_max = max(offsets.values())
        if current_max > max_score:
            max_score = current_max
            best_song = song

    # Umbral de confianza: Si el mejor match tiene muy pocos puntos alineados, es ruido
    if max_score < 4:
        return f"Desconocida (Confianza baja: {max_score} matches)"

    return f"{best_song} (Score: {max_score})"


def recognize_from_file(file_path):
    # Aquí usamos el extract_fingerprints con los ajustes de Hash Relativo que hicimos antes
    fingerprints = extract_fingerprints(file_path)
    db = load_db()
    return find_matches(fingerprints, db)


def recognize_from_mic(record_seconds=10):
    """Graba del mic, guarda el audio original, limpia y guarda el audio limpio."""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)

    print(f">>> ESCUCHANDO ({record_seconds}s)...")
    frames = []
    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print(">>> GRABACIÓN COMPLETA. PROCESANDO...")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # --- 1. GUARDADO DEL AUDIO ORIGINAL (CRUDO) ---
    raw_bytes = b''.join(frames)
    output_dir = r"C:\Users\USUARIO\Desktop\Matematicas-especiales\data\output"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    original_filename = os.path.join(output_dir, "audio_microfono_ORIGINAL.wav")
    with wave.open(original_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(RATE)
        wf.writeframes(raw_bytes)

    print(f"--- Audio original guardado: {original_filename} ---")

    # --- 2. PROCESO DE LIMPIEZA ---
    # Convertimos los bytes a array de numpy
    raw_audio_np = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)

    # Normalización (rango -1 a 1)
    max_val = np.max(np.abs(raw_audio_np))
    if max_val > 0:
        raw_audio_np /= max_val

    # Aplicamos filtros (Paso Alto + Noise Gate)
    cleaned_audio = apply_cleaning(raw_audio_np, RATE)

    # --- 3. GUARDADO DEL AUDIO LIMPIO ---
    cleaned_filename = os.path.join(output_dir, "audio_microfono_LIMPIO.wav")

    # Convertimos de nuevo a int16 para el formato WAV
    cleaned_ints = (cleaned_audio * 32767).astype(np.int16)
    with wave.open(cleaned_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(cleaned_ints.tobytes())

    print(f"--- Audio filtrado guardado: {cleaned_filename} ---")

    # --- 4. RECONOCIMIENTO ---
    # Usamos el archivo limpio para el análisis de fingerprints
    return recognize_from_file(cleaned_filename)