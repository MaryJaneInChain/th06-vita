# Touhou 6 (EoSD) Vita Port

This is a port of Touhou Koumakyou ~ the Embodiment of Scarlet Devil (東方紅魔郷　～ the Embodiment of Scarlet Devil) to the Playstation Vita using [GensokyoClub's portable EoSD decompilation](https://github.com/GensokyoClub/th06/tree/portable).

This fork adds support for the Chinese (汉化) patch, along with a few other changes:
 - Text from the Chinese patch shows up properly, in the same SimSun bitmap font the patched game uses on Windows
 - The game fills the whole screen (960x544) instead of a 640x480 box in the middle. The bars on the sides are filled in, and the title, menu and ending backgrounds are widened to 16:9
 - Music defaults to WAV, since MIDI doesn't make any sound on the Vita
 - No FPS counter, and no vitaGL logo when it boots
 - The original Japanese release and English data still work, you just pick which one when building

## Installation
You must own a legally obtained install of EoSD (v1.02h), as well as a font from your Windows install (see step 5). From there:

 1. Build the VPK (see [Building](#building)). This fork doesn't have any releases yet.
 2. Copy the VPK to somewhere convenient on your Vita so you can install it.
 3. Create a `th06` folder in your `data` folder on your Vita.
 4. Copy the following files and folders from your EoSD install directory to the `th06` folder you just made on your Vita:
```
bgm/
紅魔郷CM.DAT
紅魔郷ED.DAT
紅魔郷IN.DAT
紅魔郷MD.DAT
紅魔郷ST.DAT
紅魔郷TL.DAT
```
   If you're using English data, copy the `KOUMAKYO_*.dat` files instead.

5. Copy a font to the `th06` folder you just made on your Vita:
   - Chinese: `simsun.ttc` (SimSun). That's what the Chinese patch draws its text with, and MS Gothic is missing most simplified Chinese characters.
   - Japanese / English: `msgothic.ttc` (or any other compatible font).
6. (On your Vita) Install the VPK.
7. Enjoy!

The widened backgrounds don't contain any of the game's own images. The VPK only has the extra bits for the left and right (outpainted with an image model), and the game puts your own copy of each background in the middle when it loads it. Those bits were made to match the Chinese patch's backgrounds, so if you're using other data, a background the patch changed might not line up perfectly.

## Known Issues

 - Performance isn't perfect. It can hold 60FPS most of the time (at least on Normal difficulty) but it can dip when things get hectic or when using bombs, and stage 5 can get pretty bad. I suggest playing with an overclock for the time being until I can fix it.
 - Some minor graphical bugs
	 - The blurred game window on a pause is offset vertically
	 - Remilia's spell card background has a light blue tint that isn't meant to be there
 - With the Chinese patch, a few names are written into the game itself rather than the data files, so they still show up in Japanese
 - The Japanese and English builds of this fork haven't been tested on a real Vita yet

If you run into any other problems with this port, open an issue!

## Building
The easiest way to build is with the VitaSDK container image, which already has VitaGL and SDL2 set up. Run the following in your terminal (`docker` works the same as `podman`):
```
git clone -b vita-chinese-widescreen https://github.com/MaryJaneInChain/th06-vita.git
cd th06-vita
podman run --rm -v "$PWD":/work -w /work docker.io/vitasdk/vitasdk:2026.08 \
  sh -c 'cmake -S . -B build && cmake --build build'
```
The VPK ends up at `build/th06-vita.vpk`. As long as you use that exact image (`2026.08`), you get the exact same VPK, byte for byte, no matter where you cloned it.

By default the VPK is for the Chinese patch. For the original Japanese release or English data, add `-DTH06_LANG=JP` or `-DTH06_LANG=EN` to the first `cmake`.

If you'd rather not use the container: alongside VitaSDK, you must have [VitaGL](https://github.com/Rinnegatamante/vitaGL/) and [Northfear's SDL2](https://github.com/Northfear/SDL) fork compiled and installed, as well as Python 3.

You don't need anything extra for the widened backgrounds, since the side bits are already in the repo (`resources/vita/wide`). If you want to remake them, the tools are in `tools/widescreen` (see the top of `widescreen.py`).

## Special Thanks
- [Wavy667](https://github.com/Wavy667) for the [Vita port](https://github.com/Wavy667/th06-vita) this fork is built on
- [GensokyoClub](https://github.com/GensokyoClub) for their [EoSD decompilation](https://github.com/GensokyoClub/th06)
- [Swiizyu](https://github.com/Swiizyu) for their [Switch port](https://github.com/Swiizyu/th06-switch) and solution to fix elements rendering offscreen
- ZUN for making Touhou!

### Below is the original repos README verbatim:

[![Discord][discord-badge]][discord] <- click here to join discord server.

[discord]: https://discord.gg/VyGwAjrh9a
[discord-badge]: https://img.shields.io/discord/1147558514840064030?color=%237289DA&logo=discord&logoColor=%23FFFFFF

This is the readme for the portable fork of EoSD. For the readme of the decomp project, see [here](https://github.com/GensokyoClub/th06/blob/master/README.md).

EoSD-portable is a port of Touhou 6 using SDL2 and OpenGL (with a more general renderer abstraction layer hopefully on the way).
This enables theoretical portability to any system supported by SDL2, with Linux and Windows in particular being known to work.
Builds for OS X, the BSDs, and other Unices are also almost certainly possible, but may require some slight modifications to the build system.

### Platform Requirements

- SDL2, SDL2-image, and SDL2-ttf support
- C++20 standard library support
- A little endian architecture (though big endian support is currently being worked on)
- OpenGL ES 1.1, OpenGL 1.3, or GL ES 2.0 / WebGL support

### Dependencies

EoSD-portable has the following dependencies:

- `SDL2`
- `SDL2_image`
- `SDL2_ttf`
- `libasound` (Optional and Linux-only, enables MIDI support. This will almost always be present as part of a desktop distro.)

In addition, building uses [`premake5`](https://premake.github.io/download) and a compiler that supports C++20.

#### Building

In the repository root directory, run `premake5` with the desired build system as an argument (a list can be seen by running `premake5 --help`).
This will output the build files to the `build` directory, and then compilation may be done with the desired build system.

##### Build Options (Use with Premake Invocation)
`--no-asoundlib`: On Linux, doesn't build MIDI support. Removes libasound as a dev and runtime dependency
`--use-c23-embed`: Uses `#embed` for resource inclusion instead of a lua script in the Premake file.

##### Build Example (Debian-based Linux)

Obtain dependencies:

`sudo apt install build-essential libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev libasound2-dev`

Generate makefile:

`premake5 gmake`

Compile:

`cd build && make -j16`

### Use

EoSD-portable is designed to be a drop-in replacement for the vanilla EoSD binary.
You will also need to add a font to your game directory with the filename `msgothic.ttc`.
This may be the actual MS Gothic, taken from a Windows machine, or a compatible font such as Kochi Gothic.
EoSD-portable uses the Japanese filenames (e.g. 紅魔郷CM.DAT, 東方紅魔郷.cfg). English and other patches, static or thcrap, do not currently work.
A Japanese locale is not required.

# Decomp Credits

We would like to extend our thanks to the following individuals for their
invaluable contributions:

- @EstexNT for porting the [`var_order` pragma](scripts/pragma_var_order.cpp) to
  MSVC7.
