import pickle
import os
from collections import defaultdict


def view_song_list(db_path='data/db.pkl'):
    """Muestra solo la lista de canciones con información relevante."""

    if not os.path.exists(db_path):
        print(f"Archivo no encontrado: {db_path}")
        return

    if os.path.getsize(db_path) == 0:
        print("El archivo db.pkl está vacío.")
        return

    try:
        with open(db_path, 'rb') as f:
            db = pickle.load(f)
    except Exception as e:
        print(f"Error al cargar db.pkl: {type(e).__name__} - {e}")
        return

    # Contar fingerprints por canción
    song_counts = defaultdict(int)

    for entries in db.values():
        for song, offset in entries:
            song_counts[song] += 1

    total_fingerprints = sum(song_counts.values())

    print("\n=== Canciones en la base de datos ===")
    print(f"Total canciones: {len(song_counts)}")
    print(f"Total fingerprints: {total_fingerprints:,}\n")

    print(f"{'Canción':40} | {'Fingerprints':12} | {'% DB'}")
    print("-" * 65)

    for song, count in sorted(song_counts.items(), key=lambda x: x[1], reverse=True):
        percent = (count / total_fingerprints) * 100
        print(f"{song[:40]:40} | {count:12,} | {percent:5.2f}%")
