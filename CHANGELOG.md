# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-11-03

### 🐧🚴‍♂️🇮🇹 Added
- Initial public release of `public-demos-fourier-epicycle-italian-puffin`:
  - `src/build_contour.py`: 2,049-point closed complex contour & Discrete Fourier Transform (DFT) solver ($k \in [-1024, +1024]$).
  - `src/prepare_color_layers.py`: Chromatic layer splitter isolating the stealth monochrome blueprint, the 4 Google Colors (`#4285F4`, `#EA4335`, `#FBBC05`, `#34A853`) on the Puffin's tri-suit, and `"ITALIA" 🇮🇹` helmet/beak accents.
  - `src/inspect_image.py`: 60fps RMS, low-bass, and high-onset audio envelope extractor for the 120 BPM Google Lyria 3.5 soundtrack.
  - `src/render_fourier_video.py`: PyCairo + FFmpeg 1080p 60fps slow-reveal video renderer with 4.5x Tip Harmonic Microscope Loupe.
  - `src/build_interactive_html.py` & `interactive/index.html`: Self-contained HTML5 Canvas studio for scrubbing harmonics `M = 2 .. 2,049` in real time.
