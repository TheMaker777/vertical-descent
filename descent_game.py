import pygame
import sys
import random
import os
import time
import json

# ----------------------------
# Utility: resource paths
# ----------------------------
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
DATA_FILE = os.path.join(BASE_DIR, "descent_data.json")

# ----------------------------
# Simple JSON-like storage
# ----------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "leaderboards": {
                "Easy": [],
                "Normal": [],
                "Hard": []
            },
            "settings": {
                "difficulty": "Normal",
                "gradual_speed": True
            }
        }
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "leaderboards": {
                "Easy": [],
                "Normal": [],
                "Hard": []
            },
            "settings": {
                "difficulty": "Normal",
                "gradual_speed": True
            }
        }

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

# ----------------------------
# Game setup
# ----------------------------
pygame.init()
pygame.display.set_caption("Descent Game")

# TRUE fullscreen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
DARK_BG = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (220, 40, 40)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
HIGHLIGHT = (255, 255, 0)

# Game states (for clarity, all handled in functions)
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_LEADERBOARD = "leaderboard"
STATE_SETTINGS = "settings"
STATE_GAME_OVER = "game_over"
STATE_NAME_ENTRY = "name_entry"

DIFFICULTIES = ["Easy", "Normal", "Hard"]

# Load data
data = load_data()
current_difficulty = data["settings"].get("difficulty", "Normal")
gradual_speed_enabled = data["settings"].get("gradual_speed", True)

# ----------------------------
# Scaling helpers
# ----------------------------
def get_screen_size():
    info = pygame.display.Info()
    return info.current_w, info.current_h

# Base design resolution
BASE_W = 1920
BASE_H = 1080
screen_w, screen_h = get_screen_size()

def scale_value(base, reference, actual):
    return int(base * (actual / reference))

def sw(x):
    return scale_value(x, BASE_W, screen_w)

def sh(y):
    return scale_value(y, BASE_H, screen_h)

# Fonts
def get_font(size):
    return pygame.font.SysFont("arial", size)

# ----------------------------
# Button class (responsive)
# ----------------------------
class Button:
    def __init__(self, rect, text, font_size, callback):
        self.base_rect = pygame.Rect(rect)
        self.text = text
        self.font_size = font_size
        self.callback = callback
        self.hover = False

    def get_rect(self):
        return pygame.Rect(
            sw(self.base_rect.x),
            sh(self.base_rect.y),
            sw(self.base_rect.w),
            sh(self.base_rect.h),
        )

    def draw(self, surface):
        rect = self.get_rect()
        font = get_font(int(sh(self.font_size)))
        color = LIGHT_GRAY if self.hover else GRAY
        pygame.draw.rect(surface, color, rect, border_radius=sh(10))
        text_surf = font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.get_rect().collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.get_rect().collidepoint(event.pos):
                self.callback()

# ----------------------------
# Platform class
# ----------------------------
class Platform:
    def __init__(self, y, speed, gap_center_x, gap_width):
        self.y = y
        self.speed = speed
        self.gap_center_x = gap_center_x
        self.gap_width = gap_width
        self.height = sh(20)

    def update(self):
        self.y -= self.speed

    def draw(self, surface):
        y = int(self.y)
        height = self.height
        gap_half = self.gap_width // 2
        left_rect = pygame.Rect(0, y, max(0, self.gap_center_x - gap_half), height)
        right_rect = pygame.Rect(self.gap_center_x + gap_half, y,
                                 screen_w - (self.gap_center_x + gap_half), height)
        pygame.draw.rect(surface, WHITE, left_rect)
        pygame.draw.rect(surface, WHITE, right_rect)

    def collides_with(self, rect):
        y = int(self.y)
        platform_rect = pygame.Rect(0, y, screen_w, self.height)
        return platform_rect.colliderect(rect)

    def get_solid_areas(self):
        y = int(self.y)
        height = self.height
        gap_half = self.gap_width // 2
        left = pygame.Rect(0, y, max(0, self.gap_center_x - gap_half), height)
        right = pygame.Rect(self.gap_center_x + gap_half, y,
                            screen_w - (self.gap_center_x + gap_half), height)
        areas = []
        if left.width > 0:
            areas.append(left)
        if right.width > 0:
            areas.append(right)
        return areas

