#!/bin/sh
# Have Codex (`codex exec`, image generation) fill the magenta around WORK/canvas/NAME.png -> WORK/codex_out/NAME.png.
# usage: [SCENE="what to continue, what must stay out of the new areas"] codex_outpaint.sh WORK NAME...
# Results vary run to run; the strips committed in resources/vita/wide are the ones the game uses.
set -e
work=$(cd "$1" && pwd); shift
list=""; imgs=""
for n in "$@"; do list="$list canvas/$n.png"; imgs="$imgs -i canvas/$n.png"; done
mkdir -p "$work/codex_out"
cd "$work"
codex exec --skip-git-repo-check -C "$work" -s workspace-write $imgs - <<P
Outpainting job for a PS Vita port of a 2002 PC game (these are its 640x480 menu/ending backgrounds).

For EACH of these canvases:$list
- The canvas is 1536x1024 (a tall image is scaled to full height). The original artwork sits in the middle; every pure magenta (#FF00FF) pixel is empty and must be filled.
- Use your image generation tool to edit the canvas: replace ALL magenta with a natural continuation of the artwork's background (same painting style, colors, lighting, paper/canvas texture, fog, gradients). Keep the original artwork in the middle exactly where it is, same size and position. Output 1536x1024.
- ${SCENE:-Continue the scenery naturally.}
- Do NOT copy, mirror or extend any text, logos or characters into the new areas. Only continue the scenery/background.
- No visible border, frame, vignette or seam where the original meets the new area.
- Save each generated image as codex_out/<same name>.png (copy it from wherever the tool saved it). Do not resize, crop, or post-process it.
If a result still has magenta, text or extra characters in the new areas, or a visible seam, regenerate that one (at most 2 tries) and keep the best.
Do not modify any other files. Finish with one line per image: file name and any problems you noticed.
P
