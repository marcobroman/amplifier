# Stereo Audio DSP Experiments

Small Python and C programs for comparing two stereo-style filter topologies:

- **Class BD**: a gentler fourth-order low-pass design.
- **Class AD**: a steeper eighth-order low-pass design.

The project generates test signals, processes audio, calculates waveform metrics, and plots the results. It is an experiment and analysis project rather than a real-time audio driver.

## Requirements

- Python 3.12 or newer
- A C compiler such as GCC (only needed for the C workflow)
- Bash, such as Git Bash on Windows (only needed for `main.sh`)

The Python dependencies are pinned in [`requirements.txt`](requirements.txt). A virtual environment is recommended.

## Setup

From the repository directory:

```bash
python -m venv env
```

Activate the environment on Windows PowerShell:

```powershell
.\env\Scripts\Activate.ps1
```

Or in Git Bash:

```bash
source env/Scripts/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Python workflow

### Generate a reference tone

Creates a two-second, 1 kHz WAV file at 44.1 kHz:

```bash
python basetone.py
```

Output: `pure_reference_tone.wav`

### Generate a logarithmic sweep

Creates a five-second sweep from 20 Hz to 22 kHz:

```bash
python sweep.py
```

Output: `audio/pure_sweep.wav`

### Process an input WAV

Set the input and output paths before running `main.py`.

PowerShell:

```powershell
$env:INPUT_FILE = "audio/pure_sweep.wav"
$env:OUTPUT_FILE = "audio/output.wav"
python main.py
```

Git Bash:

```bash
INPUT_FILE="audio/pure_sweep.wav" OUTPUT_FILE="audio/output.wav" python main.py
```

`main.py` loads the source without changing its original sample rate, normalizes each channel, applies both filter designs, resamples the results to 44.1 kHz when necessary, prints RMSE/SNR/THD metrics, and writes the Class BD output to `audio/output.wav`. It also opens a three-panel waveform dashboard.

If `OUTPUT_FILE` is omitted, the default is `audio/output.wav`.

## C streaming-style workflow

This workflow synthesizes a two-second logarithmic sweep in C, processes it in 512-frame blocks, and records a short high-frequency window for comparison.

Generate the source sweep first:

```bash
python sweep.py
```

Then compile and run the C program:

```bash
gcc main.c -o audio_analyzer -lm
./audio_analyzer
```

On Windows, run those commands from Git Bash. The existing helper script performs the same steps and sets the input/output environment variables:

```bash
./main.sh
```

Output: `audio/dashboard_data.csv`

Plot the CSV data with:

```bash
python plot.py
```

## Repository layout

| File | Purpose |
| --- | --- |
| `main.py` | Python filtering, resampling, metrics, and dashboard |
| `main.c` | Block-based C filter simulation and CSV telemetry |
| `main.sh` | Git Bash helper for compiling and running `main.c` |
| `basetone.py` | Generates a 1 kHz reference tone |
| `sweep.py` | Generates the logarithmic sweep input |
| `plot.py` | Plots `audio/dashboard_data.csv` |
| `audio/` | Generated audio and CSV files |

## Notes

- The Python analysis is designed for offline comparison. It does not capture audio from a sound card or stream to hardware.
- `main.py` currently exports the Class BD result as the WAV master; the Class AD result is used for metrics and visualization.
- The THD calculation is intended for static tones and is not reliable as a distortion measure for frequency sweeps.
- The C program uses filter coefficients embedded in `main.c`; changing the Python filter settings does not automatically update the C coefficients.
- Generated files such as WAV output, CSV telemetry, plots, and the compiled `audio_analyzer` binary can be removed and regenerated at any time.
