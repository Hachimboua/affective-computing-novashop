"""NumPy implementations of lightweight audio features for WAV input."""
import math
import wave

try:
    import numpy as np
except ImportError:
    np = None

from .. import config


class AudioInputError(ValueError):
    """Raised when an audio file cannot be analyzed as supported PCM WAV."""


def numpy_available():
    """Return whether the optional NumPy dependency imported successfully."""
    return np is not None


def _require_numpy():
    if np is None:
        raise AudioInputError("NumPy is unavailable.")


def read_wav(path):
    """Read 16-bit PCM WAV and average stereo channels into mono samples."""
    _require_numpy()
    try:
        with wave.open(str(path), "rb") as stream:
            channels = stream.getnchannels()
            sample_width = stream.getsampwidth()
            sample_rate = stream.getframerate()
            frame_count = stream.getnframes()
            compression = stream.getcomptype()
            raw = stream.readframes(frame_count)
    except (OSError, EOFError, wave.Error) as error:
        raise AudioInputError("The WAV file could not be read.") from error

    if (
        channels not in (1, 2)
        or sample_width != 2
        or sample_rate < 1000
        or frame_count <= 0
        or compression != "NONE"
    ):
        raise AudioInputError("Only mono or stereo 16-bit PCM WAV is supported.")
    samples = np.frombuffer(raw, dtype="<i2")
    if samples.size != frame_count * channels:
        raise AudioInputError("The WAV file ended before its declared frame count.")
    samples = samples.reshape((-1, channels)).astype(np.float64) / 32768.0
    mono = np.mean(samples, axis=1)
    if not mono.size:
        raise AudioInputError("The WAV file contains no samples.")
    return mono, sample_rate


def pre_emphasis(samples, coefficient=None):
    """Boost higher-frequency detail before analysis to reduce spectral tilt."""
    _require_numpy()
    coefficient = (
        config.VOICE_PREEMPHASIS
        if coefficient is None
        else float(coefficient)
    )
    emphasized = np.empty_like(samples, dtype=np.float64)
    if not samples.size:
        return emphasized
    emphasized[0] = samples[0]
    emphasized[1:] = samples[1:] - coefficient * samples[:-1]
    return emphasized


def frame_signal(samples, sample_rate, frame_ms=None, hop_ms=None):
    """Split a waveform into overlapping short frames for local analysis."""
    _require_numpy()
    frame_ms = config.VOICE_FRAME_MS if frame_ms is None else frame_ms
    hop_ms = config.VOICE_HOP_MS if hop_ms is None else hop_ms
    frame_length = max(1, int(round(sample_rate * frame_ms / 1000.0)))
    hop_length = max(1, int(round(sample_rate * hop_ms / 1000.0)))
    if samples.size < frame_length:
        padded = np.pad(samples, (0, frame_length - samples.size))
        return padded.reshape((1, frame_length))
    starts = range(0, samples.size - frame_length + 1, hop_length)
    return np.stack(
        [samples[start : start + frame_length] for start in starts], axis=0
    )


def hamming_window(frames):
    """Apply a Hamming taper to reduce spectral leakage at frame edges."""
    _require_numpy()
    return frames * np.hamming(frames.shape[1])[None, :]


def fft_power_spectrum(windowed_frames, sample_rate):
    """Compute one-sided FFT power spectra and their frequency-bin centers."""
    _require_numpy()
    transform = np.fft.rfft(windowed_frames, axis=1)
    power = (np.abs(transform) ** 2) / float(windowed_frames.shape[1])
    frequencies = np.fft.rfftfreq(
        windowed_frames.shape[1], d=1.0 / float(sample_rate)
    )
    return power, frequencies


def rms_energy_db(frames):
    """Measure each frame's root-mean-square amplitude on a dB scale."""
    _require_numpy()
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    return 20.0 * np.log10(np.maximum(rms, 1e-12))


def zero_crossing_rate(frames, sample_rate):
    """Count sign changes per second as a simple measure of noisiness."""
    _require_numpy()
    crossings = np.sum(frames[:, 1:] * frames[:, :-1] < 0.0, axis=1)
    return crossings * float(sample_rate) / (
        2.0 * max(1, frames.shape[1] - 1)
    )


