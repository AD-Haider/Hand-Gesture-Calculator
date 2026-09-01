# """
# ╔══════════════════════════════════════════════════════════════╗
# ║          MATH PUZZLE - Hand Gesture Game                     ║
# ║   Use your hand to drag numbers & operators into chambers    ║
# ║   to balance the equation!                                   ║
# ╚══════════════════════════════════════════════════════════════╝

# Controls:
#   - Move index finger to hover over tiles
#   - PINCH (thumb + index finger close) to grab a tile
#   - Drag to a chamber and release to place it
#   - Press 'c' to check your answer
#   - Press 'r' to reset the current puzzle
#   - Press 'n' to skip to next puzzle
#   - Press 'q' to quit

# Requirements:
#   pip install opencv-python mediapipe numpy
# """

# import cv2
# import numpy as np
# import random
# import time
# import math
# import os
# import sys
# import urllib.request

# # ─────────────────────────────────────────────────────────────
# # MEDIAPIPE COMPATIBILITY LAYER
# # Supports both old (mp.solutions) and new (mp.tasks) APIs
# # ─────────────────────────────────────────────────────────────
# import mediapipe as mp

# USE_NEW_API = not hasattr(mp, "solutions") or not hasattr(getattr(mp, "solutions", None) or object(), "hands")

# MODEL_FILENAME = "hand_landmarker.task"
# MODEL_URL = (
#     "https://storage.googleapis.com/mediapipe-models/"
#     "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
# )


# def _download_model(dest_path: str):
#     """Download the HandLandmarker model file if missing."""
#     if os.path.exists(dest_path):
#         return dest_path
#     print(f"[INFO] Downloading hand landmark model → {dest_path}")
#     print(f"       (one-time download, ~10 MB)")
#     try:
#         urllib.request.urlretrieve(MODEL_URL, dest_path)
#         print("       ✅ Download complete.")
#     except Exception as e:
#         print(f"       ❌ Download failed: {e}")
#         print("       Manually download from:")
#         print(f"         {MODEL_URL}")
#         print(f"       and place it as: {dest_path}")
#         sys.exit(1)
#     return dest_path


# # ─────────────────────────────────────────────────────────────
# # CONFIGURATION
# # ─────────────────────────────────────────────────────────────
# WINDOW_W, WINDOW_H = 1280, 720
# TILE_SIZE = 70
# CHAMBER_SIZE = 75
# FPS = 30

# # Color palette (BGR)
# COL_BG           = (30, 30, 30)
# COL_TILE_NUM     = (200, 140, 50)      # blue-ish for numbers
# COL_TILE_OP      = (50, 140, 200)      # orange-ish for operators
# COL_TILE_HOVER   = (100, 220, 100)     # green highlight
# COL_TILE_GRAB    = (80, 80, 255)       # red when grabbed
# COL_CHAMBER      = (80, 80, 80)        # empty chamber
# COL_CHAMBER_FILL = (60, 120, 60)       # filled chamber
# COL_TEXT         = (255, 255, 255)
# COL_EQUALS       = (180, 180, 180)
# COL_CORRECT      = (80, 220, 80)
# COL_WRONG        = (60, 60, 230)
# COL_SCORE        = (0, 215, 255)
# COL_CURSOR       = (0, 255, 255)


# # ─────────────────────────────────────────────────────────────
# # HAND TRACKER — works with both old and new MediaPipe
# # ─────────────────────────────────────────────────────────────
# class HandTracker:
#     def __init__(self):
#         self.index_pos = None
#         self.is_pinching = False
#         self._frame_count = 0

#         if USE_NEW_API:
#             self._init_new_api()
#         else:
#             self._init_old_api()

#     # ── New API (mediapipe >= 0.10.9) ────────────────────────
#     def _init_new_api(self):
#         print("[INFO] Using new MediaPipe Tasks API (v0.10.9+)")
#         model_path = _download_model(
#             os.path.join(os.path.dirname(os.path.abspath(__file__)), MODEL_FILENAME)
#         )

#         BaseOptions = mp.tasks.BaseOptions
#         HandLandmarker = mp.tasks.vision.HandLandmarker
#         HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
#         RunningMode = mp.tasks.vision.RunningMode

#         options = HandLandmarkerOptions(
#             base_options=BaseOptions(model_asset_path=model_path),
#             running_mode=RunningMode.VIDEO,
#             num_hands=1,
#             min_hand_detection_confidence=0.7,
#             min_hand_presence_confidence=0.5,
#             min_tracking_confidence=0.5,
#         )
#         self._landmarker = HandLandmarker.create_from_options(options)
#         self._connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS

#     # ── Old API (mediapipe < 0.10.9) ─────────────────────────
#     def _init_old_api(self):
#         print("[INFO] Using legacy MediaPipe Solutions API")
#         self._hands = mp.solutions.hands.Hands(
#             static_image_mode=False,
#             max_num_hands=1,
#             min_detection_confidence=0.7,
#             min_tracking_confidence=0.6,
#         )
#         self._mp_draw = mp.solutions.drawing_utils
#         self._hand_conns = mp.solutions.hands.HAND_CONNECTIONS

#     def process(self, frame):
#         """Process a BGR frame, update index_pos and is_pinching, draw skeleton."""
#         self._frame_count += 1
#         self.index_pos = None
#         self.is_pinching = False
#         h, w, _ = frame.shape

#         if USE_NEW_API:
#             self._process_new(frame, w, h)
#         else:
#             self._process_old(frame, w, h)

#         return frame

#     def _process_new(self, frame, w, h):
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
#         timestamp_ms = int(self._frame_count * (1000 / FPS))

#         result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

#         if result.hand_landmarks and len(result.hand_landmarks) > 0:
#             landmarks = result.hand_landmarks[0]  # first hand

#             # Index finger tip (landmark 8)
#             ix = int(landmarks[8].x * w)
#             iy = int(landmarks[8].y * h)
#             self.index_pos = (ix, iy)

#             # Thumb tip (landmark 4)
#             tx = int(landmarks[4].x * w)
#             ty = int(landmarks[4].y * h)

#             dist = math.hypot(ix - tx, iy - ty)
#             self.is_pinching = dist < 45

#             # Draw skeleton
#             self._draw_skeleton_new(frame, landmarks, w, h)

#     def _draw_skeleton_new(self, frame, landmarks, w, h):
#         """Draw hand skeleton using new API landmarks."""
#         pts = []
#         for lm in landmarks:
#             px, py = int(lm.x * w), int(lm.y * h)
#             pts.append((px, py))
#             cv2.circle(frame, (px, py), 3, (60, 60, 60), -1)

#         # Draw connections
#         for conn in self._connections:
#             start_idx = conn.start
#             end_idx = conn.end
#             if start_idx < len(pts) and end_idx < len(pts):
#                 cv2.line(frame, pts[start_idx], pts[end_idx], (90, 90, 90), 1)

#     def _process_old(self, frame, w, h):
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = self._hands.process(rgb)

#         if results.multi_hand_landmarks:
#             hand = results.multi_hand_landmarks[0]

#             ix = int(hand.landmark[8].x * w)
#             iy = int(hand.landmark[8].y * h)
#             self.index_pos = (ix, iy)

#             tx = int(hand.landmark[4].x * w)
#             ty = int(hand.landmark[4].y * h)

#             dist = math.hypot(ix - tx, iy - ty)
#             self.is_pinching = dist < 45

#             self._mp_draw.draw_landmarks(
#                 frame, hand, self._hand_conns,
#                 self._mp_draw.DrawingSpec(color=(50, 50, 50), thickness=1, circle_radius=2),
#                 self._mp_draw.DrawingSpec(color=(100, 100, 100), thickness=1),
#             )


# # ─────────────────────────────────────────────────────────────
# # TILE (draggable number / operator)
# # ─────────────────────────────────────────────────────────────
# class Tile:
#     def __init__(self, value: str, x: int, y: int, is_operator: bool = False):
#         self.value = value
#         self.home_x, self.home_y = x, y
#         self.x, self.y = x, y
#         self.w, self.h = TILE_SIZE, TILE_SIZE
#         self.is_operator = is_operator
#         self.grabbed = False
#         self.placed_in = None

#     @property
#     def cx(self):
#         return self.x + self.w // 2

#     @property
#     def cy(self):
#         return self.y + self.h // 2

#     def contains(self, px, py):
#         return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

#     def reset_position(self):
#         self.x, self.y = self.home_x, self.home_y
#         if self.placed_in:
#             self.placed_in.tile = None
#             self.placed_in = None

