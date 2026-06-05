# Matematicas-especiales
En este repositorio estará todo el desarrollo y documentación relacionados con el proyecto final de la materia de matemáticas especiales.

## Descripción del Proyecto
Sistema de reconocimiento de canciones tipo **Shazam** que utiliza técnicas de procesamiento de señales y análisis espectral para identificar canciones a partir de audio en vivo o archivos. El sistema utiliza **fingerprinting perceptual** basado en picos espectrales y hashes relativos.

# Configuración del proyecto
La primera vez que se quiera ejecutar el proyecto por primera vez use este comando para dejar todas las librerias configuradas
```Bash
pip install -r requirements.txt
```

---

## Arquitectura del Proyecto

### Diagrama de Paquetes

```mermaid
graph TB
    subgraph "main.py"
        MAIN["main.py<br/>(Interfaz Principal)"]
    end
    
    subgraph "scripts/"
        BUILD["build_db.py<br/>(Construcción DB)"]
        RECOG["recognize.py<br/>(Reconocimiento)"]
        FINGER["fingerprint.py<br/>(Extracción de Hashes)"]
        SIGNAL["signal_processing.py<br/>(Procesamiento de Señal)"]
        VIEW["view_db.py<br/>(Visualización DB)"]
    end
    
    subgraph "data/"
        DB["db.pkl<br/>(Base de Datos)"]
        INPUT["input/<br/>(Audio Input)"]
        SONGS["songs/<br/>(Catálogo)"]
        OUTPUT["output/<br/>(Gráficas)"]
    end
    
    MAIN --> BUILD
    MAIN --> RECOG
    MAIN --> VIEW
    
    BUILD --> FINGER
    BUILD --> SIGNAL
    BUILD --> DB
    
    RECOG --> FINGER
    RECOG --> SIGNAL
    RECOG --> DB
    RECOG --> OUTPUT
    
    FINGER --> SIGNAL
    
    BUILD --> SONGS
    RECOG --> INPUT
    SIGNAL --> OUTPUT
```

### Descripción de Módulos

| Módulo | Función |
|--------|---------|
| **main.py** | Menú interactivo principal. Gestiona las opciones del usuario |
| **build_db.py** | Construye/actualiza la base de datos a partir de las canciones del catálogo |
| **fingerprint.py** | Extrae fingerprints (hashes perceptuales) del audio usando STFT y análisis de picos espectrales |
| **signal_processing.py** | Carga audio, aplica filtros, limpieza, genera espectrogramas y gráficas |
| **recognize.py** | Motor de reconocimiento. Compara fingerprints, calcula offsets y genera visualizaciones |
| **view_db.py** | Utilidad para inspeccionar la base de datos |

---

## Flujo de Ejecución

### Secuencia 1: Construcción de Base de Datos

```mermaid
sequenceDiagram
    participant User
    participant main.py
    participant build_db.py
    participant fingerprint.py
    participant signal_processing.py
    participant Database as db.pkl
    
    User->>main.py: Opción 1: Construir DB
    main.py->>build_db.py: build_database(songs_dir)
    
    loop Para cada canción en songs/
        build_db.py->>signal_processing.py: load_audio(song)
        signal_processing.py-->>build_db.py: fs, data
        
        build_db.py->>fingerprint.py: extract_fingerprints(audio)
        fingerprint.py->>signal_processing.py: apply_stft(data, fs)
        signal_processing.py-->>fingerprint.py: f, t, Sxx
        fingerprint.py->>fingerprint.py: find_peaks() en Sxx
        fingerprint.py->>fingerprint.py: Generar hashes relativos<br/>(target zone)
        fingerprint.py-->>build_db.py: lista de (hash, offset)
        
        build_db.py->>Database: Guardar hash → (canción, offset)
    end
    
    build_db.py->>Database: pickle.dump() guardar DB
    Database-->>main.py: ✓ Base de datos actualizada
```

### Secuencia 2: Reconocimiento desde Micrófono

```mermaid
sequenceDiagram
    participant User
    participant main.py
    participant recognize.py
    participant signal_processing.py
    participant fingerprint.py
    participant Database as db.pkl
    participant recognize.py as rec2
    
    User->>main.py: Opción 2.1: Micrófono (10s)
    main.py->>recognize.py: recognize_from_mic()
    
    recognize.py->>recognize.py: Capturar 10s de audio<br/>con PyAudio
    recognize.py->>signal_processing.py: apply_cleaning(data)
    signal_processing.py-->>recognize.py: audio limpio
    
    recognize.py->>signal_processing.py: save_spectrogram_figure()<br/>(audio original)
    signal_processing.py-->>recognize.py: espectrograma guardado
    
    recognize.py->>fingerprint.py: extract_fingerprints(audio, from_mic=True)
    fingerprint.py->>signal_processing.py: apply_stft()
    signal_processing.py-->>fingerprint.py: Sxx
    fingerprint.py->>fingerprint.py: Detectar picos<br/>(settings para micrófono)
    fingerprint.py->>fingerprint.py: Generar hashes<br/>relativos
    fingerprint.py-->>recognize.py: lista de (hash, offset)
    
    recognize.py->>Database: load_db()
    Database-->>recognize.py: db completa
    
    recognize.py->>rec2: find_matches_details(fingerprints, db)
    rec2->>rec2: Histograma de offsets<br/>por canción
    rec2->>rec2: Calcular desfases<br/>temporal
    rec2->>rec2: Encontrar mejor<br/>coincidencia
    rec2-->>recognize.py: {canción, score, offset}
    
    recognize.py->>signal_processing.py: save_spectrogram_figure()<br/>(con match resaltado)<br/>save_offset_histogram()
    signal_processing.py-->>recognize.py: gráficas guardadas
    
    recognize.py-->>main.py: ">>> RESULTADO: Canción X"
    main.py-->>User: Mostrar resultado
```