def spectral_centroid(power, frequencies):
    """Compute the power-weighted mean frequency, a spectral brightness cue."""
    _require_numpy()
    totals = np.sum(power, axis=1)
    weighted = np.sum(power * frequencies[None, :], axis=1)
    return np.divide(
        weighted,
        totals,
        out=np.zeros_like(weighted, dtype=np.float64),
        where=totals > 0.0,
    )


def autocorrelation_pitch(windowed_frames, sample_rate, voiced_mask):
    """Estimate F0 from periodic autocorrelation peaks on voiced frames."""
    _require_numpy()
    pitches = np.zeros(windowed_frames.shape[0], dtype=np.float64)
    strengths = np.zeros_like(pitches)
    minimum_lag = max(
        1, int(math.floor(sample_rate / config.VOICE_MAX_PITCH_HZ))
    )
    maximum_lag = min(
        windowed_frames.shape[1] - 1,
        int(math.ceil(sample_rate / config.VOICE_MIN_PITCH_HZ)),
    )
    if maximum_lag <= minimum_lag:
        return pitches, strengths

    for index, frame in enumerate(windowed_frames):
        if not voiced_mask[index]:
            continue
        centered = frame - np.mean(frame)
        transform = np.fft.rfft(centered, n=2 * centered.size)
        correlation = np.fft.irfft(
            transform * np.conjugate(transform), n=2 * centered.size
        )[: centered.size]
        zero_lag = correlation[0]
        if zero_lag <= 0.0:
            continue
        normalized = correlation / zero_lag
        lag = minimum_lag + int(
            np.argmax(normalized[minimum_lag : maximum_lag + 1])
        )
        strength = float(normalized[lag])
        if strength >= config.VOICE_AUTOCORRELATION_MIN:
            pitches[index] = float(sample_rate) / lag
            strengths[index] = strength
    return pitches, strengths


def median_smooth_pitch(pitches):
    """Replace isolated F0 jumps with the median of neighboring voiced frames."""
    _require_numpy()
    smoothed = np.array(pitches, dtype=np.float64, copy=True)
    for index, pitch in enumerate(pitches):
        if pitch <= 0.0:
            continue
        left = max(0, index - 1)
        right = min(len(pitches), index + 2)
        neighbors = pitches[left:right]
        voiced = neighbors[neighbors > 0.0]
        if voiced.size:
            smoothed[index] = float(np.median(voiced))
    return smoothed