# ----------------------------
# Player class (fixed collisions)
# ----------------------------
class Player:
    def __init__(self):
        self.size = sw(40)
        self.x = screen_w // 2 - self.size // 2
        self.y = screen_h - self.size - sh(10)
        self.vel_y = 0
        self.on_ground = True

    def reset(self):
        self.x = screen_w // 2 - self.size // 2
        self.y = screen_h - self.size - sh(10)
        self.vel_y = 0
        self.on_ground = True

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def update(self, gravity, platforms):
        # Apply gravity
        self.vel_y += gravity
        self.y += self.vel_y

        # Bottom invisible platform
        if self.y + self.size >= screen_h:
            self.y = screen_h - self.size
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # Platform collision from above only
        player_rect = self.rect()
        for p in platforms:
            for area in p.get_solid_areas():
                if player_rect.colliderect(area):
                    # Only land on platform if falling and previous frame was above it
                    prev_bottom = self.y + self.size - self.vel_y
                    if self.vel_y > 0 and prev_bottom <= area.top:
                        self.y = area.top - self.size
                        self.vel_y = 0
                        self.on_ground = True

    def jump(self, jump_strength):
        if self.on_ground:
            self.vel_y = -jump_strength
            self.on_ground = False

    def draw(self, surface):
        pygame.draw.rect(surface, RED, self.rect())

# ----------------------------
# Difficulty settings
# ----------------------------
def get_difficulty_params(difficulty):
    base_platform_speed = sh(4)  # Same base speed across difficulties
    if difficulty == "Easy":
        gravity = 0.55
        spawn_interval = 1.2
    elif difficulty == "Hard":
        gravity = 0.85
        spawn_interval = 0.6
    else:  # Normal
        gravity = 0.7
        spawn_interval = 0.9
    return gravity, spawn_interval, base_platform_speed

# ----------------------------
# Leaderboard helpers
# ----------------------------
def add_score(difficulty, name, score):
    leaderboard = data["leaderboards"].get(difficulty, [])
    leaderboard.append({"name": name, "score": score})
    leaderboard.sort(key=lambda e: e["score"], reverse=True)
    leaderboard[:] = leaderboard[:10]
    data["leaderboards"][difficulty] = leaderboard
    save_data(data)

def clear_leaderboard(difficulty):
    data["leaderboards"][difficulty] = []
    save_data(data)

# ----------------------------
# Gradual speed handling
# ----------------------------
def get_current_platform_speed(base_speed, score):
    if gradual_speed_enabled:
        # Linear increase with score, same rate across difficulties
        return base_speed + sh(0.02) * score
    return base_speed

# ----------------------------
# Text helpers
# ----------------------------
def draw_centered_text(surface, text, size, y, color=BLACK):
    font = get_font(int(sh(size)))
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen_w // 2, y))
    surface.blit(surf, rect)

def draw_left_text(surface, text, size, x, y, color=BLACK):
    font = get_font(int(sh(size)))
    surf = font.render(text, True, color)
    rect = surf.get_rect(topleft=(x, y))
    surface.blit(surf, rect)

# ----------------------------
# Fullscreen toggle
# ----------------------------
def toggle_fullscreen():
    global screen, screen_w, screen_h
    fullscreen = screen.get_flags() & pygame.FULLSCREEN
    if fullscreen:
        screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
    else:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_w, screen_h = get_screen_size()

