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
import math

ref_surf = cairo.ImageSurface.create_from_png("assets/reference_italian_puffin_trisuit.png")
w = ref_surf.get_width()
h = ref_surf.get_height()
stride = ref_surf.get_stride()
ref_buf = ref_surf.get_data()

# Create 6 target surfaces:
# 1. mono_surf: desaturated monochrome wireframe (all saturated tri-suit/beak/shoe/flag pixels turned into sleek dark-silver shading)
# 2. blue_surf: Google Blue (#4285F4) tri-suit pixels
# 3. red_surf: Google Red (#EA4335) tri-suit pixels
# 4. yellow_surf: Google Yellow (#FBBC05) tri-suit pixels
# 5. green_surf: Google Green (#34A853) tri-suit pixels
# 6. accents_surf: Puffin beak, eye, Italian flag on helmet, and cycling shoe

mono_surf = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
blue_surf = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
red_surf = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
yellow_surf = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
green_surf = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
accents_surf = cairo.ImageSurface(cairo.Format.ARGB32, w, h)

mono_buf = mono_surf.get_data()
blue_buf = blue_surf.get_data()
red_buf = red_surf.get_data()
yellow_buf = yellow_surf.get_data()
green_buf = green_surf.get_data()
accents_buf = accents_surf.get_data()

# Helper to check if (x, y) is in the tri-suit region vs beak/helmet/shoe
# Tri-suit bounding region: x in [510..815], y in [150..445]
def in_trisuit(x, y):
    if 510 <= x <= 815 and 150 <= y <= 445:
        # Exclude Puffin white cheek / beak / helmet (which is x > 765 and y < 235)
        if x > 768 and y < 232:
            return False
        return True
    return False

for y in range(h):
    row_off = y * stride
    for x in range(w):
        idx = row_off + x * 4
        b = ref_buf[idx]
        g = ref_buf[idx + 1]
        r = ref_buf[idx + 2]
        a = ref_buf[idx + 3]

        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c
        sat = delta / max_c if max_c > 25 else 0.0

        # Default monochrome value: luminance with subtle cool blueprint tint
        lum = int(0.299 * r + 0.587 * g + 0.114 * b)
        if sat > 0.22 and max_c > 45:
            # Darken saturated fill areas in the monochrome blueprint so only crisp structural edges & subtle shading remain!
            mono_lum = int(lum * 0.42)
            mono_buf[idx]     = min(255, int(mono_lum * 1.15)) # B
            mono_buf[idx + 1] = min(255, int(mono_lum * 1.05)) # G
            mono_buf[idx + 2] = mono_lum                       # R
            mono_buf[idx + 3] = 255
        else:
            mono_buf[idx]     = b
            mono_buf[idx + 1] = g
            mono_buf[idx + 2] = r
            mono_buf[idx + 3] = 255

        # Classify colored pixels into Google Tri-Suit colors vs Italian/Puffin accents
        if sat > 0.20 and max_c > 45:
            if in_trisuit(x, y):
                # Determine which of the 4 Google colors this pixel belongs to:
                # 1. Google Blue: b is dominant
                if b > r + 15 and b >= g - 10:
                    blue_buf[idx] = b
                    blue_buf[idx + 1] = g
                    blue_buf[idx + 2] = r
                    blue_buf[idx + 3] = 255
                # 2. Google Green: g is dominant over r and b
                elif g > r + 8 and g > b + 8:
                    green_buf[idx] = b
                    green_buf[idx + 1] = g
                    green_buf[idx + 2] = r
                    green_buf[idx + 3] = 255
                # 3. Google Yellow: both r and g are high, and g > 0.58 * r
                elif r > 110 and g > 100 and b < 130 and g > r * 0.56:
                    yellow_buf[idx] = b
                    yellow_buf[idx + 1] = g
                    yellow_buf[idx + 2] = r
                    yellow_buf[idx + 3] = 255
                # 4. Google Red: r is dominant
                elif r > g + 15 and r > b + 15:
                    red_buf[idx] = b
                    red_buf[idx + 1] = g
                    red_buf[idx + 2] = r
                    red_buf[idx + 3] = 255
                else:
                    accents_buf[idx] = b
                    accents_buf[idx + 1] = g
                    accents_buf[idx + 2] = r
                    accents_buf[idx + 3] = 255
            else:
                # Outside tri-suit (e.g., Puffin beak, eye, Italian flag on helmet, red/green cycling shoes)
                # Keep only inside subject area (x in 440..940, y in 70..620)
                if 440 <= x <= 940 and 70 <= y <= 620:
                    accents_buf[idx] = b
                    accents_buf[idx + 1] = g
                    accents_buf[idx + 2] = r
                    accents_buf[idx + 3] = 255

mono_surf.mark_dirty()
blue_surf.mark_dirty()
red_surf.mark_dirty()
yellow_surf.mark_dirty()
green_surf.mark_dirty()
accents_surf.mark_dirty()

mono_surf.write_to_png("assets/layer_mono.png")
blue_surf.write_to_png("assets/layer_google_blue.png")
red_surf.write_to_png("assets/layer_google_red.png")
yellow_surf.write_to_png("assets/layer_google_yellow.png")
green_surf.write_to_png("assets/layer_google_green.png")
accents_surf.write_to_png("assets/layer_italia_accents.png")
print("Saved all 6 decomposed color & blueprint layers!")