#     def draw(self, canvas):
#         color = COL_TILE_OP if self.is_operator else COL_TILE_NUM
#         if self.grabbed:
#             color = COL_TILE_GRAB

#         # Tile background
#         cv2.rectangle(canvas, (self.x, self.y),
#                       (self.x + self.w, self.y + self.h), color, -1)
#         # Border
#         cv2.rectangle(canvas, (self.x, self.y),
#                       (self.x + self.w, self.y + self.h), COL_TEXT, 2)
#         # Shadow effect
#         cv2.rectangle(canvas, (self.x + 3, self.y + 3),
#                       (self.x + self.w + 3, self.y + self.h + 3), (20, 20, 20), -1)
#         cv2.rectangle(canvas, (self.x, self.y),
#                       (self.x + self.w, self.y + self.h), color, -1)
#         cv2.rectangle(canvas, (self.x, self.y),
#                       (self.x + self.w, self.y + self.h), COL_TEXT, 2)

#         # Value text
#         font = cv2.FONT_HERSHEY_SIMPLEX
#         scale = 1.0 if len(self.value) <= 2 else 0.65
#         (tw, th), _ = cv2.getTextSize(self.value, font, scale, 2)
#         tx = self.x + (self.w - tw) // 2
#         ty = self.y + (self.h + th) // 2
#         cv2.putText(canvas, self.value, (tx, ty), font, scale, COL_TEXT, 2, cv2.LINE_AA)


# # ─────────────────────────────────────────────────────────────
# # CHAMBER (drop zone)
# # ─────────────────────────────────────────────────────────────
# class Chamber:
#     def __init__(self, x: int, y: int, label: str = "?"):
#         self.x, self.y = x, y
#         self.w, self.h = CHAMBER_SIZE, CHAMBER_SIZE
#         self.tile = None
#         self.label = label

#     @property
#     def cx(self):
#         return self.x + self.w // 2

#     @property
#     def cy(self):
#         return self.y + self.h // 2

#     def contains(self, px, py):
#         return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

#     def draw(self, canvas):
#         col = COL_CHAMBER_FILL if self.tile else COL_CHAMBER

#         # Chamber background
#         cv2.rectangle(canvas, (self.x, self.y),
#                       (self.x + self.w, self.y + self.h), col, -1)

#         # Dashed border effect
#         border_col = COL_CORRECT if self.tile else (140, 140, 140)
#         thickness = 2
#         dash_len = 10
#         # Top & bottom
#         for sx in range(self.x, self.x + self.w, dash_len * 2):
#             ex = min(sx + dash_len, self.x + self.w)
#             cv2.line(canvas, (sx, self.y), (ex, self.y), border_col, thickness)
#             cv2.line(canvas, (sx, self.y + self.h), (ex, self.y + self.h), border_col, thickness)
#         # Left & right
#         for sy in range(self.y, self.y + self.h, dash_len * 2):
#             ey = min(sy + dash_len, self.y + self.h)
#             cv2.line(canvas, (self.x, sy), (self.x, ey), border_col, thickness)
#             cv2.line(canvas, (self.x + self.w, sy), (self.x + self.w, ey), border_col, thickness)

#         if self.tile:
#             font = cv2.FONT_HERSHEY_SIMPLEX
#             val = self.tile.value
#             scale = 1.0 if len(val) <= 2 else 0.65
#             (tw, th), _ = cv2.getTextSize(val, font, scale, 2)
#             tx = self.x + (self.w - tw) // 2
#             ty = self.y + (self.h + th) // 2
#             cv2.putText(canvas, val, (tx, ty), font, scale, COL_TEXT, 2, cv2.LINE_AA)
#         else:
#             font = cv2.FONT_HERSHEY_SIMPLEX
#             (tw, th), _ = cv2.getTextSize("?", font, 1.2, 2)
#             tx = self.x + (self.w - tw) // 2
#             ty = self.y + (self.h + th) // 2
#             cv2.putText(canvas, "?", (tx, ty), font, 1.2, (120, 120, 120), 2, cv2.LINE_AA)


# # ─────────────────────────────────────────────────────────────
# # PUZZLE GENERATOR
# # ─────────────────────────────────────────────────────────────
# def generate_puzzle(level: int = 1):
#     """
#     Returns (layout_type, correct_values, tile_pool)
#       Level 1-2:  A  op  B  =  C          (4 values)
#       Level 3+:   A  op  B  =  C  op  D   (6 values)
#     """
#     operators = ["+", "-", "*"]

#     if level <= 2:
#         op = random.choice(["+", "-", "*"])
#         if op == "+":
#             a = random.randint(1, 20)
#             b = random.randint(1, 20)
#             c = a + b
#         elif op == "-":
#             a = random.randint(5, 30)
#             b = random.randint(1, a - 1)
#             c = a - b
#         else:
#             a = random.randint(2, 9)
#             b = random.randint(2, 9)
#             c = a * b

#         correct = [str(a), op, str(b), str(c)]
#         layout_type = "simple"
#     else:
#         for _ in range(200):
#             op1 = random.choice(["+", "-"])
#             op2 = random.choice(["+", "-"])
#             a = random.randint(1, 15)
#             b = random.randint(1, 15)
#             lhs = a + b if op1 == "+" else a - b
#             c = random.randint(1, 15)
#             d = lhs - c if op2 == "+" else c - lhs
#             if 1 <= d <= 20:
#                 rhs = c + d if op2 == "+" else c - d
#                 if lhs == rhs:
#                     break
#         else:
#             # Fallback simple
#             a, op1, b, c, op2, d = 5, "+", 3, 4, "+", 4
#         correct = [str(a), op1, str(b), str(c), op2, str(d)]
#         layout_type = "advanced"

#     # Build pool: correct tiles + distractors
#     pool = list(correct)
#     num_distractors = random.randint(3, 5)
#     for _ in range(num_distractors):
#         if random.random() < 0.3:
#             pool.append(random.choice(operators))
#         else:
#             pool.append(str(random.randint(1, 30)))
#     random.shuffle(pool)

#     return layout_type, correct, pool


# # ─────────────────────────────────────────────────────────────
# # GAME
# # ─────────────────────────────────────────────────────────────
# class MathPuzzleGame:
#     def __init__(self):
#         self.tracker = HandTracker()
#         self.score = 0
#         self.level = 1
#         self.puzzles_solved = 0
#         self.message = ""
#         self.message_time = 0
#         self.message_color = COL_TEXT
#         self.show_celebration = False
#         self.celebration_start = 0

#         self.tiles = []
#         self.chambers = []
#         self.equals_x = 0
#         self.equals_y = 0
#         self.grabbed_tile = None
#         self.grab_offset = (0, 0)
#         self.was_pinching = False

#         self._new_puzzle()

#     # ── Puzzle setup ──────────────────────────────────────────
#     def _new_puzzle(self):
#         self.tiles.clear()
#         self.chambers.clear()
#         self.grabbed_tile = None
#         self.show_celebration = False
#         self.message = ""

#         layout_type, self.correct_values, pool = generate_puzzle(self.level)

#         # Chamber layout
#         if layout_type == "simple":
#             # [A] [op] [B]  =  [C]
#             gap = 20
#             eq_gap = 50
#             total_w = 4 * CHAMBER_SIZE + 3 * gap + eq_gap
#             sx = (WINDOW_W - total_w) // 2
#             cy = WINDOW_H // 2 + 30

#             self.chambers.append(Chamber(sx, cy, "num"))
#             self.chambers.append(Chamber(sx + CHAMBER_SIZE + gap, cy, "op"))
#             self.chambers.append(Chamber(sx + 2 * (CHAMBER_SIZE + gap), cy, "num"))
#             self.equals_x = sx + 3 * (CHAMBER_SIZE + gap) - 5
#             self.equals_y = cy + CHAMBER_SIZE // 2
#             self.chambers.append(Chamber(sx + 3 * (CHAMBER_SIZE + gap) + eq_gap - gap, cy, "num"))
#         else:
#             # [A] [op1] [B]  =  [C] [op2] [D]
#             gap = 15
#             eq_gap = 45
#             total_w = 6 * CHAMBER_SIZE + 5 * gap + eq_gap
#             sx = (WINDOW_W - total_w) // 2
#             cy = WINDOW_H // 2 + 30

#             step = CHAMBER_SIZE + gap
#             self.chambers.append(Chamber(sx, cy, "num"))
#             self.chambers.append(Chamber(sx + step, cy, "op"))
#             self.chambers.append(Chamber(sx + 2 * step, cy, "num"))
#             self.equals_x = sx + 3 * step - 5
#             self.equals_y = cy + CHAMBER_SIZE // 2
#             rx = sx + 3 * step + eq_gap - gap
#             self.chambers.append(Chamber(rx, cy, "num"))
#             self.chambers.append(Chamber(rx + step, cy, "op"))
#             self.chambers.append(Chamber(rx + 2 * step, cy, "num"))

