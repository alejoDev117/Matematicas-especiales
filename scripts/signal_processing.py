import numpy as np
import librosa
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.signal import spectrogram, butter, lfilter
from pathlib import Path
from datetime import datetime


def load_audio(file_path, offset=0.0, duration=None):
    """Carga audio (MP3, WAV, etc.) usando librosa - muy confiable."""
    try:
        # mono=True fuerza a mono, sr=None mantiene sample rate original
        data, fs = librosa.load(
            file_path,
            mono=True,
            sr=None,
            offset=max(0.0, float(offset)),
            duration=None if duration is None else max(0.0, float(duration)),
        )
        # Normalizar
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data = data.astype(np.float32) / max_val
        else:
            data = data.astype(np.float32)
        print(f"Cargado: {file_path} | fs={fs} | duración={len(data) / fs:.1f} seg")
        return fs, data
    except Exception as e:
        print(f"Error cargando {file_path}: {e}")
        raise


def apply_stft(data, fs, n_fft=2048):
    """Aplica STFT (basado en FFT) para obtener espectrograma."""
    f, t, Sxx = spectrogram(data, fs=fs, nperseg=n_fft, noverlap=n_fft // 2)
    Sxx = np.log(Sxx + 1e-10)  # Escala logarítmica
    return f, t, Sxx


def apply_laplace_filter(data):
    """Filtro aproximado de Laplace (segunda derivada)."""
    # Útil para resaltar transitorios y ataques de notas
    return np.diff(data, n=2)


def apply_cleaning(data, fs):
    # Filtro paso-alto para eliminar frecuencias muy bajas (rumble, ruido de ventilador)
    cutoff_low = 80  # Hz - mucho más bajo para mantener bajos musicales
    nyquist = 0.5 * fs
    normal_cutoff_low = cutoff_low / nyquist
    b_low, a_low = butter(4, normal_cutoff_low, btype='high', analog=False)
    data = lfilter(b_low, a_low, data)
    
    # Filtro paso-bajo para eliminar frecuencias muy altas (siseos, artefactos)
    # La mayoría de instrumentos musicales están bajo 8kHz
    cutoff_high = 8000  # Hz
    normal_cutoff_high = cutoff_high / nyquist
    b_high, a_high = butter(4, normal_cutoff_high, btype='low', analog=False)
    data = lfilter(b_high, a_high, data)
    
    # Noise Gate suave: reducir el ruido de forma más gentil
    # Usar threshold adaptativo basado en RMS
    rms = np.sqrt(np.mean(data**2))
    threshold = rms * 0.2  # 20% del RMS como threshold (menos agresivo)
    mask = np.abs(data) < threshold
    data[mask] *= 0.3  # Reducir suavemente el ruido de fondo
    
    return data.astype(np.float32)


def get_project_root():
    return Path(__file__).resolve().parent.parent


def get_output_dir():
    output_dir = get_project_root() / 'data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_spectrogram_output_dir(clear_existing=False):
    output_dir = get_output_dir() / 'espectogramas'
    output_dir.mkdir(parents=True, exist_ok=True)

    if clear_existing:
        for image_file in output_dir.glob('*'):
            if image_file.is_file() and image_file.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
                image_file.unlink(missing_ok=True)

    return output_dir


def sanitize_name(name):
    clean = ''.join(c if c.isalnum() or c in ('-', '_') else '_' for c in str(name))
    return clean.strip('_') or 'audio'


def build_output_name(prefix, source_name, suffix, ext='png'):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_source = sanitize_name(source_name)
    safe_prefix = sanitize_name(prefix)
    return f"{safe_prefix}_{safe_source}_{suffix}_{timestamp}.{ext}"


def save_spectrogram_figure(audio_path, output_dir, output_name, n_fft=2048, start_sec=None, end_sec=None, highlight_range=None):
    # Siempre carga la canción completa (a menos que se especifique específicamente start_sec/end_sec sin highlight)
    fs, data = load_audio(str(audio_path))
    title_suffix = ''
    
    if len(data) == 0:
        raise ValueError(f'No se pudo cargar audio para graficar: {audio_path}')

    f, t, Sxx = apply_stft(data, fs, n_fft=n_fft)

    # Evita consumo excesivo de RAM en audios largos reduciendo resolución para la gráfica.
    max_freq_bins = 512
    max_time_bins = 2000
    freq_step = max(1, int(np.ceil(len(f) / max_freq_bins)))
    time_step = max(1, int(np.ceil(len(t) / max_time_bins)))

    f_plot = f[::freq_step]
    t_plot = t[::time_step]
    Sxx_plot = np.ascontiguousarray(Sxx[::freq_step, ::time_step], dtype=np.float32)

    fig, ax = plt.subplots(figsize=(11, 4.5))
    mesh = ax.imshow(
        Sxx_plot,
        origin='lower',
        aspect='auto',
        cmap='magma',
        extent=[t_plot[0], t_plot[-1], f_plot[0], f_plot[-1]],
        interpolation='nearest',
    )
    
    # Si tenemos un rango a resaltar, dibujamos un rectángulo rojo
    if highlight_range is not None:
        highlight_start, highlight_end = highlight_range
        if highlight_start is not None and highlight_end is not None:
            title_suffix = f' (match en {highlight_start:.2f}s - {highlight_end:.2f}s)'
            # Dibujar rectángulo rojo alrededor del rango de coincidencia
            rect = Rectangle(
                (highlight_start, f_plot[0]),
                highlight_end - highlight_start,
                f_plot[-1] - f_plot[0],
                linewidth=2.5,
                edgecolor='red',
                facecolor='none',
                linestyle='--'
            )
            ax.add_patch(rect)
    
    ax.set_title(f'Espectrograma - {Path(audio_path).name}{title_suffix}')
    ax.set_xlabel('Tiempo [s]')
    ax.set_ylabel('Frecuencia [Hz]')
    fig.colorbar(mesh, ax=ax, label='Magnitud log')
    fig.tight_layout()

    output_path = Path(output_dir) / output_name
    if output_path.exists():
        output_path.unlink()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return str(output_path)


def save_offset_histogram(offset_counts, output_dir, output_name, song_name):
    if not offset_counts:
        return None

    offsets = sorted(offset_counts.keys())
    values = [offset_counts[o] for o in offsets]

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar(offsets, values, width=0.08, color='#2c7fb8', edgecolor='#084081')
    ax.set_title(f'Histograma de desfases - {song_name}')
    ax.set_xlabel('Desfase temporal (s)')
    ax.set_ylabel('Coincidencias')
    ax.grid(axis='y', alpha=0.25)
    fig.tight_layout()

    output_path = Path(output_dir) / output_name
    if output_path.exists():
        output_path.unlink()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return str(output_path)