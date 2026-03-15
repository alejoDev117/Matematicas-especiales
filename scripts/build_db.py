import pickle
import os
from scripts.fingerprint import extract_fingerprints

def build_database(songs_dir, db_path='data/db.pkl'):
    """Construye o actualiza la DB de fingerprints."""
    db = {}  # hash -> lista de (canción, offset)
    if os.path.exists(db_path):
        with open(db_path, 'rb') as f:
            db = pickle.load(f)

    for song_file in os.listdir(songs_dir):
        if not song_file.endswith('.wav'): continue
        full_path = os.path.join(songs_dir, song_file)
        fingerprints = extract_fingerprints(full_path)
        for hash_key, offset in fingerprints:
            if hash_key not in db:
                db[hash_key] = []
            db[hash_key].append((song_file, offset))

    with open(db_path, 'wb') as f:
        pickle.dump(db, f)
    print(f"DB actualizada con {len(os.listdir(songs_dir))} canciones. Total hashes: {len(db)}")