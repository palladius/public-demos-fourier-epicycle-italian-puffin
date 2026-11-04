# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent

import cairo
import subprocess
import wave
import array
import math
import json

surf = cairo.ImageSurface.create_from_png("assets/reference_italian_puffin_trisuit.png")
w = surf.get_width()
h = surf.get_height()
stride = surf.get_stride()
data = surf.get_data()
print(f"Reference image dimensions: {w}x{h}, stride={stride}, format={surf.get_format()}")

# Also convert MP3 to 44.1kHz mono WAV using ffmpeg and analyze its energy per 1/60s frame
subprocess.run([
    "ffmpeg", "-y", "-i", "assets/soundtrack_lyria35.mp3",
    "-ac", "1", "-ar", "44100", "assets/audio_mono.wav"
], check=True, capture_output=True)

with wave.open("assets/audio_mono.wav", "rb") as wf:
    n_samples = wf.getnframes()
    sr = wf.getframerate()
    raw = wf.readframes(n_samples)
    samples = array.array("h", raw)

duration = n_samples / sr
fps = 60
n_frames = int(duration * fps)
samples_per_frame = sr // fps

rms_list = []
low_list = []
high_list = []

for f in range(n_frames):
    start = f * samples_per_frame
    end = min(n_samples, start + samples_per_frame)
    chunk = samples[start:end]
    if not chunk:
        rms_list.append(0.0)
        low_list.append(0.0)
        high_list.append(0.0)
        continue
    # RMS
    s2 = sum(x * x for x in chunk) / len(chunk)
    rms = math.sqrt(s2) / 32768.0
    # High-frequency energy (first difference)
    diff2 = sum((chunk[i] - chunk[i-1])**2 for i in range(1, len(chunk))) / max(1, len(chunk)-1)
    high = math.sqrt(diff2) / 32768.0
    # Low-frequency energy (moving average of 16 samples)
    step = 16
    low_s2 = 0.0
    cnt = 0
    for i in range(0, len(chunk) - step, step):
        avg = sum(chunk[i:i+step]) / step
        low_s2 += avg * avg
        cnt += 1
    low = (math.sqrt(low_s2 / max(1, cnt)) / 32768.0)
    rms_list.append(rms)
    low_list.append(low)
    high_list.append(high)

max_rms = max(rms_list) or 1.0
max_low = max(low_list) or 1.0
max_high = max(high_list) or 1.0

rms_norm = [round(x / max_rms, 4) for x in rms_list]
low_norm = [round(x / max_low, 4) for x in low_list]
high_norm = [round(x / max_high, 4) for x in high_list]

# Print average RMS per 1-second window to verify Act 1, Act 2, Act 3 dynamics
print(f"Total audio duration: {duration:.2f}s ({n_frames} frames @ 60fps)")
for sec in range(int(duration)):
    slice_rms = rms_norm[sec*60:(sec+1)*60]
    avg_r = sum(slice_rms)/len(slice_rms) if slice_rms else 0
    bar = "#" * int(avg_r * 40)
    print(f"t={sec:02d}s: {avg_r:.3f} | {bar}")

with open("assets/beat_envelope.json", "w") as f:
    json.dump({
        "duration": duration,
        "fps": fps,
        "n_frames": n_frames,
        "rms": rms_norm,
        "low": low_norm,
        "high": high_norm
    }, f)
print("Saved assets/beat_envelope.json")