# ----------------------------
# Core game loop
# ----------------------------
def play_game():
    global screen_w, screen_h

    gravity, spawn_interval, base_platform_speed = get_difficulty_params(current_difficulty)
    player = Player()
    platforms = []

    last_spawn_time = time.time()
    score = 0.0
    running = True
    game_over = False
    game_over_time = 0

    while running:
        dt = clock.tick(60) / 1000.0
        score += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                    player.jump(sh(18))
                if event.key == pygame.K_F11:
                    toggle_fullscreen()

        # Current platform speed (gradual speed feature)
        current_speed = get_current_platform_speed(base_platform_speed, score)

        # Spawn platforms
        if time.time() - last_spawn_time > spawn_interval:
            gap_center_x = random.randint(sw(200), screen_w - sw(200))
            gap_width = sw(200)
            platforms.append(Platform(screen_h, current_speed, gap_center_x, gap_width))
            last_spawn_time = time.time()

        # Move platforms
        for p in platforms:
            p.speed = current_speed
            p.update()

        # Remove off-screen platforms
        platforms = [p for p in platforms if p.y + p.height > 0]

        # Update player
        player.update(gravity, platforms)

        # Top collision = game over
        if player.y <= 0:
            game_over = True
            if game_over_time == 0:
                game_over_time = time.time()

        # Draw
        screen.fill(DARK_BG)
        for p in platforms:
            p.draw(screen)
        player.draw(screen)

        score_text = f"Score: {int(score)}"
        draw_left_text(screen, score_text, 32, sw(20), sh(20))

        difficulty_text = f"Difficulty: {current_difficulty}"
        draw_left_text(screen, difficulty_text, 28, sw(20), sh(60))

        pygame.display.flip()

        # After short delay, leave to name entry
        if game_over and time.time() - game_over_time > 0.8:
            return int(score)

