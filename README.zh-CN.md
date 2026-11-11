# 东方红魔乡 Vita 移植版

[English](README.md) | 简体中文

这是《东方红魔乡 ～ the Embodiment of Scarlet Devil》（東方紅魔郷　～ the Embodiment of Scarlet Devil）的 PS Vita 移植版，基于 [GensokyoClub 的 EoSD 跨平台反编译](https://github.com/GensokyoClub/th06/tree/portable)。

这个 fork 加上了对汉化版的支持，另外还有几处改动：
 - 汉化版的文字能正常显示，用的是和汉化版在 Windows 上一样的宋体点阵字
 - 画面铺满整个屏幕（960x544），不再只是中间一块 640x480。两侧的黑边会填上，标题、菜单和结局的背景也扩成了 16:9
 - 音乐默认用 WAV，因为 MIDI 在 Vita 上没有声音
 - 去掉了 FPS 显示和开机时的 vitaGL 标志
 - 日文原版和英文数据依然能用，编译时选一个就行

## 安装
你需要一份正版的东方红魔乡（v1.02h），以及 Windows 里的字体文件（见第 5 步）。然后：

 1. 编译出 VPK（见[编译](#编译)）。这个 fork 暂时还没有发布版。
 2. 把 VPK 拷到 Vita 上方便安装的地方。
 3. 在 Vita 的 `data` 文件夹里新建一个 `th06` 文件夹。
 4. 把游戏目录里的下列文件和文件夹拷到刚建好的 `th06` 文件夹里：
```
bgm/
紅魔郷CM.DAT
紅魔郷ED.DAT
紅魔郷IN.DAT
紅魔郷MD.DAT
紅魔郷ST.DAT
紅魔郷TL.DAT
```
   如果用的是英文数据，就改拷 `KOUMAKYO_*.dat` 这几个文件。

5. 把字体拷到同一个 `th06` 文件夹里：
   - 汉化版：`simsun.ttc`（宋体）。汉化版本来就是用宋体显示文字的，而 MS Gothic 缺很多简体字。
   - 日文版 / 英文版：`msgothic.ttc`（或其他兼容的字体）。
6. （在 Vita 上）安装 VPK。
7. 开玩！

扩宽的背景里不含游戏自己的图片。VPK 里只有左右两侧多出来的部分（用图像模型外扩出来的），游戏加载背景时，会把你自己数据里的那张图放到中间。两侧是照着汉化版的背景做的，所以用别的版本的数据时，如果某张背景被汉化改过，可能会对不太齐。

## 已知问题

 - 性能还不完美。大多数时候能跑满 60 帧（至少在 Normal 难度下），但弹幕密集或放炸弹时会掉帧，第 5 面会掉得比较厉害。原移植作者建议暂时超频玩，等他修好。
 - 一些小的画面问题
	 - 暂停时背后模糊的游戏画面上下有偏移
	 - 蕾米莉亚的符卡背景带着一层本不该有的浅蓝色
 - 汉化版里有几个名字是写死在程序里的，不在数据文件中，所以仍然显示日文
 - 这个 fork 的日文版和英文版还没在真机上测过

遇到其他问题，欢迎开 issue！

## 编译
最省事的办法是用 VitaSDK 的容器镜像，里面已经配好了 VitaGL 和 SDL2。在终端里运行下面这些（`docker` 和 `podman` 用法一样）：
```
git clone -b vita-chinese-widescreen https://github.com/MaryJaneInChain/th06-vita.git
cd th06-vita
podman run --rm -v "$PWD":/work -w /work docker.io/vitasdk/vitasdk:2026.08 \
  sh -c 'cmake -S . -B build && cmake --build build'
```
VPK 会生成在 `build/th06-vita.vpk`。只要用的是同一个镜像（`2026.08`），不管克隆到哪个目录，编出来的 VPK 都逐字节相同。

默认编出来的是汉化版用的 VPK。要用日文原版或英文数据，就在第一条 `cmake` 后面加上 `-DTH06_LANG=JP` 或 `-DTH06_LANG=EN`。

不想用容器的话：除了 VitaSDK，还需要编译并安装 [VitaGL](https://github.com/Rinnegatamante/vitaGL/) 和 [Northfear 的 SDL2](https://github.com/Northfear/SDL) fork，以及 Python 3。

扩宽背景不需要额外准备，两侧的图已经在仓库里了（`resources/vita/wide`）。想重新生成的话，工具在 `tools/widescreen` 里（用法见 `widescreen.py` 开头）。

## 致谢
- [Wavy667](https://github.com/Wavy667)，这个 fork 所基于的 [Vita 移植](https://github.com/Wavy667/th06-vita)
- [GensokyoClub](https://github.com/GensokyoClub) 的 [EoSD 反编译](https://github.com/GensokyoClub/th06)
- [Swiizyu](https://github.com/Swiizyu) 的 [Switch 移植](https://github.com/Swiizyu/th06-switch)，以及解决元素画到屏幕外的办法
- ZUN 创作了东方！

原反编译项目（EoSD-portable）自己的说明，见英文 README 末尾的[原文](README.md#below-is-the-original-repos-readme-verbatim)。
