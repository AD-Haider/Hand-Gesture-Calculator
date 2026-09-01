# Hand Gesture Game

An interactive math balancing game that uses **OpenCV** and **MediaPipe** hand tracking. Drag numbers and operators into empty chambers using pinch gestures to make both sides of the equation equal.

## How It Works

```
Available tiles (scattered at top):
  [3]  [+]  [5]  [8]  [*]  [12]  [-]  [7]  [2]

Equation chambers (center):
  [ ? ]  [ ? ]  [ ? ]  =  [ ? ]
    ↑      ↑      ↑         ↑
   num    op    num        num

Goal: drag 3, +, 5, 8 → makes  3 + 5 = 8  ✓
```

## Setup

```bash
pip install -r requirements.txt
python math_puzzle_game.py
```

> **Requires a webcam.** The game uses your camera for hand tracking.

## Controls

| Action | How |
|---|---|
| Move cursor | Point your **index finger** at the camera |
| Grab a tile | **Pinch** — bring thumb and index finger together |
| Drop a tile | **Release** the pinch over a chamber |
| Check answer | Press **C** |
| Reset puzzle | Press **R** |
| Next puzzle | Press **N** |
| Quit | Press **Q** |

## Game Mechanics

- **Levels auto-increase** every 3 solved puzzles
- **Level 1–2**: Simple equations → `A op B = C`
- **Level 3+**: Two-sided equations → `A op B = C op D`
- **Scoring**: `10 × level` points per correct answer
- **Distractors**: Extra wrong tiles are mixed in to make it harder
- Correct answer → celebration animation with particles
- Wrong answer → tiles reset, try again

## Architecture

```
math_puzzle_game.py
├── HandTracker      — MediaPipe hand detection + pinch gesture
├── Tile             — Draggable number/operator element
├── Chamber          — Drop zone for tiles
├── generate_puzzle  — Random equation generator with distractors
└── MathPuzzleGame   — Main game loop, rendering, scoring
```

## Troubleshooting

| Issue | Fix |
|---|---|
| "Cannot open webcam" | Check camera permissions, try a different camera index in `cv2.VideoCapture(0)` → try `1` or `2` |
| Hand not detected | Ensure good lighting, keep hand 30–60 cm from camera |
| Laggy performance | Close other camera apps, reduce `WINDOW_W`/`WINDOW_H` in the config section |