def mel_filterbank(sample_rate, fft_size, filter_count=None):
    """Build triangular filters spaced uniformly on the perceptual Mel scale."""
    _require_numpy()
    filter_count = (
        config.VOICE_MEL_FILTERS
        if filter_count is None
        else int(filter_count)
    )
    maximum_mel = 2595.0 * math.log10(1.0 + sample_rate / 2.0 / 700.0)
    mel_points = np.linspace(0.0, maximum_mel, filter_count + 2)
    hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
    bins = np.floor((fft_size + 1) * hz_points / sample_rate).astype(int)
    bins = np.clip(bins, 0, fft_size // 2)
    filters = np.zeros((filter_count, fft_size // 2 + 1), dtype=np.float64)
    for index in range(filter_count):
        left, center, right = bins[index : index + 3]
        if center > left:
            filters[index, left:center] = (
                np.arange(left, center) - left
            ) / float(center - left)
        if right > center:
            filters[index, center:right] = (
                right - np.arange(center, right)
            ) / float(right - center)
    return filters


def mfcc(power, sample_rate, coefficient_count=None, filter_count=None):
    """Compute MFCCs: log Mel-band power followed by an orthonormal DCT-II."""
    _require_numpy()
    coefficient_count = (
        config.VOICE_MFCC_COUNT
        if coefficient_count is None
        else int(coefficient_count)
    )
    fft_size = (power.shape[1] - 1) * 2
    filters = mel_filterbank(sample_rate, fft_size, filter_count)
    mel_power = power @ filters.T
    log_mel = np.log(np.maximum(mel_power, 1e-12))
    filter_indices = np.arange(filters.shape[0], dtype=np.float64)
    coefficient_indices = np.arange(coefficient_count, dtype=np.float64)
    basis = np.cos(
        math.pi
        / filters.shape[0]
        * (filter_indices[None, :] + 0.5)
        * coefficient_indices[:, None]
    )
    basis[0] *= math.sqrt(1.0 / filters.shape[0])
    if coefficient_count > 1:
        basis[1:] *= math.sqrt(2.0 / filters.shape[0])
    return log_mel @ basis.T


def speaking_rate_proxy(voiced_mask, duration_seconds):
    """Estimate syllabic pace by counting voiced-segment starts per second."""
    _require_numpy()
    if duration_seconds <= 0.0 or not len(voiced_mask):
        return 0.0
    starts = np.asarray(voiced_mask, dtype=bool) & ~np.r_[
        False, np.asarray(voiced_mask[:-1], dtype=bool)
    ]
    return float(np.sum(starts)) / float(duration_seconds)


def _estimate_snr_db(power, frequencies):
    """Estimate SNR by contrasting total band power with its median noise floor."""
    band = (frequencies >= 100.0) & (
        frequencies <= min(4000.0, frequencies[-1])
    )
    if not np.any(band):
        return -100.0
    band_power = power[:, band]
    noise_density = np.median(band_power, axis=1)
    noise_power = noise_density * band_power.shape[1]
    signal_power = np.maximum(
        np.sum(band_power, axis=1) - noise_power, 1e-12
    )
    frame_snr = 10.0 * np.log10(
        signal_power / np.maximum(noise_power, 1e-12)
    )
    return float(np.median(frame_snr))


def extract_features(samples, sample_rate):
    """Extract framed energy, ZCR, spectrum, pitch, MFCC, SNR, and clipping."""
    _require_numpy()
    samples = np.asarray(samples, dtype=np.float64)
    if samples.ndim != 1 or not samples.size or sample_rate < 1000:
        raise AudioInputError("Audio samples or sample rate are invalid.")

    duration = samples.size / float(sample_rate)
    raw_frames = frame_signal(samples, sample_rate)
    emphasized_frames = frame_signal(
        pre_emphasis(samples), sample_rate
    )
    windowed = hamming_window(emphasized_frames)
    power, frequencies = fft_power_spectrum(windowed, sample_rate)
    energy = rms_energy_db(raw_frames)
    zcr = zero_crossing_rate(raw_frames, sample_rate)
    centroid = spectral_centroid(power, frequencies)
    voiced = (
        (energy >= config.VOICE_VOICED_ENERGY_FLOOR_DB)
        & (zcr <= config.VOICE_MAX_ZCR_HZ)
    )
    pitch, strengths = autocorrelation_pitch(windowed, sample_rate, voiced)
    pitch = median_smooth_pitch(pitch)
    voiced &= pitch > 0.0
    voiced_pitch = pitch[voiced]
    pitch_mean = float(np.mean(voiced_pitch)) if voiced_pitch.size else 0.0
    pitch_variability = (
        float(np.std(voiced_pitch) / pitch_mean)
        if voiced_pitch.size and pitch_mean > 0.0
        else 0.0
    )
    mfcc_values = mfcc(power, sample_rate)
    rms = float(np.sqrt(np.mean(samples * samples)))
    rms_db = 20.0 * math.log10(max(rms, 1e-12))
    clipping_ratio = float(
        np.mean(np.abs(samples) >= config.VOICE_CLIP_LEVEL)
    )
    voiced_ratio = float(np.mean(voiced))
    features = {
        "duration_seconds": float(duration),
        "rms_db": float(rms_db),
        "energy_db": float(np.mean(energy)),
        "zcr_hz": float(np.mean(zcr)),
        "spectral_centroid_hz": float(np.mean(centroid)),
        "f0_mean_hz": pitch_mean,
        "f0_variability": pitch_variability,
        "voiced_ratio": voiced_ratio,
        "speaking_rate": speaking_rate_proxy(voiced, duration),
        "snr_db": _estimate_snr_db(power, frequencies),
        "clipping_ratio": clipping_ratio,
        "mfcc_mean": np.mean(mfcc_values, axis=0).tolist(),
        "mfcc_std": np.std(mfcc_values, axis=0).tolist(),
        "mean_autocorrelation_strength": float(np.mean(strengths[voiced]))
        if np.any(voiced)
        else 0.0,
        "no_speech": bool(
            rms_db < config.VOICE_SILENCE_DB
            or voiced_ratio < config.VOICE_MIN_VOICED_RATIO
        ),
    }
    return features


def extract_wav_features(path):
    """Read a supported WAV file and return its derived feature dictionary."""
    samples, sample_rate = read_wav(path)
    return extract_features(samples, sample_rate)