#         # Create tiles — spread across top region
#         cols = min(len(pool), 8)
#         margin_x = 80
#         spacing_x = (WINDOW_W - 2 * margin_x) // max(cols, 1)
#         for i, val in enumerate(pool):
#             col = i % cols
#             row = i // cols
#             x = margin_x + col * spacing_x + random.randint(-8, 8)
#             y = 110 + row * (TILE_SIZE + 25) + random.randint(-5, 5)
#             is_op = val in ["+", "-", "*", "/"]
#             self.tiles.append(Tile(val, x, y, is_operator=is_op))

#     # ── Evaluate equation ────────────────────────────────────
#     def _check_answer(self):
#         for ch in self.chambers:
#             if ch.tile is None:
#                 self._show_message("Fill all chambers first!", COL_WRONG)
#                 return

#         values = [ch.tile.value for ch in self.chambers]

#         try:
#             if len(values) == 4:
#                 lhs = eval(f"{values[0]} {values[1]} {values[2]}")
#                 rhs = float(values[3])
#             elif len(values) == 6:
#                 lhs = eval(f"{values[0]} {values[1]} {values[2]}")
#                 rhs = eval(f"{values[3]} {values[4]} {values[5]}")
#             else:
#                 self._on_wrong()
#                 return

#             if abs(lhs - rhs) < 0.001:
#                 self._on_correct()
#             else:
#                 self._on_wrong()
#         except Exception:
#             self._on_wrong()

#     def _on_correct(self):
#         self.score += 10 * self.level
#         self.puzzles_solved += 1
#         if self.puzzles_solved % 3 == 0 and self.level < 5:
#             self.level += 1
#         self.show_celebration = True
#         self.celebration_start = time.time()

#     def _on_wrong(self):
#         self._show_message("WRONG! Try Again...", COL_WRONG)
#         for ch in self.chambers:
#             if ch.tile:
#                 ch.tile.reset_position()
#                 ch.tile = None

#     def _show_message(self, msg, color):
#         self.message = msg
#         self.message_time = time.time()
#         self.message_color = color

#     # ── Gesture input ────────────────────────────────────────
#     def _handle_hand(self):
#         pos = self.tracker.index_pos
#         pinching = self.tracker.is_pinching

#         if pos is None:
#             if self.grabbed_tile:
#                 self._release_tile()
#             self.was_pinching = False
#             return

#         px, py = pos

#         # Pinch just started
#         if pinching and not self.was_pinching:
#             # Check chambers first (to remove placed tiles)
#             for ch in self.chambers:
#                 if ch.tile and ch.contains(px, py):
#                     tile = ch.tile
#                     tile.placed_in = None
#                     ch.tile = None
#                     tile.grabbed = True
#                     self.grabbed_tile = tile
#                     self.grab_offset = (tile.x - px, tile.y - py)
#                     self.was_pinching = True
#                     return

#             # Check free tiles (topmost first)
#             for tile in reversed(self.tiles):
#                 if tile.contains(px, py) and tile.placed_in is None:
#                     tile.grabbed = True
#                     self.grabbed_tile = tile
#                     self.grab_offset = (tile.x - px, tile.y - py)
#                     break

#         # Dragging
#         if pinching and self.grabbed_tile:
#             ox, oy = self.grab_offset
#             self.grabbed_tile.x = px + ox
#             self.grabbed_tile.y = py + oy

#         # Released
#         if not pinching and self.was_pinching and self.grabbed_tile:
#             self._release_tile()

#         self.was_pinching = pinching

#     def _release_tile(self):
#         tile = self.grabbed_tile
#         if tile is None:
#             return
#         tile.grabbed = False

#         placed = False
#         for ch in self.chambers:
#             if ch.contains(tile.cx, tile.cy) and ch.tile is None:
#                 ch.tile = tile
#                 tile.placed_in = ch
#                 tile.x = ch.x + (ch.w - tile.w) // 2
#                 tile.y = ch.y + (ch.h - tile.h) // 2
#                 placed = True
#                 break

#         if not placed:
#             tile.reset_position()

#         self.grabbed_tile = None

#     # ── Drawing ───────────────────────────────────────────────
#     def _draw_header(self, canvas):
#         font = cv2.FONT_HERSHEY_SIMPLEX

#         # Title bar background
#         cv2.rectangle(canvas, (0, 0), (WINDOW_W, 90), (40, 40, 40), -1)
#         cv2.line(canvas, (0, 90), (WINDOW_W, 90), COL_SCORE, 2)

#         # Title
#         cv2.putText(canvas, "MATH PUZZLE", (20, 45),
#                     font, 1.3, COL_SCORE, 3, cv2.LINE_AA)
#         cv2.putText(canvas, "Pinch to grab tiles, drop into chambers",
#                     (20, 75), font, 0.55, (140, 140, 140), 1, cv2.LINE_AA)

#         # Score & Level (right side)
#         score_text = f"SCORE: {self.score}"
#         (sw, _), _ = cv2.getTextSize(score_text, font, 0.9, 2)
#         cv2.putText(canvas, score_text, (WINDOW_W - sw - 20, 40),
#                     font, 0.9, COL_SCORE, 2, cv2.LINE_AA)

#         level_text = f"LEVEL {self.level}"
#         (lw, _), _ = cv2.getTextSize(level_text, font, 0.65, 2)
#         cv2.putText(canvas, level_text, (WINDOW_W - lw - 20, 72),
#                     font, 0.65, (180, 180, 180), 2, cv2.LINE_AA)

#         # Puzzles solved
#         solved_text = f"Solved: {self.puzzles_solved}"
#         (pw, _), _ = cv2.getTextSize(solved_text, font, 0.55, 1)
#         cv2.putText(canvas, solved_text, (WINDOW_W - pw - sw - 60, 40),
#                     font, 0.55, (120, 120, 120), 1, cv2.LINE_AA)

#     def _draw_equation_label(self, canvas):
#         """Draw 'LHS = RHS' label above chambers."""
#         font = cv2.FONT_HERSHEY_SIMPLEX
#         if len(self.chambers) == 4:
#             label = "Place:  [ num ]  [ op ]  [ num ]  =  [ result ]"
#         else:
#             label = "Place:  [ num ]  [ op ]  [ num ]  =  [ num ]  [ op ]  [ num ]"

#         (tw, th), _ = cv2.getTextSize(label, font, 0.5, 1)
#         x = (WINDOW_W - tw) // 2
#         y = self.chambers[0].y - 20
#         cv2.putText(canvas, label, (x, y), font, 0.5, (130, 130, 130), 1, cv2.LINE_AA)

#     def _draw_controls(self, canvas):
#         font = cv2.FONT_HERSHEY_SIMPLEX
#         bar_y = WINDOW_H - 40
#         cv2.rectangle(canvas, (0, bar_y), (WINDOW_W, WINDOW_H), (40, 40, 40), -1)

#         controls = [
#             ("[C] Check", COL_CORRECT),
#             ("[R] Reset", COL_SCORE),
#             ("[N] Next", (200, 200, 200)),
#             ("[Q] Quit", (150, 150, 150)),
#         ]
#         x = 30
#         for text, col in controls:
#             cv2.putText(canvas, text, (x, WINDOW_H - 12), font, 0.55, col, 1, cv2.LINE_AA)
#             (tw, _), _ = cv2.getTextSize(text, font, 0.55, 1)
#             x += tw + 40

#     def _draw_ui(self, canvas):
#         self._draw_header(canvas)
#         self._draw_equation_label(canvas)

#         # Chambers
#         for ch in self.chambers:
#             ch.draw(canvas)

#         # Equals sign
#         font = cv2.FONT_HERSHEY_SIMPLEX
#         cv2.putText(canvas, "=", (self.equals_x, self.equals_y + 12),
#                     font, 2.0, COL_EQUALS, 3, cv2.LINE_AA)

#         # Tiles (non-grabbed, non-placed first)
#         for tile in self.tiles:
#             if not tile.grabbed and tile.placed_in is None:
#                 tile.draw(canvas)

#         # Grabbed tile on top
#         if self.grabbed_tile:
#             self.grabbed_tile.draw(canvas)