# ----------------------------
# Name entry screen
# ----------------------------
def name_entry_screen(score):
    name = ""
    active = True
    while active:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_RETURN:
                    trimmed = name.strip()
                    if trimmed == "":
                        trimmed = "Player"
                    add_score(current_difficulty, trimmed, score)
                    return
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 12 and event.unicode.isprintable():
                        name += event.unicode
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()

        screen.fill(DARK_BG)
        draw_centered_text(screen, "GAME OVER", 64, sh(150))
        draw_centered_text(screen, f"Score: {score}", 48, sh(230))
        draw_centered_text(screen, "Enter your name:", 36, sh(320))

        font = get_font(int(sh(40)))
        rect = pygame.Rect(0, 0, sw(600), sh(80))
        rect.center = (screen_w // 2, sh(420))
        pygame.draw.rect(screen, WHITE, rect, border_radius=sh(10))
        text_surf = font.render(name, True, BLACK)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

        draw_centered_text(screen, "Press Enter to confirm, ESC to skip", 28, sh(520))

        pygame.display.flip()

# ----------------------------
# Leaderboard screen
# ----------------------------
def leaderboard_screen():
    selected_diff = "Easy"

    def set_diff_easy():
        nonlocal selected_diff
        selected_diff = "Easy"

    def set_diff_normal():
        nonlocal selected_diff
        selected_diff = "Normal"

    def set_diff_hard():
        nonlocal selected_diff
        selected_diff = "Hard"

    btn_easy = Button((BASE_W * 0.15, BASE_H * 0.15, BASE_W * 0.2, BASE_H * 0.08),
                      "Easy", 36, set_diff_easy)
    btn_normal = Button((BASE_W * 0.4, BASE_H * 0.15, BASE_W * 0.2, BASE_H * 0.08),
                        "Normal", 36, set_diff_normal)
    btn_hard = Button((BASE_W * 0.65, BASE_H * 0.15, BASE_W * 0.2, BASE_H * 0.08),
                      "Hard", 36, set_diff_hard)

    while True:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            btn_easy.handle_event(event)
            btn_normal.handle_event(event)
            btn_hard.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_F11:
                    toggle_fullscreen()

        screen.fill(DARK_BG)

        draw_centered_text(screen, "LEADERBOARD", 64, sh(80))

        btn_easy.draw(screen)
        btn_normal.draw(screen)
        btn_hard.draw(screen)

        lb = data["leaderboards"].get(selected_diff, [])
        start_y = sh(220)
        font = get_font(int(sh(32)))
        x_name = sw(600)
        x_score = sw(1150)
        header_surf = font.render(f"{selected_diff} Scores", True, BLACK)
        header_rect = header_surf.get_rect(center=(screen_w // 2, sh(180)))
        screen.blit(header_surf, header_rect)

        for idx, entry in enumerate(lb[:10]):
            y = start_y + idx * sh(40)
            name_text = f"{idx+1}. {entry['name']}"
            score_text = str(entry['score'])
            name_surf = font.render(name_text, True, BLACK)
            score_surf = font.render(score_text, True, BLACK)
            screen.blit(name_surf, (x_name, y))
            screen.blit(score_surf, (x_score, y))

        pygame.display.flip()

# ----------------------------
# Settings screen (with secret slider)
# ----------------------------
def slider_rect(base_rect):
    return pygame.Rect(
        sw(base_rect.x),
        sh(base_rect.y),
        sw(base_rect.w),
        sh(base_rect.h),
    )

def settings_screen():
    global current_difficulty, gradual_speed_enabled

    # Secret: reveal slider after typing "help" quickly
    secret_sequence = "help"
    secret_index = 0
    secret_visible = False
    last_key_time = 0
    secret_timeout = 1.3  # seconds

    def set_easy():
        nonlocal secret_visible
        current_difficulty = "Easy"
        data["settings"]["difficulty"] = current_difficulty
        save_data(data)

    def set_normal():
        nonlocal secret_visible
        current_difficulty = "Normal"
        data["settings"]["difficulty"] = current_difficulty
        save_data(data)

    def set_hard():
        nonlocal secret_visible
        current_difficulty = "Hard"
        data["settings"]["difficulty"] = current_difficulty
        save_data(data)

    def clear_easy():
        clear_leaderboard("Easy")

    def clear_normal():
        clear_leaderboard("Normal")

    def clear_hard():
        clear_leaderboard("Hard")

    btn_easy = Button((BASE_W * 0.15, BASE_H * 0.2, BASE_W * 0.2, BASE_H * 0.08),
                      "Easy", 32, set_easy)
    btn_normal = Button((BASE_W * 0.4, BASE_H * 0.2, BASE_W * 0.2, BASE_H * 0.08),
                        "Normal", 32, set_normal)
    btn_hard = Button((BASE_W * 0.65, BASE_H * 0.2, BASE_W * 0.2, BASE_H * 0.08),
                      "Hard", 32, set_hard)

    btn_clear_easy = Button((BASE_W * 0.15, BASE_H * 0.32, BASE_W * 0.2, BASE_H * 0.06),
                            "Clear Easy", 28, clear_easy)
    btn_clear_normal = Button((BASE_W * 0.4, BASE_H * 0.32, BASE_W * 0.2, BASE_H * 0.06),
                              "Clear Normal", 28, clear_normal)
    btn_clear_hard = Button((BASE_W * 0.65, BASE_H * 0.32, BASE_W * 0.2, BASE_H * 0.06),
                            "Clear Hard", 28, clear_hard)

    slider_rect_base = pygame.Rect(BASE_W * 0.3, BASE_H * 0.5, BASE_W * 0.4, BASE_H * 0.08)
    dragging = False

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            btn_easy.handle_event(event)
            btn_normal.handle_event(event)
            btn_hard.handle_event(event)
            btn_clear_easy.handle_event(event)
            btn_clear_normal.handle_event(event)
            btn_clear_hard.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_F11:
                    toggle_fullscreen()

                # Secret sequence logic for "help"
                now = time.time()
                ch = event.unicode.lower()
                if now - last_key_time > secret_timeout:
                    secret_index = 0
                last_key_time = now
                if secret_index < len(secret_sequence) and ch == secret_sequence[secret_index]:
                    secret_index += 1
                    if secret_index == len(secret_sequence):
                        secret_visible = True
                        secret_index = 0
                else:
                    if ch:
                        secret_index = 0

            if secret_visible:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if slider_rect(slider_rect_base).collidepoint(event.pos):
                        dragging = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging = False
                elif event.type == pygame.MOUSEMOTION and dragging:
                    rect = slider_rect(slider_rect_base)
                    x = event.pos[0]
                    center = rect.centerx
                    if x >= center:
                        gradual_speed_enabled = True
                    else:
                        gradual_speed_enabled = False
                    data["settings"]["gradual_speed"] = gradual_speed_enabled
                    save_data(data)

        screen.fill(DARK_BG)
        draw_centered_text(screen, "SETTINGS", 64, sh(80))

        btn_easy.draw(screen)
        btn_normal.draw(screen)
        btn_hard.draw(screen)

        btn_clear_easy.draw(screen)
        btn_clear_normal.draw(screen)
        btn_clear_hard.draw(screen)

        # Highlight current difficulty
        if current_difficulty == "Easy":
            active_btn = btn_easy
        elif current_difficulty == "Hard":
            active_btn = btn_hard
        else:
            active_btn = btn_normal
        rect = active_btn.get_rect()
        pygame.draw.rect(screen, HIGHLIGHT, rect, width=sh(4), border_radius=sh(10))

        # Secret gradual speed slider (only visible after "help")
        if secret_visible:
            rect = slider_rect(slider_rect_base)
            pygame.draw.rect(screen, WHITE, rect, border_radius=sh(10))
            inner = rect.inflate(-sh(10), -sh(10))
            pygame.draw.rect(screen, DARK_BG, inner, border_radius=sh(8))

            knob_width = inner.width // 2
            if gradual_speed_enabled:
                knob_rect = pygame.Rect(inner.centerx, inner.y, knob_width, inner.height)
            else:
                knob_rect = pygame.Rect(inner.x, inner.y, knob_width, inner.height)
            pygame.draw.rect(screen, WHITE, knob_rect, border_radius=sh(8))

            font = get_font(int(sh(26)))
            label = "Gradual Speed: ON" if gradual_speed_enabled else "Gradual Speed: OFF"
            text_surf = font.render(label, True, BLACK)
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        pygame.display.flip()

# ----------------------------
# Main menu
# ----------------------------
def main_menu():
    logo_size = sh(80)

    def play():
        result = play_game()
        if result is None:
            return
        name_entry_screen(result)

    def leaderboard():
        leaderboard_screen()

    def settings():
        settings_screen()

    btn_play = Button((BASE_W * 0.35, BASE_H * 0.45, BASE_W * 0.3, BASE_H * 0.09),
                      "Play", 40, play)
    btn_leaderboard = Button((BASE_W * 0.35, BASE_H * 0.57, BASE_W * 0.3, BASE_H * 0.09),
                             "Leaderboard", 40, leaderboard)
    btn_settings = Button((BASE_W * 0.35, BASE_H * 0.69, BASE_W * 0.3, BASE_H * 0.09),
                          "Settings", 40, settings)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            btn_play.handle_event(event)
            btn_leaderboard.handle_event(event)
            btn_settings.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_F11:
                    toggle_fullscreen()

        screen.fill(DARK_BG)

        # Red square logo
        logo_rect = pygame.Rect(0, 0, logo_size, logo_size)
        logo_rect.center = (screen_w // 2, sh(150))
        pygame.draw.rect(screen, RED, logo_rect)

        # Title
        draw_centered_text(screen, "DESCENT", 72, sh(260))

        btn_play.draw(screen)
        btn_leaderboard.draw(screen)
        btn_settings.draw(screen)

        pygame.display.flip()

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    main_menu()
