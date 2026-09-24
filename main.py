import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt
import scipy.io.wavfile as wav
import librosa
import os
from dotenv import load_dotenv

def calculate_thd(signal, sampling_rate, fundamental_freq=1000.0):
    """
    Calculates Total Harmonic Distortion (THD).
    Note: Highly accurate for static tones, will yield extreme errors for sweeps.
    """
    if signal.ndim > 1:
        sig_data = signal[0, :]
    else:
        sig_data = signal

    n = len(sig_data)
    fft_vals = np.fft.rfft(sig_data)
    fft_freqs = np.fft.rfftfreq(n, d=1.0/sampling_rate)
    magnitudes = np.abs(fft_vals)
    
    fund_idx = np.argmin(np.abs(fft_freqs - fundamental_freq))
    search_radius = max(1, int(n * 0.0001))
    start_idx = max(0, fund_idx - search_radius)
    end_idx = min(len(magnitudes), fund_idx + search_radius + 1)
    peak_fund_idx = start_idx + np.argmax(magnitudes[start_idx:end_idx])
    
    fundamental_mag = magnitudes[peak_fund_idx]
    if fundamental_mag == 0:
        return 0.0

    harmonic_energy = 0.0
    max_harmonic = int(sampling_rate / (2 * fundamental_freq))
    
    for h in range(2, max_harmonic + 1):
        target_h_freq = fundamental_freq * h
        h_idx = np.argmin(np.abs(fft_freqs - target_h_freq))
        h_start = max(0, h_idx - 2)
        h_end = min(len(magnitudes), h_idx + 3)
        harmonic_energy += np.max(magnitudes[h_start:h_end]) ** 2

    thd = np.sqrt(harmonic_energy) / fundamental_mag
    return thd * 100

def calculate_waveform_metrics(reference, processed, label, sampling_rate):
    """
    Computes precise comparative statistics between the reference and processed tracks.
    """
    min_samples = min(reference.shape[1], processed.shape[1])
    ref = reference[:, :min_samples]
    pro = processed[:, :min_samples]
    
    rmse = np.sqrt(np.mean((ref - pro) ** 2)) * 100
    max_error = np.max(np.abs(ref - pro))
    ref_power = np.mean(ref ** 2)
    noise_power = np.mean((ref - pro) ** 2)
    snr_db = float('inf') if noise_power == 0 else 10 * np.log10(ref_power / noise_power)
        
    print(f"\n📊 --- METRIC REPORT: {label} ---")
    print(f"  🔹 Root Mean Square Error (RMSE): {rmse:.4f}%")
    print(f"  🔹 Max Single-Sample Drift:     {max_error:.6f} V")
    print(f"  🔹 Signal-to-Noise Ratio (SNR): {snr_db:.2f} dB")
    
    thd_value = calculate_thd(pro, sampling_rate)
    print(f"  🔹 Total Harmonic Distortion (THD): {thd_value:.6f}%")
    
    return rmse, max_error, snr_db

