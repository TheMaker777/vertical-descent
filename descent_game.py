import pygame
import random
import sys
import os
import json

try:
    pygame.init()
except Exception as e:
    print(f"Pygame init failed: {e}")
    input("Press Enter to exit...")
    sys.exit()

# Proper fullscreen that fills screen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH = screen.get_width()
HEIGHT = screen.get_height()
pygame.display.set_caption("Descent Game")
clock = pygame.time.Clock()

# Colors
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG = (20, 20, 20)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)

# Fonts - scale to screen
title_font = pygame.font.SysFont(None, min(72, HEIGHT // 10))
font = pygame.font.SysFont(None, min(48, HEIGHT // 12))
small_font = pygame.font.SysFont(None, min(36, HEIGHT // 16))

# Game state
state = "menu"
player_size = min(WIDTH, HEIGHT) // 20
player_x = WIDTH // 2 - player_size // 2
player_y = HEIGHT // 4
player_speed = max(WIDTH, HEIGHT) // 100
gravity = 0.3
velocity_y = 0
platform_height = max(WIDTH, HEIGHT) // 40
gap_width = WIDTH // 4
platforms = []
platform_speed = 2
spawn_timer = 0
score = 0
difficulty = "normal"
game_mode = "normal"
leaderboard_mode = "normal"
gradual_speed = True  # Always enabled by default, same across difficulties
help_typed = False  # Secret settings access

# Difficulty settings (speed same across all, only spawn_rate/gravity differ)
DIFFICULTY = {
    "easy": {"speed": 2.0, "spawn_rate": 90, "gravity": 0.2},
    "normal": {"speed": 2.0, "spawn_rate": 60, "gravity": 0.4},
    "hard": {"speed": 2.0, "spawn_rate": 40, "gravity": 0.6}
}

SCORE_FILES = {
    "easy": "highscores_easy.json",
    "normal": "highscores_normal.json",
    "hard": "highscores_hard.json"
}

def load_scores(mode):
    filename = SCORE_FILES[mode]
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass
    return []

def save_score(mode, name, score_value):
    filename = SCORE_FILES[mode]
    scores = load_scores(mode)
    scores.append({"name": name, "score": score_value})
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:5]
    with open(filename, "w") as f:
        json.dump(scores, f)

def clear_leaderboard(mode):
    filename = SCORE_FILES[mode]
    if os.path.exists(filename):
        os.remove(filename)

def draw_button(text, x, y, w, h, color=WHITE, hover_color=GREEN, selected=False):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    rect = pygame.Rect(x, y, w, h)
    if rect.collidepoint(mouse):
        pygame.draw.rect(screen, hover_color, rect)
        if click[0] == 1 and not selected:
            return True
    else:
        pygame.draw.rect(screen, color if not selected else GREEN, rect)
    pygame.draw.rect(screen, WHITE, rect, 3)

    text_surf = small_font.render(text, True, BLACK)
    screen.blit(
        text_surf,
        (
            x + (w - text_surf.get_width()) // 2,
            y + (h - text_surf.get_height()) // 2,
        ),
    )
    return False

def draw_checkbox_slider(x, y, w, h, enabled):
    # Slider background
    pygame.draw.rect(screen, GRAY, (x, y, w, h))
    pygame.draw.rect(screen, WHITE, (x, y, w, h), 2)

    # Fill if enabled
    if enabled:
        pygame.draw.rect(screen, GREEN, (x, y, w, h))

    # Slider knob
    knob_x = x + 5 if enabled else x + w - 15
    pygame.draw.circle(screen, WHITE, (int(knob_x + 10), y + h // 2), 10)

def draw_home_menu():
    screen.fill(BG)

    logo_size = min(WIDTH, HEIGHT) // 8
    pygame.draw.rect(
        screen,
        RED,
        (
            WIDTH // 2 - logo_size // 2,
            HEIGHT // 4 - logo_size // 2,
            logo_size,
            logo_size,
        ),
    )

    title = title_font.render("DESCENT", True, BLACK)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4 - 140))

    btn_w, btn_h = WIDTH // 3, HEIGHT // 12
    btn_y = HEIGHT // 2
    play_clicked = draw_button("PLAY", WIDTH // 2 - btn_w // 2, btn_y, btn_w, btn_h)
    leaderboard_clicked = draw_button(
        "LEADERBOARD",
        WIDTH // 2 - btn_w // 2,
        btn_y + btn_h + 20,
        btn_w,
        btn_h,
    )
    settings_clicked = draw_button(
        "SETTINGS",
        WIDTH // 2 - btn_w // 2,
        btn_y + 2 * (btn_h + 20),
        btn_w,
        btn_h,
    )

    return play_clicked, leaderboard_clicked, settings_clicked

def draw_settings():
    global help_typed, gradual_speed, difficulty

    screen.fill(BG)
    title = title_font.render("SETTINGS", True, BLACK)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

    # Difficulty buttons
    btn_w, btn_h = WIDTH // 5, HEIGHT // 14
    y_start = HEIGHT // 3
    easy_x = WIDTH // 2 - btn_w * 1.5 - 20
    normal_x = WIDTH // 2 - btn_w // 2
    hard_x = WIDTH // 2 + btn_w * 0.5 + 20

    easy_clicked = draw_button(
        "EASY", easy_x, y_start, btn_w, btn_h, selected=difficulty == "easy"
    )
    normal_clicked = draw_button(
        "NORMAL", normal_x, y_start, btn_w, btn_h, selected=difficulty == "normal"
    )
    hard_clicked = draw_button(
        "HARD", hard_x, y_start, btn_w, btn_h, selected=difficulty == "hard"
    )

    # Clear buttons
    clear_y = y_start + btn_h + 40
    clear_easy = draw_button("Clear Easy", easy_x, clear_y, btn_w, btn_h // 1.3)
    clear_normal = draw_button("Clear Normal", normal_x, clear_y, btn_w, btn_h // 1.3)
    clear_hard = draw_button("Clear Hard", hard_x, clear_y, btn_w, btn_h // 1.3)

    # SECRET gradual speed checkbox slider (type "help")
    slider_y = HEIGHT // 2 + 40
    if help_typed:
        slider_title = small_font.render("Gradual Speed Increase", True, BLACK)
        screen.blit(slider_title, (WIDTH // 2 - 200, slider_y - 30))
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        slider_rect = pygame.Rect(WIDTH // 2 - 100, slider_y, 200, 30)
        draw_checkbox_slider(
            slider_rect.x, slider_rect.y, slider_rect.w, slider_rect.h, gradual_speed
        )
        if slider_rect.collidepoint(mouse) and click[0] == 1:
            gradual_speed = not gradual_speed

    back_clicked = draw_button(
        "BACK", WIDTH // 2 - 100, HEIGHT - 100, 200, HEIGHT // 15
    )

    return {
        "easy": easy_clicked,
        "normal": normal_clicked,
        "hard": hard_clicked,
        "clear_easy": clear_easy,
        "clear_normal": clear_normal,
        "clear_hard": clear_hard,
        "back": back_clicked,
    }

def draw_leaderboards():
    global leaderboard_mode

    screen.fill(BG)

    title = title_font.render(f"{leaderboard_mode.upper()} LEADERBOARD", True, BLACK)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

    # Current leaderboard
    scores = load_scores(leaderboard_mode)
    y_offset = 160
    line_spacing = 50

    if not scores:
        no_scores = font.render("No scores yet", True, BLACK)
        screen.blit(no_scores, (WIDTH // 2 - no_scores.get_width() // 2, y_offset))
    else:
        for i, entry in enumerate(scores):
            name_text = f"{i+1}. {entry['name']}"
            score_text = str(entry["score"])

            name_surf = font.render(name_text, True, BLACK)
            score_surf = font.render(score_text, True, BLACK)

            # Positioning
            name_x = WIDTH // 4
            score_x = WIDTH * 3 // 4 - score_surf.get_width() // 2
            y = y_offset + i * line_spacing

            # Small white backdrop behind the name only
            padding_x = 10
            padding_y = 4
            name_bg_rect = pygame.Rect(
                name_x - padding_x,
                y - padding_y,
                name_surf.get_width() + 2 * padding_x,
                name_surf.get_height() + 2 * padding_y,
            )
            pygame.draw.rect(screen, WHITE, name_bg_rect, border_radius=6)

            # Draw text
            screen.blit(name_surf, (name_x, y))
            screen.blit(score_surf, (score_x, y))

    # Difficulty selector buttons at the bottom
    btn_w, btn_h = WIDTH // 6, HEIGHT // 14
    btn_y = HEIGHT - 120
    easy_lb = draw_button(
        "EASY",
        WIDTH // 2 - btn_w * 1.5 - 20,
        btn_y,
        btn_w,
        btn_h,
        selected=leaderboard_mode == "easy",
    )
    normal_lb = draw_button(
        "NORMAL",
        WIDTH // 2 - btn_w // 2,
        btn_y,
        btn_w,
        btn_h,
        selected=leaderboard_mode == "normal",
    )
    hard_lb = draw_button(
        "HARD",
        WIDTH // 2 + btn_w * 0.5 + 20,
        btn_y,
        btn_w,
        btn_h,
        selected=leaderboard_mode == "hard",
    )

    back_clicked = draw_button(
        "BACK", WIDTH // 2 - 100, HEIGHT - 60, 200, HEIGHT // 18
    )

    return {
        "easy_lb": easy_lb,
        "normal_lb": normal_lb,
        "hard_lb": hard_lb,
        "back": back_clicked,
    }

def spawn_platform():
    gap_x = random.randint(0, WIDTH - gap_width)
    platforms.append({"y": HEIGHT, "gap_x": gap_x, "scored": False})

def reset_game():
    global player_x, player_y, velocity_y, platforms, platform_speed, spawn_timer, score, game_mode
    player_x = WIDTH // 2 - player_size // 2
    player_y = HEIGHT // 4
    velocity_y = 0
    platforms = []
    platform_speed = DIFFICULTY[difficulty]["speed"]
    spawn_timer = 0
    score = 0
    game_mode = difficulty

def main_game():
    global player_x, player_y, velocity_y, platforms, platform_speed, spawn_timer, score
    reset_game()
    running = True
    settings = DIFFICULTY[difficulty]
    base_speed = settings["speed"]

    while running:
        clock.tick(60)
        screen.fill(BG)

        # Gradual speed increase (secret feature)
        current_speed = base_speed
        if gradual_speed:
            current_speed += score * 0.02  # Simple gradual increase

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, 0
                if event.key == pygame.K_F11:  # F11 toggle fullscreen (backup)
                    pygame.display.toggle_fullscreen()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]:
            # Jump from platforms or bottom
            on_ground = player_y >= HEIGHT - player_size - 2
            on_platform = False
            for plat in platforms:
                plat_top = plat["y"]
                plat_bottom = plat["y"] + platform_height
                if (
                    player_y + player_size <= plat_top + 5
                    and player_y + player_size >= plat_top - 5
                    and player_x + player_size > plat["gap_x"] + gap_width
                ) or (
                    player_y + player_size <= plat_top + 5
                    and player_y + player_size >= plat_top - 5
                    and player_x < plat["gap_x"]
                ):
                    on_platform = True
                    break
            if on_ground or on_platform:
                velocity_y = -15

        velocity_y += settings["gravity"]
        player_y += velocity_y
        platform_speed = current_speed

        if player_x < 0:
            player_x = 0
        if player_x > WIDTH - player_size:
            player_x = WIDTH - player_size
        if player_y < 0:
            return True, score
        if player_y > HEIGHT - player_size:
            player_y = HEIGHT - player_size
            velocity_y = 0

        spawn_timer += 1
        if spawn_timer > settings["spawn_rate"]:
            spawn_platform()
            spawn_timer = 0

        # Move and draw platforms
        for plat in platforms[:]:
            plat["y"] -= platform_speed
            if plat["y"] + platform_height < 0:
                platforms.remove(plat)
                continue
            pygame.draw.rect(
                screen, WHITE, (0, plat["y"], plat["gap_x"], platform_height)
            )
            pygame.draw.rect(
                screen,
                WHITE,
                (
                    plat["gap_x"] + gap_width,
                    plat["y"],
                    WIDTH - plat["gap_x"] - gap_width,
                    platform_height,
                ),
            )

        # COLLISION: strong hitboxes for white segments
        player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        prev_player_rect = pygame.Rect(player_rect)
        prev_player_rect.y -= velocity_y

        for plat in platforms:
            plat_rect_left = pygame.Rect(0, plat["y"], plat["gap_x"], platform_height)
            plat_rect_right = pygame.Rect(
                plat["gap_x"] + gap_width,
                plat["y"],
                WIDTH - plat["gap_x"] - gap_width,
                platform_height,
            )

            for seg in [plat_rect_left, plat_rect_right]:
                if player_rect.colliderect(seg):
                    # Determine side of impact
                    from_above = prev_player_rect.bottom <= seg.top and velocity_y > 0
                    from_below = prev_player_rect.top >= seg.bottom and velocity_y < 0

                    if from_above:
                        player_y = seg.top - player_size
                        velocity_y = 0
                        player_rect.y = player_y
                    elif from_below:
                        player_y = seg.bottom
                        velocity_y = 1
                        player_rect.y = player_y

        # Scoring when passing platforms
        for plat in platforms:
            if plat["y"] + platform_height < player_y and not plat["scored"]:
                score += 1
                plat["scored"] = True

        pygame.draw.rect(screen, RED, (player_x, player_y, player_size, player_size))
        score_text = font.render(f"Score: {score} | {difficulty.upper()}", True, BLACK)
        screen.blit(score_text, (20, 20))
        controls = small_font.render(
            "A/D Arrows: Move | W/Up/Space: Jump | ESC: Menu | F11: Fullscreen",
            True,
            BLACK,
        )
        screen.blit(controls, (20, HEIGHT - 50))

        pygame.display.flip()

    return True, score

def name_entry_screen(final_score):
    name = ""
    entering = True
    while entering:
        screen.fill(BG)

        title = title_font.render(f"FINAL SCORE: {final_score}", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        prompt = font.render("Enter name:", True, BLACK)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2))

        name_surf = font.render(name + "_", True, BLACK)
        screen.blit(name_surf, (WIDTH // 2 - name_surf.get_width() // 2, HEIGHT // 2 + 60))

        info = small_font.render("ENTER=save ESC=leaderboards", True, BLACK)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 120))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
                elif event.key == pygame.K_RETURN:
                    if name.strip():
                        save_score(game_mode, name, final_score)
                    else:
                        save_score(game_mode, "PLAYER", final_score)
                    entering = False
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 12 and event.unicode.isprintable():
                        name += event.unicode
    return False

def main():
    global state, difficulty, leaderboard_mode, help_typed, gradual_speed

    print("Descent Game - TRUE FULLSCREEN!")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

                # Secret "help" detection in settings (no visual indicator)
                if state == "settings":
                    # simple sequence: type "help" quickly; we just require h,e,l,p in order
                    if event.unicode.lower() == "h":
                        help_typed = True
                    elif event.unicode.lower() in ["e", "l", "p"] and help_typed:
                        help_typed = True

        if state == "menu":
            play_clicked, leaderboard_clicked, settings_clicked = draw_home_menu()
            if play_clicked:
                state = "playing"
                leaderboard_mode = difficulty
            elif leaderboard_clicked:
                state = "leaderboards"
            elif settings_clicked:
                state = "settings"
                help_typed = False  # Reset secret each visit

        elif state == "settings":
            clicks = draw_settings()
            if clicks["easy"]:
                difficulty = "easy"
            elif clicks["normal"]:
                difficulty = "normal"
            elif clicks["hard"]:
                difficulty = "hard"
            elif clicks["clear_easy"]:
                clear_leaderboard("easy")
            elif clicks["clear_normal"]:
                clear_leaderboard("normal")
            elif clicks["clear_hard"]:
                clear_leaderboard("hard")
            elif clicks["back"]:
                state = "menu"

        elif state == "playing":
            game_over, final_score = main_game()
            if game_over:
                show_leaderboards_flag = name_entry_screen(final_score)
                if show_leaderboards_flag:
                    state = "leaderboards"
                    leaderboard_mode = game_mode
                else:
                    state = "menu"
            else:
                state = "menu"

        elif state == "leaderboards":
            clicks = draw_leaderboards()
            if clicks["easy_lb"]:
                leaderboard_mode = "easy"
            elif clicks["normal_lb"]:
                leaderboard_mode = "normal"
            elif clicks["hard_lb"]:
                leaderboard_mode = "hard"
            elif clicks["back"]:
                state = "menu"

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()