#         # Cursor
#         if self.tracker.index_pos:
#             px, py = self.tracker.index_pos
#             if self.tracker.is_pinching:
#                 cv2.circle(canvas, (px, py), 14, COL_TILE_GRAB, -1)
#                 cv2.circle(canvas, (px, py), 16, COL_TEXT, 2)
#                 # Pinch indicator lines
#                 for angle in range(0, 360, 45):
#                     ex = int(px + 22 * math.cos(math.radians(angle)))
#                     ey = int(py + 22 * math.sin(math.radians(angle)))
#                     cv2.line(canvas, (px, py), (ex, ey), (100, 100, 255), 1)
#             else:
#                 cv2.circle(canvas, (px, py), 9, COL_CURSOR, -1)
#                 cv2.circle(canvas, (px, py), 11, COL_TEXT, 1)

#         # Message toast
#         if self.message and time.time() - self.message_time < 2.5:
#             (tw, th), _ = cv2.getTextSize(self.message, font, 1.1, 2)
#             mx = (WINDOW_W - tw) // 2
#             my = WINDOW_H - 100
#             pad = 15
#             cv2.rectangle(canvas, (mx - pad, my - th - pad),
#                           (mx + tw + pad, my + pad), self.message_color, -1)
#             cv2.rectangle(canvas, (mx - pad, my - th - pad),
#                           (mx + tw + pad, my + pad), COL_TEXT, 2)
#             cv2.putText(canvas, self.message, (mx, my), font, 1.1, COL_TEXT, 2, cv2.LINE_AA)

#         self._draw_controls(canvas)

#         # Celebration overlay
#         if self.show_celebration:
#             elapsed = time.time() - self.celebration_start
#             if elapsed < 3.5:
#                 self._draw_celebration(canvas, elapsed)
#             else:
#                 self.show_celebration = False
#                 self._new_puzzle()

#     def _draw_celebration(self, canvas, elapsed):
#         font = cv2.FONT_HERSHEY_SIMPLEX

#         # Dark overlay
#         overlay = canvas.copy()
#         cv2.rectangle(overlay, (0, 0), (WINDOW_W, WINDOW_H), (0, 0, 0), -1)
#         alpha = min(0.65, elapsed * 2)
#         cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

#         # ─── Stars / sparkles ─────────────────────────────────
#         num_sparkles = min(int(elapsed * 20), 50)
#         random.seed(42)  # consistent sparkle positions per frame cycle
#         for i in range(num_sparkles):
#             sx = random.randint(50, WINDOW_W - 50)
#             sy = random.randint(50, WINDOW_H - 50)
#             brightness = int(128 + 127 * math.sin(elapsed * 5 + i))
#             size = random.randint(2, 6)
#             col = (brightness, brightness, min(255, brightness + 80))
#             # Star shape
#             cv2.circle(canvas, (sx, sy), size, col, -1)
#             cv2.line(canvas, (sx - size * 2, sy), (sx + size * 2, sy), col, 1)
#             cv2.line(canvas, (sx, sy - size * 2), (sx, sy + size * 2), col, 1)
#         random.seed()  # restore random

#         # ─── CONGRATULATIONS text ────────────────────────────
#         pulse = 1.0 + 0.12 * math.sin(elapsed * 8)
#         scale = 2.0 * pulse
#         congrats = "CONGRATULATIONS!"
#         (tw, th), _ = cv2.getTextSize(congrats, font, scale, 4)
#         cx = (WINDOW_W - tw) // 2
#         cy_text = WINDOW_H // 2 - 80

#         # Glow layers
#         cv2.putText(canvas, congrats, (cx, cy_text), font, scale, (0, 80, 0), 8, cv2.LINE_AA)
#         cv2.putText(canvas, congrats, (cx, cy_text), font, scale, (0, 200, 0), 4, cv2.LINE_AA)
#         cv2.putText(canvas, congrats, (cx, cy_text), font, scale, COL_CORRECT, 3, cv2.LINE_AA)

#         # ─── Clapping line ────────────────────────────────────
#         clap = ">> CLAP! CLAP! CLAP! <<"
#         (tw2, _), _ = cv2.getTextSize(clap, font, 0.9, 2)
#         cx2 = (WINDOW_W - tw2) // 2
#         bounce = int(8 * math.sin(elapsed * 10))
#         cv2.putText(canvas, clap, (cx2, cy_text + 60 + bounce),
#                     font, 0.9, COL_SCORE, 2, cv2.LINE_AA)

#         # ─── Score popup ─────────────────────────────────────
#         pts = 10 * self.level
#         score_msg = f"+{pts} POINTS!"
#         (tw3, _), _ = cv2.getTextSize(score_msg, font, 1.2, 3)
#         cx3 = (WINDOW_W - tw3) // 2
#         cv2.putText(canvas, score_msg, (cx3, cy_text + 120),
#                     font, 1.2, (0, 255, 255), 3, cv2.LINE_AA)

#         # ─── Total score ─────────────────────────────────────
#         total_msg = f"Total Score: {self.score}"
#         (tw4, _), _ = cv2.getTextSize(total_msg, font, 0.8, 2)
#         cx4 = (WINDOW_W - tw4) // 2
#         cv2.putText(canvas, total_msg, (cx4, cy_text + 165),
#                     font, 0.8, (200, 200, 200), 2, cv2.LINE_AA)

#         # ─── Firework rings ──────────────────────────────────
#         centers = [(300, 250), (980, 250), (640, 200), (200, 400), (1080, 400)]
#         for ci, (fcx, fcy) in enumerate(centers):
#             radius = int((elapsed * 80 + ci * 30) % 120)
#             fade = max(0, 255 - radius * 3)
#             if fade > 20:
#                 color = (
#                     (fade + ci * 40) % 256,
#                     (fade + ci * 80) % 256,
#                     fade,
#                 )
#                 cv2.circle(canvas, (fcx, fcy), radius, color, 2)

#     # ── Main loop ─────────────────────────────────────────────
#     def run(self):
#         cap = cv2.VideoCapture(0)
#         if not cap.isOpened():
#             print("\n❌  ERROR: Cannot open webcam!")
#             print("   Make sure a camera is connected and not in use by another app.")
#             print("   Try changing cv2.VideoCapture(0) to (1) if you have multiple cameras.")
#             return

#         cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_W)
#         cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_H)

#         print("\n✅  Game started! Show your hand to the camera.")
#         print("   PINCH (thumb + index finger) to grab tiles.")
#         print("   Press [C] to check, [R] to reset, [N] for next, [Q] to quit.\n")

#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 print("❌  Failed to read from camera.")
#                 break

#             # Mirror so movements feel natural
#             frame = cv2.flip(frame, 1)
#             frame = cv2.resize(frame, (WINDOW_W, WINDOW_H))

#             # Hand tracking
#             frame = self.tracker.process(frame)

#             # Darken camera feed so UI stands out
#             canvas = (frame * 0.2).astype(np.uint8)

#             # Gesture handling
#             if not self.show_celebration:
#                 self._handle_hand()

#             # Render
#             self._draw_ui(canvas)

#             cv2.imshow("Math Puzzle Game", canvas)

#             key = cv2.waitKey(1000 // FPS) & 0xFF
#             if key == ord("q"):
#                 break
#             elif key == ord("c"):
#                 if not self.show_celebration:
#                     self._check_answer()
#             elif key == ord("r"):
#                 for tile in self.tiles:
#                     tile.reset_position()
#                 for ch in self.chambers:
#                     ch.tile = None
#                 self._show_message("Puzzle reset!", COL_SCORE)
#             elif key == ord("n"):
#                 self._new_puzzle()
#                 self._show_message("New puzzle!", COL_SCORE)

#         cap.release()
#         cv2.destroyAllWindows()
#         print(f"\n{'='*50}")
#         print(f"  GAME OVER")
#         print(f"  Final Score : {self.score}")
#         print(f"  Puzzles Solved : {self.puzzles_solved}")
#         print(f"  Final Level : {self.level}")
#         print(f"{'='*50}")


# # ─────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     print("=" * 60)
#     print("   MATH PUZZLE - Hand Gesture Game")
#     print(f"   MediaPipe version: {mp.__version__}")
#     print(f"   API mode: {'New Tasks API' if USE_NEW_API else 'Legacy Solutions API'}")
#     print("=" * 60)
#     game = MathPuzzleGame()
#     game.run()



"""
╔══════════════════════════════════════════════════════════════╗
║          MATH PUZZLE - Hand Gesture Game                     ║
║   Use your hand to drag numbers & operators into chambers    ║
║   to balance the equation!                                   ║
╚══════════════════════════════════════════════════════════════╝

Controls:
  - Move index finger to hover over tiles
  - PINCH (thumb + index finger close) to grab a tile
  - Drag to a chamber and release to place it
  - Press 'c' to check your answer
  - Press 'r' to reset the current puzzle
  - Press 'n' to skip to next puzzle
  - Press 'q' to quit

Requirements:
  pip install opencv-python mediapipe numpy
"""