### Secuencia 3: Reconocimiento desde Archivo

```mermaid
sequenceDiagram
    participant User
    participant main.py
    participant recognize.py
    participant signal_processing.py
    participant fingerprint.py
    participant Database as db.pkl
    
    User->>main.py: Opción 2.2: Desde archivo
    main.py->>main.py: Listar archivos<br/>en data/input/
    main.py->>User: Mostrar opciones
    User->>main.py: Seleccionar archivo
    
    main.py->>recognize.py: recognize_from_file(archivo)
    
    recognize.py->>signal_processing.py: load_audio(archivo)
    signal_processing.py-->>recognize.py: fs, data
    
    recognize.py->>signal_processing.py: apply_cleaning(data)
    signal_processing.py-->>recognize.py: audio limpio
    
    recognize.py->>signal_processing.py: Guardar espectrogramas<br/>(original + limpio)
    
    recognize.py->>fingerprint.py: extract_fingerprints(audio)
    fingerprint.py->>signal_processing.py: apply_stft()
    fingerprint.py-->>fingerprint.py: Analizar picos
    fingerprint.py-->>recognize.py: fingerprints
    
    recognize.py->>Database: load_db()
    Database-->>recognize.py: db
    
    recognize.py->>recognize.py: find_matches_details()
    recognize.py->>signal_processing.py: Generar gráficas<br/>de match
    
    recognize.py-->>main.py: Resultado
    main.py-->>User: Mostrar canción<br/>identificada
```

---

## Procesamiento de Señal: Paso a Paso

### Extracción de Fingerprints

```
1. Cargar Audio
   ├─ Convertir a mono
   ├─ Normalizar amplitud
   └─ Resample si es necesario

2. Aplicar STFT (Short-Time Fourier Transform)
   ├─ n_fft = 4096 (resolución en frecuencia)
   ├─ Ventanas solapadas (noverlap = n_fft/2)
   └─ Escala logarítmica: log(|X(f,t)| + ε)

3. Detección de Picos Espectrales
   ├─ Por cada ventana temporal
   ├─ Encontrar picos prominentes
   ├─ Seleccionar top 6-8 picos por energía
   └─ Guardar (frecuencia, tiempo)

4. Generación de Hashes Relativos (Target Zone)
   ├─ Cada par de picos (P1, P2) genera un hash
   ├─ Hash = H(f1, Δf, Δt)
   │   donde Δf = f2 - f1, Δt = t2 - t1
   ├─ Almacenar tupla (hash, offset_temporal)
   └─ Guardar en BD: hash → [(canción1, t1), (canción2, t2), ...]

5. Comparación y Matching
   ├─ Extraer fingerprints del audio de entrada
   ├─ Buscar hashes en la BD
   ├─ Por cada coincidencia, calcular desfase temporal
   ├─ Crear histograma de desfases por canción
   ├─ Identificar pico más alto = mejor coincidencia
   └─ Calcular confianza basada en número de matches
```

---

## Visualizaciones Generadas

El sistema genera automáticamente las siguientes gráficas durante el reconocimiento:

1. **Espectrograma Original** (`entrada_audio_*_spectrograma_*.png`)
   - Muestra toda la señal de audio en el dominio tiempo-frecuencia
   - Usada para análisis visual del contenido espectral

2. **Espectrograma con Match Resaltado** (`match_*_spectrograma_completo_match_*.png`)
   - Espectrograma con rectángulo rojo indicando la región donde se encontró la coincidencia
   - Permite verificar visualmente la precisión del matching

3. **Histograma de Desfases** (`match_*_histograma_desfases_*.png`)
   - Gráfica de barras mostrando la distribución de desfases temporales encontrados
   - El pico más alto corresponde al desfase correcto
   - Visualiza la confianza del match

---

## Tecnologías Utilizadas

- **librosa**: Carga y procesamiento de audio (MP3, WAV, etc.)
- **scipy.signal**: STFT, detección de picos, filtros digitales
- **numpy**: Operaciones numéricas y álgebra lineal
- **matplotlib**: Generación de gráficas y espectrogramas
- **PyAudio**: Captura de audio en tiempo real
- **pickle**: Serialización de la base de datos de fingerprints
