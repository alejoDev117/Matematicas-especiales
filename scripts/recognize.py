import pyaudio
import wave
import os
import pickle
import numpy as np
from collections import defaultdict
from pathlib import Path
from scripts.fingerprint import extract_fingerprints
from scripts.signal_processing import (
    apply_cleaning,
    get_project_root,
    get_spectrogram_output_dir,
    get_output_dir,
    build_output_name,
    save_spectrogram_figure,
    save_offset_histogram,
    load_audio,
)


def load_db(db_path='data/db.pkl'):
    if not os.path.exists(db_path):
        raise ValueError("La base de datos no existe. Ejecuta la opción 1 primero.")
    with open(db_path, 'rb') as f:
        return pickle.load(f)


def find_matches_details(sample_fingerprints, db, confidence_threshold=4):
    """
    Busca coincidencias usando un histograma de offsets.
    Esto asegura que los hashes coincidan en el MISMO ORDEN TEMPORAL.
    
    confidence_threshold: Score mínimo requerido para considerar una coincidencia válida.
                         Micrófono: 2-3 (más ruidoso)
                         Archivos: 4+ (más limpio)
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
        return {
            'best_song': 'Desconocida',
            'max_score': 0,
            'status': 'Sin coincidencias',
            'histograms': histograms,
            'best_delta': None,
            'sample_min_offset': None,
            'sample_max_offset': None,
        }

    best_song = "Desconocida"
    max_score = 0

    # Buscamos la canción que tenga el pico más alto en su histograma
    best_delta = None
    for song, offsets in histograms.items():
        # El score es el máximo de coincidencias que comparten un mismo desfase temporal
        current_max = max(offsets.values())
        if current_max > max_score:
            max_score = current_max
            best_song = song
            best_delta = max(offsets.items(), key=lambda item: item[1])[0]

    if sample_fingerprints:
        sample_offsets = [offset for _, offset in sample_fingerprints]
        sample_min_offset = float(min(sample_offsets))
        sample_max_offset = float(max(sample_offsets))
    else:
        sample_min_offset = None
        sample_max_offset = None

    # Umbral de confianza: Si el mejor match tiene muy pocos puntos alineados, es ruido
    if max_score < confidence_threshold:
        return {
            'best_song': 'Desconocida',
            'max_score': max_score,
            'status': f'Confianza baja: {max_score} matches',
            'histograms': histograms,
            'best_delta': best_delta,
            'sample_min_offset': sample_min_offset,
            'sample_max_offset': sample_max_offset,
        }

    return {
        'best_song': best_song,
        'max_score': max_score,
        'status': 'OK',
        'histograms': histograms,
        'best_delta': best_delta,
        'sample_min_offset': sample_min_offset,
        'sample_max_offset': sample_max_offset,
    }


def find_matches(sample_fingerprints, db):
    result = find_matches_details(sample_fingerprints, db, confidence_threshold=4)
    if result['best_song'] == 'Desconocida':
        return f"Desconocida ({result['status']})"
    return f"{result['best_song']} (Score: {result['max_score']})"


def resolve_song_path(song_name):
    songs_dir = get_project_root() / 'data' / 'songs'
    candidate = songs_dir / song_name
    if candidate.exists():
        return candidate

    # Fallback por si cambia la extensión o hay diferencias de mayúsculas.
    song_base = Path(song_name).stem.lower()
    for entry in songs_dir.glob('*'):
        if entry.is_file() and entry.stem.lower() == song_base:
            return entry
    return None


def save_recognition_plots(input_audio_path, result):
    output_dir = get_spectrogram_output_dir(clear_existing=True)
    input_name = Path(input_audio_path).stem

    input_plot = save_spectrogram_figure(
        input_audio_path,
        output_dir,
        build_output_name('entrada', input_name, 'spectrograma')
    )
    print(f"--- Espectrograma entrada guardado: {input_plot} ---")

    best_song = result['best_song']
    if best_song == 'Desconocida':
        print('--- No se generó espectrograma de canción por falta de match confiable ---')
        return

    song_path = resolve_song_path(best_song)
    if song_path is None:
        print(f"--- No se encontró el archivo físico de la canción: {best_song} ---")
        return

    # Calcula el fragmento de la canción que mejor alinea con la entrada.
    best_delta = result.get('best_delta')
    sample_min_offset = result.get('sample_min_offset')
    sample_max_offset = result.get('sample_max_offset')

    song_start_sec = None
    song_end_sec = None

    if best_delta is not None and sample_min_offset is not None and sample_max_offset is not None:
        margin_sec = 1.0
        song_start_sec = max(0.0, float(best_delta + sample_min_offset - margin_sec))
        song_end_sec = float(best_delta + sample_max_offset + margin_sec)

        # Si por redondeos el tramo sale inválido, usamos la duración del input como respaldo.
        if song_end_sec <= song_start_sec:
            fs_in, data_in = load_audio(str(input_audio_path))
            input_duration = len(data_in) / fs_in if fs_in > 0 else 0
            song_end_sec = song_start_sec + max(1.0, input_duration)

    fragment_tag = 'spectrograma_completo_match'

    song_plot = save_spectrogram_figure(
        song_path,
        output_dir,
        build_output_name('match', Path(best_song).stem, fragment_tag),
        highlight_range=(song_start_sec, song_end_sec),
    )
    if song_start_sec is not None and song_end_sec is not None:
        print(f"--- Espectrograma completo con match resaltado ({song_start_sec:.2f}s-{song_end_sec:.2f}s) guardado: {song_plot} ---")
    else:
        print(f"--- Espectrograma match guardado: {song_plot} ---")

    offsets = result['histograms'].get(best_song, {})
    histogram_plot = save_offset_histogram(
        offsets,
        output_dir,
        build_output_name('match', Path(best_song).stem, 'histograma_desfases'),
        best_song,
    )
    if histogram_plot:
        print(f"--- Histograma de desfases guardado: {histogram_plot} ---")


def recognize_from_file(file_path):
    # Aquí usamos el extract_fingerprints con los ajustes de Hash Relativo que hicimos antes
    fingerprints = extract_fingerprints(file_path)
    db = load_db()
    result = find_matches_details(fingerprints, db)
    save_recognition_plots(file_path, result)
    if result['best_song'] == 'Desconocida':
        return f"Desconocida ({result['status']})"
    return f"{result['best_song']} (Score: {result['max_score']})"


def recognize_from_file_details(file_path, db=None, save_plots=True, from_mic=False):
    fingerprints = extract_fingerprints(file_path, from_mic=from_mic)
    local_db = db if db is not None else load_db()
    confidence_threshold = 2 if from_mic else 4
    result = find_matches_details(fingerprints, local_db, confidence_threshold=confidence_threshold)
    if save_plots:
        save_recognition_plots(file_path, result)
    return result


def recognize_from_mic(record_seconds=10):
    """Graba del mic, guarda el audio original, limpia y guarda el audio limpio."""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 2048  # Aumentado de 1024 para mejor estabilidad

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
    output_dir = str(get_output_dir())

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

    # Clip defensivo para evitar distorsión por overflow al volver a int16.
    cleaned_audio = np.clip(cleaned_audio, -1.0, 1.0)
    cleaned_ints = (cleaned_audio * 32767).astype(np.int16)
    with wave.open(cleaned_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(cleaned_ints.tobytes())

    print(f"--- Audio filtrado guardado: {cleaned_filename} ---")

    # --- 4. RECONOCIMIENTO ROBUSTO ---
    # Evaluamos ORIGINAL y LIMPIO, y nos quedamos con el de mayor score.
    db = load_db()

    result_original = recognize_from_file_details(original_filename, db=db, save_plots=False, from_mic=True)
    result_cleaned = recognize_from_file_details(cleaned_filename, db=db, save_plots=False, from_mic=True)

    best_result = result_cleaned
    best_source = cleaned_filename

    if result_original['max_score'] > result_cleaned['max_score']:
        best_result = result_original
        best_source = original_filename

    print(
        f"--- Score ORIGINAL: {result_original['max_score']} | "
        f"Score LIMPIO: {result_cleaned['max_score']} | "
        f"Fuente elegida: {Path(best_source).name} ---"
    )

    save_recognition_plots(best_source, best_result)

    if best_result['best_song'] == 'Desconocida':
        return f"Desconocida ({best_result['status']})"
    return f"{best_result['best_song']} (Score: {best_result['max_score']})"