import cv2
import numpy as np
import random
import time
import math
import os
import sys
import urllib.request

# ─────────────────────────────────────────────────────────────
# MEDIAPIPE COMPATIBILITY LAYER
# Supports both old (mp.solutions) and new (mp.tasks) APIs
# ─────────────────────────────────────────────────────────────
import mediapipe as mp

USE_NEW_API = not hasattr(mp, "solutions") or not hasattr(getattr(mp, "solutions", None) or object(), "hands")

MODEL_FILENAME = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)


def _download_model(dest_path: str):
    """Download the HandLandmarker model file if missing."""
    if os.path.exists(dest_path):
        return dest_path
    print(f"[INFO] Downloading hand landmark model → {dest_path}")
    print(f"       (one-time download, ~10 MB)")
    try:
        urllib.request.urlretrieve(MODEL_URL, dest_path)
        print("       ✅ Download complete.")
    except Exception as e:
        print(f"       ❌ Download failed: {e}")
        print("       Manually download from:")
        print(f"         {MODEL_URL}")
        print(f"       and place it as: {dest_path}")
        sys.exit(1)
    return dest_path


# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
WINDOW_W, WINDOW_H = 1280, 720
TILE_SIZE = 70
CHAMBER_SIZE = 75
FPS = 30

# Color palette (BGR)
COL_BG           = (30, 30, 30)
COL_TILE_NUM     = (200, 140, 50)      # blue-ish for numbers
COL_TILE_OP      = (50, 140, 200)      # orange-ish for operators
COL_TILE_HOVER   = (100, 220, 100)     # green highlight
COL_TILE_GRAB    = (80, 80, 255)       # red when grabbed
COL_CHAMBER      = (80, 80, 80)        # empty chamber
COL_CHAMBER_FILL = (60, 120, 60)       # filled chamber
COL_TEXT         = (255, 255, 255)
COL_EQUALS       = (180, 180, 180)
COL_CORRECT      = (80, 220, 80)
COL_WRONG        = (60, 60, 230)
COL_SCORE        = (0, 215, 255)
COL_CURSOR       = (0, 255, 255)


