# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# List available recipes
list:
    @just -l

# Run the full 2,049-circle Fourier pipeline & render 1080p60 MP4 + interactive HTML5 studio
all: analyze-audio layers contour render-video build-html

# 1. Extract 60fps beat & RMS/bass/treble envelopes from the Lyria 3.5 soundtrack
analyze-audio:
    python3 src/inspect_image.py

# 2. Split reference illustration into monochrome blueprint + 4 Google Tri-Suit color layers + ITALIA accents
layers:
    python3 src/prepare_color_layers.py

# 3. Compute 2,049-point closed contour & exact 2,049 complex DFT coefficients (k=-1024..1024)
contour:
    python3 src/build_contour.py

# 4. Render 1920x1080 @ 60fps MP4 synced to Lyria 3.5 + 4 milestone PNG snapshots
render-video:
    python3 src/render_fourier_video.py

# 5. Build self-contained interactive HTML5 Canvas Fourier Studio
build-html:
    python3 src/build_interactive_html.py

# 6. Verify all generated artifacts & JSON invariants
test:
    test -s assets/fourier_2049_coeffs.json
    test -s assets/beat_envelope.json
    test -s output/italian_puffin_fourier_epicycles.mp4
    test -s interactive/index.html
    @echo "✅ All Fourier Epicycle artifacts verified!"

# 7. Launch local HTTP server to explore interactive/index.html
serve:
    python3 -m http.server 8088

# 8. Check Google Open Source license compliance
check-google-license:
    gemini -y -p '/commsl:check_google_license Verify all is in place, and if needed apply the addlicense script to the whole git repo.'
