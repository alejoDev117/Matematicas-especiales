import pyaudio
import wave
import tempfile
import os
import pickle
from collections import defaultdict
from scripts.fingerprint import extract_fingerprints

def load_db(db_path='data/db.pkl'):
    if not os.path.exists(db_path):
        raise ValueError("DB no existe. Construye primero.")
    with open(db_path, 'rb') as f:
        return pickle.load(f)

def find_matches(sample_fingerprints, db):
    """Busca matches y alinea offsets."""
    match_counts = defaultdict(int)
    offsets = defaultdict(list)

    for sample_hash, sample_offset in sample_fingerprints:
        if sample_hash in db:
            for song, db_offset in db[sample_hash]:
                delta_offset = db_offset - sample_offset  # Alineación
                offsets[song].append(delta_offset)
                match_counts[song] += 1

    # Encuentra la canción con más matches (y offsets consistentes)
    if not match_counts:
        return "Desconocida"
    best_song = max(match_counts, key=match_counts.get)
    # Opcional: Verifica consistencia de offsets (histograma para peak)
    return best_song

def recognize_from_file(file_path):
    fingerprints = extract_fingerprints(file_path)
    db = load_db()
    return find_matches(fingerprints, db)


def recognize_from_mic(record_seconds=10):
    """Graba del mic, guarda el archivo en el escritorio y luego lo reconoce."""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()

    # Iniciar flujo de captura
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)

    print(f">>> ESCUCHANDO ({record_seconds}s)... Habla o pon música ahora.")
    frames = []

    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print(">>> GRABACIÓN COMPLETA.")

    # Cerrar el flujo del micrófono
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # --- LÓGICA DE GUARDADO EN RUTA ESPECÍFICA ---
    output_dir = r"C:\Users\USUARIO\Desktop\Matematicas-especiales\data\output"
    output_filename = os.path.join(output_dir, "test_microfono.wav")

    # Crear la carpeta si no existe para evitar errores
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Guardar el archivo .wav
    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print(f"--- Archivo guardado para verificación: {output_filename} ---")

    # --- CONTINUAR CON EL RECONOCIMIENTO ---
    # Ahora enviamos la ruta del archivo recién guardado a la función de análisis
    result = recognize_from_file(output_filename)

    return result