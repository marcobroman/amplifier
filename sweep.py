import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import chirp

fs = 44100
duration = 5.0  # 5 seconds long
t = np.linspace(0, duration, int(fs * duration), endpoint=False)

# Generate a sweep sliding logarithmically from 20 Hz up to 22,000 Hz
sweep_tone = chirp(t, f0=20, f1=22000, t1=duration, method='logarithmic')

# Save the pure reference sweep
wav.write("audio/pure_sweep.wav", fs, (sweep_tone * 32767).astype(np.int16))
print("Generated audio/pure_sweep.wav successfully!")
