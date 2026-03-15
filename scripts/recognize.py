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
    """Graba del mic y reconoce."""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Escuchando... (10 segundos)")
    frames = []
    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Grabación terminada.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    temp_wav = tempfile.mktemp(suffix='.wav')
    with wave.open(temp_wav, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    result = recognize_from_file(temp_wav)
    os.remove(temp_wav)
    return result