def amplify_and_compare_topologies():
    input_filename = os.getenv('INPUT_FILE')  
    output_filename = os.getenv('OUTPUT_FILE', 'audio/output.wav')
    
    if not input_filename or not os.path.exists(input_filename):
        print(f"❌ ERROR: Please drop your file '{input_filename}' into this folder!")
        return

    print(f"📥 Loading '{input_filename}' for true multi-topology analysis...")
    audio_data, native_fs = librosa.load(input_filename, sr=None, mono=False)
    
    if audio_data.ndim == 1:
        audio_data = np.vstack((audio_data, audio_data))
        
    num_channels, total_samples = audio_data.shape

    # Normalize baseline input
    max_source_vals = np.max(np.abs(audio_data), axis=1, keepdims=True)
    max_source_vals[max_source_vals == 0] = 1.0
    original_normalized = audio_data / max_source_vals
    
    # --- FILTER CONFIGURATION 1: CLASS BD (Gentle 4th-Order @ 20kHz) ---
    bd_cutoff = 20000  
    bd_sos = butter(N=4, Wn=bd_cutoff / (0.5 * native_fs), btype='low', analog=False, output='sos')
    matrix_bd = sosfiltfilt(bd_sos, original_normalized, axis=1)
    
    # --- FILTER CONFIGURATION 2: CLASS AD MODIFIED (Aggressive 8th-Order @ 20kHz) ---
    # UPDATED: Cutoff raised to 20kHz to match Class BD and test architectural slope deviations
    ad_cutoff = 20000  
    ad_sos = butter(N=8, Wn=ad_cutoff / (0.5 * native_fs), btype='low', analog=False, output='sos')
    matrix_ad = sosfiltfilt(ad_sos, original_normalized, axis=1)
    
    # High-fidelity timeline locking / resampling stage
    target_fs = 44100
    if native_fs != target_fs:
        bd_export = librosa.resample(matrix_bd, orig_sr=native_fs, target_sr=target_fs, res_type='soxr_hq')
        ad_export = librosa.resample(matrix_ad, orig_sr=native_fs, target_sr=target_fs, res_type='soxr_hq')
        original_plot = librosa.resample(original_normalized, orig_sr=native_fs, target_sr=target_fs, res_type='soxr_hq')
    else:
        bd_export = matrix_bd.copy()
        ad_export = matrix_ad.copy()
        original_plot = original_normalized.copy()
        
    # Symmetrical Peak Matching Execution loop
    for ch in range(num_channels):
        orig_max = np.max(np.abs(original_plot[ch, :]))
        bd_max = np.max(np.abs(bd_export[ch, :])) or 1.0
        bd_export[ch, :] = (bd_export[ch, :] / bd_max) * orig_max
        
        ad_max = np.max(np.abs(ad_export[ch, :])) or 1.0
        ad_export[ch, :] = (ad_export[ch, :] / ad_max) * orig_max
        
    # Run statistical metrics
    calculate_waveform_metrics(original_plot, bd_export, "CLASS BD DESIGN ACCURACY", target_fs)
    calculate_waveform_metrics(original_plot, ad_export, "CLASS AD DESIGN ACCURACY", target_fs)
    print("-" * 40)
    
    # Anti-pop fade stabilization
    fade_len = int(target_fs * 0.015)
    fade_window = np.linspace(0, 1, fade_len)
    for target_arr in [bd_export, ad_export]:
        target_arr[:, :fade_len] *= fade_window
        target_arr[:, -fade_len:] *= fade_window[::-1]
    
    # Export master track
    out_dir = os.path.dirname(output_filename)
    if out_dir and not os.path.exists(out_dir): os.makedirs(out_dir)
    wav.write(output_filename, target_fs, (bd_export.T * 32767).astype(np.int16))
    print(f"\n🎉 Master saved to: '{output_filename}'")
    
    # --- VISUAL DASHBOARD GENERATION AT HIGH FREQUENCY CRITICAL LIMITS ---
    view_len = int(target_fs * 0.002)  # 2ms window for microsecond accuracy
    end_sample = int(bd_export.shape[1] - fade_len - (target_fs * 0.1)) 
    t_plot = np.arange(0, view_len) / target_fs
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True, sharey=True)
    
    # Panel 1: Pure Source Track Reference
    ax1.plot(t_plot * 1000, original_plot[0, end_sample:end_sample+view_len], label="Unfiltered LEFT", color="blue", linewidth=1.5)
    ax1.plot(t_plot * 1000, original_plot[1, end_sample:end_sample+view_len], label="Unfiltered RIGHT", color="red", linestyle="--", linewidth=1)
    ax1.set_title("1. REFERENCE: High-Frequency Sweep Tail End (Raw Source Material)")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right")
    
    # Panel 2: Class BD Output
    ax2.plot(t_plot * 1000, bd_export[0, end_sample:end_sample+view_len], label="Class BD LEFT", color="green", linewidth=1.5)
    ax2.plot(t_plot * 1000, bd_export[1, end_sample:end_sample+view_len], label="Class BD RIGHT", color="purple", linestyle="--", linewidth=1)
    ax2.set_title("2. OUTPUT: Class BD Stage (Transparent Filter / 20kHz Limit Preserved)")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right")
    
    # Panel 3: Class AD Output
    ax3.plot(t_plot * 1000, ad_export[0, end_sample:end_sample+view_len], label="Class AD LEFT", color="darkcyan", linewidth=1.5)
    ax3.plot(t_plot * 1000, ad_export[1, end_sample:end_sample+view_len], label="Class AD RIGHT", color="orange", linestyle="--", linewidth=1)
    ax3.set_title("3. OUTPUT: Class AD Stage (Aggressive 20kHz Filter / 8th-Order Attenuation Slope)")
    ax3.set_xlabel("Window Timeline Segment (Milliseconds)")
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="upper right")
    
    # DYNAMIC AUTO-AXIS LOCK
    active_segment = original_plot[:, end_sample:end_sample+view_len]
    padding = 0.05
    ymin, ymax = np.min(active_segment) - padding, np.max(active_segment) + padding
    plt.ylim([ymin, ymax])
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    load_dotenv()
    amplify_and_compare_topologies()