# ─────────────────────────────────────────────────────────────
# HAND TRACKER — works with both old and new MediaPipe
# ─────────────────────────────────────────────────────────────
class HandTracker:
    # ── Pinch tuning ─────────────────────────────────────────
    PINCH_CLOSE_DIST   = 60      # px — threshold to START a pinch (generous)
    PINCH_OPEN_DIST    = 80      # px — threshold to END a pinch (hysteresis)
    SMOOTH_FRAMES      = 3       # how many consecutive pinch frames before we commit
    CURSOR_SMOOTH      = 0.45    # 0 = no smoothing, 1 = frozen  (lower = snappier)

    def __init__(self):
        self.index_pos = None       # smoothed cursor position
        self.is_pinching = False    # final, smoothed pinch state
        self._frame_count = 0

        # ── smoothing internals ──
        self._raw_pos = None
        self._raw_pinch = False
        self._pinch_counter = 0                # consecutive frames in pinch
        self._release_counter = 0              # consecutive frames NOT in pinch
        self._prev_smooth_pos = None           # for cursor EMA

        if USE_NEW_API:
            self._init_new_api()
        else:
            self._init_old_api()

    # ── New API (mediapipe >= 0.10.9) ────────────────────────
    def _init_new_api(self):
        print("[INFO] Using new MediaPipe Tasks API (v0.10.9+)")
        model_path = _download_model(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), MODEL_FILENAME)
        )

        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        RunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS

    # ── Old API (mediapipe < 0.10.9) ─────────────────────────
    def _init_old_api(self):
        print("[INFO] Using legacy MediaPipe Solutions API")
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        self._mp_draw = mp.solutions.drawing_utils
        self._hand_conns = mp.solutions.hands.HAND_CONNECTIONS

    def process(self, frame):
        """Process a BGR frame, update index_pos and is_pinching, draw skeleton."""
        self._frame_count += 1
        self._raw_pos = None
        self._raw_pinch = False
        h, w, _ = frame.shape

        if USE_NEW_API:
            self._process_new(frame, w, h)
        else:
            self._process_old(frame, w, h)

        # ── Smooth the cursor position (EMA filter) ──────────
        if self._raw_pos is not None:
            if self._prev_smooth_pos is None:
                self._prev_smooth_pos = self._raw_pos
            a = self.CURSOR_SMOOTH
            sx = int(a * self._prev_smooth_pos[0] + (1 - a) * self._raw_pos[0])
            sy = int(a * self._prev_smooth_pos[1] + (1 - a) * self._raw_pos[1])
            self._prev_smooth_pos = (sx, sy)
            self.index_pos = (sx, sy)
        else:
            self.index_pos = None
            self._prev_smooth_pos = None

        # ── Smooth the pinch state (hysteresis + counter) ────
        if self._raw_pinch:
            self._pinch_counter += 1
            self._release_counter = 0
        else:
            self._release_counter += 1
            self._pinch_counter = 0

        if not self.is_pinching:
            # Need SMOOTH_FRAMES consecutive pinch frames to START
            if self._pinch_counter >= self.SMOOTH_FRAMES:
                self.is_pinching = True
        else:
            # Need SMOOTH_FRAMES consecutive open frames to STOP
            if self._release_counter >= self.SMOOTH_FRAMES:
                self.is_pinching = False

        return frame

    def _process_new(self, frame, w, h):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(self._frame_count * (1000 / FPS))

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            landmarks = result.hand_landmarks[0]

            # Index finger tip (landmark 8) & Thumb tip (landmark 4)
            ix = int(landmarks[8].x * w)
            iy = int(landmarks[8].y * h)
            tx = int(landmarks[4].x * w)
            ty = int(landmarks[4].y * h)

            # Cursor = midpoint between thumb and index (more stable)
            self._raw_pos = ((ix + tx) // 2, (iy + ty) // 2)

            # Pinch with hysteresis
            dist = math.hypot(ix - tx, iy - ty)
            if self._raw_pinch or self.is_pinching:
                self._raw_pinch = dist < self.PINCH_OPEN_DIST
            else:
                self._raw_pinch = dist < self.PINCH_CLOSE_DIST

            self._draw_skeleton_new(frame, landmarks, w, h)

    def _draw_skeleton_new(self, frame, landmarks, w, h):
        """Draw hand skeleton using new API landmarks."""
        pts = []
        for lm in landmarks:
            px, py = int(lm.x * w), int(lm.y * h)
            pts.append((px, py))
            cv2.circle(frame, (px, py), 3, (60, 60, 60), -1)

        # Draw connections
        for conn in self._connections:
            start_idx = conn.start
            end_idx = conn.end
            if start_idx < len(pts) and end_idx < len(pts):
                cv2.line(frame, pts[start_idx], pts[end_idx], (90, 90, 90), 1)

    def _process_old(self, frame, w, h):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            ix = int(hand.landmark[8].x * w)
            iy = int(hand.landmark[8].y * h)
            tx = int(hand.landmark[4].x * w)
            ty = int(hand.landmark[4].y * h)

            # Cursor = midpoint between thumb and index
            self._raw_pos = ((ix + tx) // 2, (iy + ty) // 2)

            # Pinch with hysteresis
            dist = math.hypot(ix - tx, iy - ty)
            if self._raw_pinch or self.is_pinching:
                self._raw_pinch = dist < self.PINCH_OPEN_DIST
            else:
                self._raw_pinch = dist < self.PINCH_CLOSE_DIST

            self._mp_draw.draw_landmarks(
                frame, hand, self._hand_conns,
                self._mp_draw.DrawingSpec(color=(50, 50, 50), thickness=1, circle_radius=2),
                self._mp_draw.DrawingSpec(color=(100, 100, 100), thickness=1),
            )


# ─────────────────────────────────────────────────────────────
# TILE (draggable number / operator)
# ─────────────────────────────────────────────────────────────
class Tile:
    def __init__(self, value: str, x: int, y: int, is_operator: bool = False):
        self.value = value
        self.home_x, self.home_y = x, y
        self.x, self.y = x, y
        self.w, self.h = TILE_SIZE, TILE_SIZE
        self.is_operator = is_operator
        self.grabbed = False
        self.hovered = False          # True when cursor is nearby
        self.placed_in = None

    @property
    def cx(self):
        return self.x + self.w // 2

    @property
    def cy(self):
        return self.y + self.h // 2

    def contains(self, px, py, padding=20):
        """Check if point is inside tile, with extra padding for easier grabbing."""
        return (self.x - padding <= px <= self.x + self.w + padding and
                self.y - padding <= py <= self.y + self.h + padding)

    def reset_position(self):
        self.x, self.y = self.home_x, self.home_y
        if self.placed_in:
            self.placed_in.tile = None
            self.placed_in = None

    def draw(self, canvas):
        color = COL_TILE_OP if self.is_operator else COL_TILE_NUM
        if self.grabbed:
            color = COL_TILE_GRAB
        elif self.hovered:
            color = COL_TILE_HOVER

        # Hover glow ring (drawn BEFORE tile so it's behind)
        if self.hovered and not self.grabbed:
            glow_pad = 6
            cv2.rectangle(canvas,
                          (self.x - glow_pad, self.y - glow_pad),
                          (self.x + self.w + glow_pad, self.y + self.h + glow_pad),
                          COL_TILE_HOVER, 3)

        # Shadow
        cv2.rectangle(canvas, (self.x + 3, self.y + 3),
                      (self.x + self.w + 3, self.y + self.h + 3), (20, 20, 20), -1)
        # Tile background
        cv2.rectangle(canvas, (self.x, self.y),
                      (self.x + self.w, self.y + self.h), color, -1)
        # Border
        border_col = COL_TEXT if not self.grabbed else (150, 150, 255)
        cv2.rectangle(canvas, (self.x, self.y),
                      (self.x + self.w, self.y + self.h), border_col, 2)

        # Value text
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 1.0 if len(self.value) <= 2 else 0.65
        (tw, th), _ = cv2.getTextSize(self.value, font, scale, 2)
        tx = self.x + (self.w - tw) // 2
        ty = self.y + (self.h + th) // 2
        cv2.putText(canvas, self.value, (tx, ty), font, scale, COL_TEXT, 2, cv2.LINE_AA)


# ─────────────────────────────────────────────────────────────
# CHAMBER (drop zone)
# ─────────────────────────────────────────────────────────────
class Chamber:
    def __init__(self, x: int, y: int, label: str = "?"):
        self.x, self.y = x, y
        self.w, self.h = CHAMBER_SIZE, CHAMBER_SIZE
        self.tile = None
        self.label = label

    @property
    def cx(self):
        return self.x + self.w // 2

    @property
    def cy(self):
        return self.y + self.h // 2

    def contains(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def draw(self, canvas):
        col = COL_CHAMBER_FILL if self.tile else COL_CHAMBER

        # Chamber background
        cv2.rectangle(canvas, (self.x, self.y),
                      (self.x + self.w, self.y + self.h), col, -1)

        # Dashed border effect
        border_col = COL_CORRECT if self.tile else (140, 140, 140)
        thickness = 2
        dash_len = 10
        # Top & bottom
        for sx in range(self.x, self.x + self.w, dash_len * 2):
            ex = min(sx + dash_len, self.x + self.w)
            cv2.line(canvas, (sx, self.y), (ex, self.y), border_col, thickness)
            cv2.line(canvas, (sx, self.y + self.h), (ex, self.y + self.h), border_col, thickness)
        # Left & right
        for sy in range(self.y, self.y + self.h, dash_len * 2):
            ey = min(sy + dash_len, self.y + self.h)
            cv2.line(canvas, (self.x, sy), (self.x, ey), border_col, thickness)
            cv2.line(canvas, (self.x + self.w, sy), (self.x + self.w, ey), border_col, thickness)

        if self.tile:
            font = cv2.FONT_HERSHEY_SIMPLEX
            val = self.tile.value
            scale = 1.0 if len(val) <= 2 else 0.65
            (tw, th), _ = cv2.getTextSize(val, font, scale, 2)
            tx = self.x + (self.w - tw) // 2
            ty = self.y + (self.h + th) // 2
            cv2.putText(canvas, val, (tx, ty), font, scale, COL_TEXT, 2, cv2.LINE_AA)
        else:
            font = cv2.FONT_HERSHEY_SIMPLEX
            (tw, th), _ = cv2.getTextSize("?", font, 1.2, 2)
            tx = self.x + (self.w - tw) // 2
            ty = self.y + (self.h + th) // 2
            cv2.putText(canvas, "?", (tx, ty), font, 1.2, (120, 120, 120), 2, cv2.LINE_AA)


# ─────────────────────────────────────────────────────────────
# PUZZLE GENERATOR
# ─────────────────────────────────────────────────────────────
def generate_puzzle(level: int = 1):
    """
    Returns (layout_type, correct_values, tile_pool)
      Level 1-2:  A  op  B  =  C          (4 values)
      Level 3+:   A  op  B  =  C  op  D   (6 values)
    """
    operators = ["+", "-", "*"]

    if level <= 2:
        op = random.choice(["+", "-", "*"])
        if op == "+":
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            c = a + b
        elif op == "-":
            a = random.randint(5, 30)
            b = random.randint(1, a - 1)
            c = a - b
        else:
            a = random.randint(2, 9)
            b = random.randint(2, 9)
            c = a * b

        correct = [str(a), op, str(b), str(c)]
        layout_type = "simple"
    else:
        for _ in range(200):
            op1 = random.choice(["+", "-"])
            op2 = random.choice(["+", "-"])
            a = random.randint(1, 15)
            b = random.randint(1, 15)
            lhs = a + b if op1 == "+" else a - b
            c = random.randint(1, 15)
            d = lhs - c if op2 == "+" else c - lhs
            if 1 <= d <= 20:
                rhs = c + d if op2 == "+" else c - d
                if lhs == rhs:
                    break
        else:
            # Fallback simple
            a, op1, b, c, op2, d = 5, "+", 3, 4, "+", 4
        correct = [str(a), op1, str(b), str(c), op2, str(d)]
        layout_type = "advanced"

    # Build pool: correct tiles + distractors
    pool = list(correct)
    num_distractors = random.randint(3, 5)
    for _ in range(num_distractors):
        if random.random() < 0.3:
            pool.append(random.choice(operators))
        else:
            pool.append(str(random.randint(1, 30)))
    random.shuffle(pool)

    return layout_type, correct, pool


# ─────────────────────────────────────────────────────────────
# GAME
# ─────────────────────────────────────────────────────────────
class MathPuzzleGame:
    def __init__(self):
        self.tracker = HandTracker()
        self.score = 0
        self.level = 1
        self.puzzles_solved = 0
        self.message = ""
        self.message_time = 0
        self.message_color = COL_TEXT
        self.show_celebration = False
        self.celebration_start = 0

        self.tiles = []
        self.chambers = []
        self.equals_x = 0
        self.equals_y = 0
        self.grabbed_tile = None
        self.grab_offset = (0, 0)
        self.was_pinching = False

        self._new_puzzle()

    # ── Puzzle setup ──────────────────────────────────────────
    def _new_puzzle(self):
        self.tiles.clear()
        self.chambers.clear()
        self.grabbed_tile = None
        self.show_celebration = False
        self.message = ""

        layout_type, self.correct_values, pool = generate_puzzle(self.level)

        # Chamber layout
        if layout_type == "simple":
            # [A] [op] [B]  =  [C]
            gap = 20
            eq_gap = 50
            total_w = 4 * CHAMBER_SIZE + 3 * gap + eq_gap
            sx = (WINDOW_W - total_w) // 2
            cy = WINDOW_H // 2 + 30

            self.chambers.append(Chamber(sx, cy, "num"))
            self.chambers.append(Chamber(sx + CHAMBER_SIZE + gap, cy, "op"))
            self.chambers.append(Chamber(sx + 2 * (CHAMBER_SIZE + gap), cy, "num"))
            self.equals_x = sx + 3 * (CHAMBER_SIZE + gap) - 5
            self.equals_y = cy + CHAMBER_SIZE // 2
            self.chambers.append(Chamber(sx + 3 * (CHAMBER_SIZE + gap) + eq_gap - gap, cy, "num"))
        else:
            # [A] [op1] [B]  =  [C] [op2] [D]
            gap = 15
            eq_gap = 45
            total_w = 6 * CHAMBER_SIZE + 5 * gap + eq_gap
            sx = (WINDOW_W - total_w) // 2
            cy = WINDOW_H // 2 + 30

            step = CHAMBER_SIZE + gap
            self.chambers.append(Chamber(sx, cy, "num"))
            self.chambers.append(Chamber(sx + step, cy, "op"))
            self.chambers.append(Chamber(sx + 2 * step, cy, "num"))
            self.equals_x = sx + 3 * step - 5
            self.equals_y = cy + CHAMBER_SIZE // 2
            rx = sx + 3 * step + eq_gap - gap
            self.chambers.append(Chamber(rx, cy, "num"))
            self.chambers.append(Chamber(rx + step, cy, "op"))
            self.chambers.append(Chamber(rx + 2 * step, cy, "num"))

        # Create tiles — spread across top region
        cols = min(len(pool), 8)
        margin_x = 80
        spacing_x = (WINDOW_W - 2 * margin_x) // max(cols, 1)
        for i, val in enumerate(pool):
            col = i % cols
            row = i // cols
            x = margin_x + col * spacing_x + random.randint(-8, 8)
            y = 110 + row * (TILE_SIZE + 25) + random.randint(-5, 5)
            is_op = val in ["+", "-", "*", "/"]
            self.tiles.append(Tile(val, x, y, is_operator=is_op))

    # ── Evaluate equation ────────────────────────────────────
    def _check_answer(self):
        for ch in self.chambers:
            if ch.tile is None:
                self._show_message("Fill all chambers first!", COL_WRONG)
                return

        values = [ch.tile.value for ch in self.chambers]

        try:
            if len(values) == 4:
                lhs = eval(f"{values[0]} {values[1]} {values[2]}")
                rhs = float(values[3])
            elif len(values) == 6:
                lhs = eval(f"{values[0]} {values[1]} {values[2]}")
                rhs = eval(f"{values[3]} {values[4]} {values[5]}")
            else:
                self._on_wrong()
                return

            if abs(lhs - rhs) < 0.001:
                self._on_correct()
            else:
                self._on_wrong()
        except Exception:
            self._on_wrong()

    def _on_correct(self):
        self.score += 10 * self.level
        self.puzzles_solved += 1
        if self.puzzles_solved % 3 == 0 and self.level < 5:
            self.level += 1
        self.show_celebration = True
        self.celebration_start = time.time()

    def _on_wrong(self):
        self._show_message("WRONG! Try Again...", COL_WRONG)
        for ch in self.chambers:
            if ch.tile:
                ch.tile.reset_position()
                ch.tile = None

    def _show_message(self, msg, color):
        self.message = msg
        self.message_time = time.time()
        self.message_color = color

    # ── Gesture input ────────────────────────────────────────
    def _handle_hand(self):
        pos = self.tracker.index_pos
        pinching = self.tracker.is_pinching

        # ── Clear all hover states first ─────────────────────
        for tile in self.tiles:
            tile.hovered = False

        if pos is None:
            if self.grabbed_tile:
                self._release_tile()
            self.was_pinching = False
            return

        px, py = pos

        # ── Update hover state (visual feedback) ─────────────
        if not self.grabbed_tile:
            for tile in reversed(self.tiles):
                if tile.placed_in is None and tile.contains(px, py):
                    tile.hovered = True
                    break  # only hover the topmost tile

        # ── Pinch just started → try to grab ─────────────────
        if pinching and not self.was_pinching:
            # Check chambers first (to remove placed tiles)
            for ch in self.chambers:
                if ch.tile and ch.contains(px, py):
                    tile = ch.tile
                    tile.placed_in = None
                    ch.tile = None
                    tile.grabbed = True
                    self.grabbed_tile = tile
                    self.grab_offset = (tile.x - px, tile.y - py)
                    self.was_pinching = True
                    return

            # Check free tiles (topmost first, generous padding)
            for tile in reversed(self.tiles):
                if tile.contains(px, py, padding=25) and tile.placed_in is None:
                    tile.grabbed = True
                    tile.hovered = False
                    self.grabbed_tile = tile
                    self.grab_offset = (tile.x - px, tile.y - py)
                    break

        # ── Already pinching + already holding → keep trying to grab
        #    (catches cases where pinch was detected but no tile was
        #     under cursor at the exact transition frame)
        if pinching and self.grabbed_tile is None and self.was_pinching:
            for tile in reversed(self.tiles):
                if tile.contains(px, py, padding=25) and tile.placed_in is None:
                    tile.grabbed = True
                    tile.hovered = False
                    self.grabbed_tile = tile
                    self.grab_offset = (tile.x - px, tile.y - py)
                    break

        # ── Dragging ─────────────────────────────────────────
        if pinching and self.grabbed_tile:
            ox, oy = self.grab_offset
            self.grabbed_tile.x = px + ox
            self.grabbed_tile.y = py + oy

        # ── Released ─────────────────────────────────────────
        if not pinching and self.was_pinching and self.grabbed_tile:
            self._release_tile()

        self.was_pinching = pinching

    def _release_tile(self):
        tile = self.grabbed_tile
        if tile is None:
            return
        tile.grabbed = False

        placed = False
        for ch in self.chambers:
            if ch.contains(tile.cx, tile.cy) and ch.tile is None:
                ch.tile = tile
                tile.placed_in = ch
                tile.x = ch.x + (ch.w - tile.w) // 2
                tile.y = ch.y + (ch.h - tile.h) // 2
                placed = True
                break

        if not placed:
            tile.reset_position()

        self.grabbed_tile = None

    # ── Drawing ───────────────────────────────────────────────
    def _draw_header(self, canvas):
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Title bar background
        cv2.rectangle(canvas, (0, 0), (WINDOW_W, 90), (40, 40, 40), -1)
        cv2.line(canvas, (0, 90), (WINDOW_W, 90), COL_SCORE, 2)

        # Title
        cv2.putText(canvas, "MATH PUZZLE", (20, 45),
                    font, 1.3, COL_SCORE, 3, cv2.LINE_AA)
        cv2.putText(canvas, "Pinch to grab tiles, drop into chambers",
                    (20, 75), font, 0.55, (140, 140, 140), 1, cv2.LINE_AA)

        # Score & Level (right side)
        score_text = f"SCORE: {self.score}"
        (sw, _), _ = cv2.getTextSize(score_text, font, 0.9, 2)
        cv2.putText(canvas, score_text, (WINDOW_W - sw - 20, 40),
                    font, 0.9, COL_SCORE, 2, cv2.LINE_AA)

        level_text = f"LEVEL {self.level}"
        (lw, _), _ = cv2.getTextSize(level_text, font, 0.65, 2)
        cv2.putText(canvas, level_text, (WINDOW_W - lw - 20, 72),
                    font, 0.65, (180, 180, 180), 2, cv2.LINE_AA)

        # Puzzles solved
        solved_text = f"Solved: {self.puzzles_solved}"
        (pw, _), _ = cv2.getTextSize(solved_text, font, 0.55, 1)
        cv2.putText(canvas, solved_text, (WINDOW_W - pw - sw - 60, 40),
                    font, 0.55, (120, 120, 120), 1, cv2.LINE_AA)

    def _draw_equation_label(self, canvas):
        """Draw 'LHS = RHS' label above chambers."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        if len(self.chambers) == 4:
            label = "Place:  [ num ]  [ op ]  [ num ]  =  [ result ]"
        else:
            label = "Place:  [ num ]  [ op ]  [ num ]  =  [ num ]  [ op ]  [ num ]"

        (tw, th), _ = cv2.getTextSize(label, font, 0.5, 1)
        x = (WINDOW_W - tw) // 2
        y = self.chambers[0].y - 20
        cv2.putText(canvas, label, (x, y), font, 0.5, (130, 130, 130), 1, cv2.LINE_AA)

    def _draw_controls(self, canvas):
        font = cv2.FONT_HERSHEY_SIMPLEX
        bar_y = WINDOW_H - 40
        cv2.rectangle(canvas, (0, bar_y), (WINDOW_W, WINDOW_H), (40, 40, 40), -1)

        controls = [
            ("[C] Check", COL_CORRECT),
            ("[R] Reset", COL_SCORE),
            ("[N] Next", (200, 200, 200)),
            ("[Q] Quit", (150, 150, 150)),
        ]
        x = 30
        for text, col in controls:
            cv2.putText(canvas, text, (x, WINDOW_H - 12), font, 0.55, col, 1, cv2.LINE_AA)
            (tw, _), _ = cv2.getTextSize(text, font, 0.55, 1)
            x += tw + 40

    def _draw_ui(self, canvas):
        self._draw_header(canvas)
        self._draw_equation_label(canvas)

        # Chambers
        for ch in self.chambers:
            ch.draw(canvas)

        # Equals sign
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas, "=", (self.equals_x, self.equals_y + 12),
                    font, 2.0, COL_EQUALS, 3, cv2.LINE_AA)

        # Tiles (non-grabbed, non-placed first)
        for tile in self.tiles:
            if not tile.grabbed and tile.placed_in is None:
                tile.draw(canvas)

        # Grabbed tile on top
        if self.grabbed_tile:
            self.grabbed_tile.draw(canvas)

        # Cursor
        if self.tracker.index_pos:
            px, py = self.tracker.index_pos
            if self.tracker.is_pinching:
                # Pinching cursor — solid red with pulsing ring
                pulse = int(4 * math.sin(time.time() * 10))
                cv2.circle(canvas, (px, py), 14, COL_TILE_GRAB, -1)
                cv2.circle(canvas, (px, py), 18 + pulse, COL_TEXT, 2)
                # "GRAB" label near cursor
                cv2.putText(canvas, "GRAB", (px + 22, py - 8),
                            font, 0.45, COL_TILE_GRAB, 1, cv2.LINE_AA)
            else:
                # Open cursor — yellow dot
                cv2.circle(canvas, (px, py), 9, COL_CURSOR, -1)
                cv2.circle(canvas, (px, py), 11, COL_TEXT, 1)

        # ── Pinch status indicator (bottom-left) ─────────────
        status_y = WINDOW_H - 70
        if self.tracker.index_pos:
            if self.tracker.is_pinching:
                cv2.circle(canvas, (30, status_y), 10, COL_TILE_GRAB, -1)
                cv2.putText(canvas, "PINCHING", (48, status_y + 6),
                            font, 0.5, COL_TILE_GRAB, 1, cv2.LINE_AA)
            else:
                cv2.circle(canvas, (30, status_y), 10, COL_CORRECT, -1)
                cv2.putText(canvas, "HAND OK", (48, status_y + 6),
                            font, 0.5, COL_CORRECT, 1, cv2.LINE_AA)
        else:
            cv2.circle(canvas, (30, status_y), 10, (80, 80, 80), -1)
            cv2.putText(canvas, "NO HAND", (48, status_y + 6),
                        font, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

        # Message toast
        if self.message and time.time() - self.message_time < 2.5:
            (tw, th), _ = cv2.getTextSize(self.message, font, 1.1, 2)
            mx = (WINDOW_W - tw) // 2
            my = WINDOW_H - 100
            pad = 15
            cv2.rectangle(canvas, (mx - pad, my - th - pad),
                          (mx + tw + pad, my + pad), self.message_color, -1)
            cv2.rectangle(canvas, (mx - pad, my - th - pad),
                          (mx + tw + pad, my + pad), COL_TEXT, 2)
            cv2.putText(canvas, self.message, (mx, my), font, 1.1, COL_TEXT, 2, cv2.LINE_AA)

        self._draw_controls(canvas)

        # Celebration overlay
        if self.show_celebration:
            elapsed = time.time() - self.celebration_start
            if elapsed < 3.5:
                self._draw_celebration(canvas, elapsed)
            else:
                self.show_celebration = False
                self._new_puzzle()

    def _draw_celebration(self, canvas, elapsed):
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Dark overlay
        overlay = canvas.copy()
        cv2.rectangle(overlay, (0, 0), (WINDOW_W, WINDOW_H), (0, 0, 0), -1)
        alpha = min(0.65, elapsed * 2)
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

        # ─── Stars / sparkles ─────────────────────────────────
        num_sparkles = min(int(elapsed * 20), 50)
        random.seed(42)  # consistent sparkle positions per frame cycle
        for i in range(num_sparkles):
            sx = random.randint(50, WINDOW_W - 50)
            sy = random.randint(50, WINDOW_H - 50)
            brightness = int(128 + 127 * math.sin(elapsed * 5 + i))
            size = random.randint(2, 6)
            col = (brightness, brightness, min(255, brightness + 80))
            # Star shape
            cv2.circle(canvas, (sx, sy), size, col, -1)
            cv2.line(canvas, (sx - size * 2, sy), (sx + size * 2, sy), col, 1)
            cv2.line(canvas, (sx, sy - size * 2), (sx, sy + size * 2), col, 1)
        random.seed()  # restore random

        # ─── CONGRATULATIONS text ────────────────────────────
        pulse = 1.0 + 0.12 * math.sin(elapsed * 8)
        scale = 2.0 * pulse
        congrats = "CONGRATULATIONS!"
        (tw, th), _ = cv2.getTextSize(congrats, font, scale, 4)
        cx = (WINDOW_W - tw) // 2
        cy_text = WINDOW_H // 2 - 80

        # Glow layers
        cv2.putText(canvas, congrats, (cx, cy_text), font, scale, (0, 80, 0), 8, cv2.LINE_AA)
        cv2.putText(canvas, congrats, (cx, cy_text), font, scale, (0, 200, 0), 4, cv2.LINE_AA)
        cv2.putText(canvas, congrats, (cx, cy_text), font, scale, COL_CORRECT, 3, cv2.LINE_AA)

        # ─── Clapping line ────────────────────────────────────
        clap = ">> CLAP! CLAP! CLAP! <<"
        (tw2, _), _ = cv2.getTextSize(clap, font, 0.9, 2)
        cx2 = (WINDOW_W - tw2) // 2
        bounce = int(8 * math.sin(elapsed * 10))
        cv2.putText(canvas, clap, (cx2, cy_text + 60 + bounce),
                    font, 0.9, COL_SCORE, 2, cv2.LINE_AA)

        # ─── Score popup ─────────────────────────────────────
        pts = 10 * self.level
        score_msg = f"+{pts} POINTS!"
        (tw3, _), _ = cv2.getTextSize(score_msg, font, 1.2, 3)
        cx3 = (WINDOW_W - tw3) // 2
        cv2.putText(canvas, score_msg, (cx3, cy_text + 120),
                    font, 1.2, (0, 255, 255), 3, cv2.LINE_AA)

        # ─── Total score ─────────────────────────────────────
        total_msg = f"Total Score: {self.score}"
        (tw4, _), _ = cv2.getTextSize(total_msg, font, 0.8, 2)
        cx4 = (WINDOW_W - tw4) // 2
        cv2.putText(canvas, total_msg, (cx4, cy_text + 165),
                    font, 0.8, (200, 200, 200), 2, cv2.LINE_AA)

        # ─── Firework rings ──────────────────────────────────
        centers = [(300, 250), (980, 250), (640, 200), (200, 400), (1080, 400)]
        for ci, (fcx, fcy) in enumerate(centers):
            radius = int((elapsed * 80 + ci * 30) % 120)
            fade = max(0, 255 - radius * 3)
            if fade > 20:
                color = (
                    (fade + ci * 40) % 256,
                    (fade + ci * 80) % 256,
                    fade,
                )
                cv2.circle(canvas, (fcx, fcy), radius, color, 2)

    # ── Main loop ─────────────────────────────────────────────
    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("\n❌  ERROR: Cannot open webcam!")
            print("   Make sure a camera is connected and not in use by another app.")
            print("   Try changing cv2.VideoCapture(0) to (1) if you have multiple cameras.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_H)

        print("\n✅  Game started! Show your hand to the camera.")
        print("   PINCH (thumb + index finger) to grab tiles.")
        print("   Press [C] to check, [R] to reset, [N] for next, [Q] to quit.\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌  Failed to read from camera.")
                break

            # Mirror so movements feel natural
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (WINDOW_W, WINDOW_H))

            # Hand tracking
            frame = self.tracker.process(frame)

            # Darken camera feed so UI stands out
            canvas = (frame * 0.2).astype(np.uint8)

            # Gesture handling
            if not self.show_celebration:
                self._handle_hand()

            # Render
            self._draw_ui(canvas)

            cv2.imshow("Math Puzzle Game", canvas)

            key = cv2.waitKey(1000 // FPS) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c"):
                if not self.show_celebration:
                    self._check_answer()
            elif key == ord("r"):
                for tile in self.tiles:
                    tile.reset_position()
                for ch in self.chambers:
                    ch.tile = None
                self._show_message("Puzzle reset!", COL_SCORE)
            elif key == ord("n"):
                self._new_puzzle()
                self._show_message("New puzzle!", COL_SCORE)

        cap.release()
        cv2.destroyAllWindows()
        print(f"\n{'='*50}")
        print(f"  GAME OVER")
        print(f"  Final Score : {self.score}")
        print(f"  Puzzles Solved : {self.puzzles_solved}")
        print(f"  Final Level : {self.level}")
        print(f"{'='*50}")


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("   MATH PUZZLE - Hand Gesture Game")
    print(f"   MediaPipe version: {mp.__version__}")
    print(f"   API mode: {'New Tasks API' if USE_NEW_API else 'Legacy Solutions API'}")
    print("=" * 60)
    game = MathPuzzleGame()
    game.run()