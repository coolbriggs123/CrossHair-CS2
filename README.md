```markdown
# 🎯 Crosshair Overlay (CS2 Compatible)

**Crosshair Overlay** is a dynamic and customizable crosshair overlay designed primarily for CS2. It provides a lightweight fullscreen overlay that is click-through, supports movement-based spread, counter-strafe logic, click jitter, and more — all configurable through a built-in UI.

https://i.imgur.com/0Z2PgAi.png

---

## 🔧 Features

- ✅ Transparent fullscreen overlay  
- ✅ Starts only when `cs2.exe` is running  
- ✅ WASD-based movement spread simulation  
- ✅ Counter-strafe detection and reduction  
- ✅ Click spread and jitter effects  
- ✅ Fully customizable via an in-app configuration menu (press `F1`)  
- ✅ Custom color, size, thickness, and spread options  
- ✅ Persistent config (`config.json`)  
- ✅ Click-through support via Windows API  

---

## 🖥️ Screenshots

> Include images of the overlay and the customization menu here for best effect.

---

## 🚀 Getting Started

### 📅 Installation

1. Download `crosshair_overlay.exe` from the [Releases](https://github.com/yourusername/crosshair-overlay/releases).
2. Launch **CS2**.
3. Run `crosshair_overlay.exe`.
4. Press `F1` to open the crosshair customization menu.

---

## ⚙️ Configuration

All settings are saved in `config.json`. You can edit this manually or through the in-app UI:

### Editable Options

- `crosshair_color`: `[R, G, B, A]`
- `outline_color`: `[R, G, B, A]`
- `line_thickness`: `int`
- `gap`: `int`
- `length`: `int`
- `movement_spread_enabled`: `bool`
- `click_spread_enabled`: `bool`
- `jitter_enabled`: `bool`
- ...and more!

---

## 👟 Controls

| Key         | Action                          |
| ----------- | ------------------------------- |
| F1          | Open/close settings menu        |
| ESC         | (Disabled for accidental exits) |
| WASD        | Movement spread simulation      |
| Mouse Click | Trigger jitter/click spread     |

---

## 📁 File Structure


crosshair_overlay.exe       # Compiled executable
config.json                 # Saved config
assets/icon.png             # App icon (optional)
README.md                   # This file


---

## ✅ TODO

- [ ] Add screenshots/GIFs
- [ ] Add Linux support
- [ ] Add preset profiles
- [ ] Export/import configs

---

## 📜 License

MIT License. See [LICENSE](./LICENSE).

---

## ✨ Credits

Made by [Your Name / Alias].  
A fully dynamic and lightweight overlay for CS2 players.
```
