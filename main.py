import sys
from scripts.build_db import build_database
from scripts.recognize import recognize_from_mic, recognize_from_file

def show_menu():
    while True:
        print("\nBienvenido al Shazam Casero!")
        print("1. Construir/actualizar repositorio de canciones")
        print("2. Reconocer canción")
        print("3. Salir")
        choice = input("Elige una opción: ").strip()
        
        if choice == '1':
            songs_dir = input("Ruta a carpeta de canciones (e.g., data/songs/): ").strip()
            build_database(songs_dir)
            print("Repositorio actualizado!")
        
        elif choice == '2':
            print("1. Desde micrófono (10s)")
            print("2. Desde archivo MP3")
            sub_choice = input("Elige: ").strip()
            if sub_choice == '1':
                song = recognize_from_mic()
            elif sub_choice == '2':
                file_path = input("Ruta al fragmento MP3: ").strip()
                song = recognize_from_file(file_path)
            else:
                print("Opción inválida.")
                continue
            print(f"Canción detectada: {song}")
        
        elif choice == '3':
            print("¡Hasta luego!")
            sys.exit(0)
        
        else:
            print("Opción inválida. Intenta de nuevo.")

if __name__ == "__main__":
    show_menu()