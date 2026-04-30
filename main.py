import sys
import os
from scripts.build_db import build_database
from scripts.recognize import recognize_from_mic, recognize_from_file


def show_menu():
    while True:
        print("\n--- Bienvenido al Shazam Casero! ---")
        print("1. Construir/actualizar repositorio de canciones")
        print("2. Reconocer canción")
        print("3. Lista de canciones")
        print("4. Salir")
        choice = input("Elige una opción: ").strip()

        if choice == '1':
            songs_dir = "data/songs"
            print(f"Construyendo base de datos desde: {songs_dir}")
            build_database(songs_dir)
            print("Repositorio actualizado!")

        elif choice == '2':
            print("\n1. Desde micrófono (10s)")
            print("2. Desde archivo en data/input")
            sub_choice = input("Elige: ").strip()

            if sub_choice == '1':
                song = recognize_from_mic()
                print(f"\n>>> RESULTADO: {song}")

            elif sub_choice == '2':
                # --- NUEVA LÓGICA AUTOMÁTICA ---
                input_dir = "data/input"

                if not os.path.exists(input_dir):
                    os.makedirs(input_dir)
                    print(f"Carpeta '{input_dir}' creada. Coloca tus archivos ahí.")
                    continue

                # Listar archivos soportados
                archivos = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp3', '.wav'))]

                if not archivos:
                    print(f"No hay archivos .mp3 o .wav en {input_dir}")
                else:
                    print(f"\nArchivos encontrados en {input_dir}:")
                    for i, arc in enumerate(archivos):
                        print(f"{i + 1}. {arc}")

                    try:
                        seleccion = int(input("\nElige el número del archivo: ")) - 1
                        if 0 <= seleccion < len(archivos):
                            ruta_final = os.path.join(input_dir, archivos[seleccion])
                            print(f"Analizando: {archivos[seleccion]}...")
                            song = recognize_from_file(ruta_final)
                            print(f"\n>>> RESULTADO: {song}")
                        else:
                            print("Número fuera de rango.")
                    except ValueError:
                        print("Entrada no válida. Debes ingresar un número.")
                # -------------------------------
            else:
                print("Opción inválida.")

        elif choice == '3':
            try:
                from scripts.view_db import view_song_list
                view_song_list()
            except ImportError:
                print("Error: No se encontró el script 'view_db' o la función 'view_song_list'.")

        elif choice == '4':
            print("¡Hasta luego!")
            sys.exit(0)

        else:
            print("Opción inválida. Intenta de nuevo.")


if __name__ == "__main__":
    show_menu()