import numpy as np
import scipy.io.wavfile as wav

def generate_pure_reference():
    print("Generating pure mathematical analog tone...")
    
    # 1. Standard CD Quality parameters
    target_fs = 44100    # 44.1 kHz standard audio sample rate
    f_signal = 1000      # 1 kHz test audio tone
    duration = 2.0       # 2 seconds long
    
    # 2. Generate a mathematically perfect, continuous sine wave
    t = np.arange(0, duration, 1/target_fs)
    pure_signal = np.sin(2 * np.pi * f_signal * t)
    
    # 3. Export directly to WAV (No digital switching loops, 0% distortion)
    wav.write("pure_reference_tone.wav", target_fs, (pure_signal * 32767).astype(np.int16))
    print("🔊 SUCCESS: Pure reference file saved as 'pure_reference_tone.wav'!")

if __name__ == "__main__":
    generate_pure_reference()
