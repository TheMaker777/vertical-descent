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

# Auto-fit to screen (not fixed size)
info = pygame.display.Info()
WIDTH = min(info.current_w * 0.9, 1000)  # 90% of screen width, max 1000
HEIGHT = min(info.current_h * 0.9, 700)  # 90% of screen height, max 700
screen = pygame.display.set_mode((int(WIDTH), int(HEIGHT)))
pygame.display.set_caption("Descent Game")
clock = pygame.time.Clock()

# Colors
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG = (20, 20, 20)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)

# Fonts
title_font = pygame.font.SysFont(None, min(72, HEIGHT//10))
font = pygame.font.SysFont(None, min(48, HEIGHT//12))
small_font = pygame.font.SysFont(None, min(36, HEIGHT//16))

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
leaderboard_mode = "normal"  # Default leaderboard
gradual_speed = True  # Default enabled
speed_increase_rate = 2  # easy=1, medium=2, hard=3
help_typed = False  # For secret slider

# Difficulty settings
DIFFICULTY = {
    "easy": {"speed": 1.5, "spawn_rate": 90, "gravity": 0.2},
    "normal": {"speed": 3.0, "spawn_rate": 60, "gravity": 0.4},
    "hard": {"speed": 6.0, "spawn_rate": 40, "gravity": 0.6}
}

# Leaderboard files
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

def save_score(mode, name, score):
    filename = SCORE_FILES[mode]
    scores = load_scores(mode)
    scores.append({"name": name, "score": score})
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
    screen.blit(text_surf, (x + (w - text_surf.get_width()) // 2, y + (h - text_surf.get_height()) // 2))
    return False

def draw_slider(x, y, w, h, value, min_val, max_val):
    # Background
    pygame.draw.rect(screen, GRAY, (x, y, w, h))
    # Fill
    fill_w = int((value - min_val) / (max_val - min_val) * w)
    pygame.draw.rect(screen, GREEN, (x, y, fill_w, h))
    pygame.draw.rect(screen, WHITE, (x, y, w, h), 2)
    
    # Knob
    knob_x = x + fill_w - 8
    pygame.draw.circle(screen, WHITE, (int(knob_x), y + h//2), 8)

def draw_home_menu():
    screen.fill(BG)
    
    logo_size = min(WIDTH, HEIGHT) // 8
    pygame.draw.rect(screen, RED, (WIDTH//2 - logo_size//2, HEIGHT//4 - logo_size//2, logo_size, logo_size))
    
    title = title_font.render("DESCENT", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4 - 140))
    
    btn_w, btn_h = WIDTH//3, HEIGHT//12
    btn_y = HEIGHT//2
    play_clicked = draw_button("PLAY", WIDTH//2 - btn_w//2, btn_y, btn_w, btn_h)
    leaderboard_clicked = draw_button("LEADERBOARD", WIDTH//2 - btn_w//2, btn_y + btn_h + 20, btn_w, btn_h)
    settings_clicked = draw_button("SETTINGS", WIDTH//2 - btn_w//2, btn_y + 2*(btn_h + 20), btn_w, btn_h)
    
    return play_clicked, leaderboard_clicked, settings_clicked

def draw_settings():
    global help_typed, gradual_speed, speed_increase_rate
    
    screen.fill(BG)
    title = title_font.render("SETTINGS", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
    
    # Difficulty buttons
    btn_w, btn_h = WIDTH//5, HEIGHT//14
    y_start = HEIGHT//3
    easy_x = WIDTH//2 - btn_w*1.5 - 20
    normal_x = WIDTH//2 - btn_w//2
    hard_x = WIDTH//2 + btn_w*0.5 + 20
    
    easy_clicked = draw_button("EASY", easy_x, y_start, btn_w, btn_h, selected=difficulty == "easy")
    normal_clicked = draw_button("NORMAL", normal_x, y_start, btn_w, btn_h, selected=difficulty == "normal")
    hard_clicked = draw_button("HARD", hard_x, y_start, btn_w, btn_h, selected=difficulty == "hard")
    
    # Clear buttons
    clear_y = y_start + btn_h + 40
    clear_easy = draw_button("Clear Easy", easy_x, clear_y, btn_w, btn_h//1.3)
    clear_normal = draw_button("Clear Normal", normal_x, clear_y, btn_w, btn_h//1.3)
    clear_hard = draw_button("Clear Hard", hard_x, clear_y, btn_w, btn_h//1.3)
    
    # Secret slider (type "help" to show)
    slider_y = HEIGHT//2 + 40
    if help_typed:
        slider_title = small_font.render("Gradual Speed Increase:", True, BLACK)
        screen.blit(slider_title, (WIDTH//2 - 200, slider_y - 30))
        draw_slider(WIDTH//2 - 150, slider_y, 300, 20, speed_increase_rate, 1, 3)
        status = small_font.render("Easy" if speed_increase_rate == 1 else "Medium" if speed_increase_rate == 2 else "Hard", True, BLACK)
        screen.blit(status, (WIDTH//2 + 160, slider_y - 5))
        gradual_text = small_font.render(f"Enabled: {'ON' if gradual_speed else 'OFF'}", True, GREEN if gradual_speed else GRAY)
        screen.blit(gradual_text, (WIDTH//2 - 100, slider_y + 30))
    
    help_text = small_font.render('"help" = secret settings', True, GRAY)
    screen.blit(help_text, (20, HEIGHT - 40))
    
    back_clicked = draw_button("BACK", WIDTH//2 - 100, HEIGHT - 100, 200, HEIGHT//15)
    
    return {
        "easy": easy_clicked, "normal": normal_clicked, "hard": hard_clicked,
        "clear_easy": clear_easy, "clear_normal": clear_normal, "clear_hard": clear_hard,
        "back": back_clicked
    }

def draw_leaderboards():
    screen.fill(BG)
    
    title = title_font.render(f"{leaderboard_mode.upper()} LEADERBOARD", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
    
    # Difficulty selector buttons
    btn_w, btn_h = WIDTH//6, HEIGHT//14
    easy_lb = draw_button("EASY", 50, 120, btn_w, btn_h, selected=leaderboard_mode == "easy")
    normal_lb = draw_button("NORMAL", WIDTH//2 - btn_w//2, 120, btn_w, btn_h, selected=leaderboard_mode == "normal")
    hard_lb = draw_button("HARD", WIDTH - 50 - btn_w, 120, btn_w, btn_h, selected=leaderboard_mode == "hard")
    
    # Current leaderboard
    scores = load_scores(leaderboard_mode)
    y_offset = 200
    if not scores:
        no_scores = font.render("No scores yet", True, BLACK)
        screen.blit(no_scores, (WIDTH//2 - no_scores.get_width()//2, y_offset))
    else:
        for i, entry in enumerate(scores):
            line = font.render(f"{i+1}. {entry['name']} - {entry['score']}", True, BLACK)
            screen.blit(line, (WIDTH//2 - line.get_width()//2, y_offset))
            y_offset += 60
    
    back_clicked = draw_button("BACK", WIDTH//2 - 100, HEIGHT - 100, 200, HEIGHT//15)
    
    return {
        "easy_lb": easy_lb, "normal_lb": normal_lb, "hard_lb": hard_lb,
        "back": back_clicked
    }

# [spawn_platform, reset_game, main_game functions unchanged - same as previous version]

def spawn_platform():
    gap_x = random.randint(0, WIDTH - gap_width)
    platforms.append({'y': HEIGHT, 'gap_x': gap_x, 'scored': False})

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
    global player_x, player_y, velocity_y, platforms, platform_speed, spawn_timer, score, gradual_speed, speed_increase_rate
    reset_game()
    running = True
    settings = DIFFICULTY[difficulty]
    base_speed = settings["speed"]
    
    while running:
        clock.tick(60)
        screen.fill(BG)

        # Gradual speed increase
        if gradual_speed:
            platform_speed = base_speed + (score * speed_increase_rate * 0.02)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]:
            if player_y >= HEIGHT - player_size - 10:
                velocity_y = -15
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            player_y += player_speed

        velocity_y += settings["gravity"]
        player_y += velocity_y

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

        for plat in platforms[:]:
            plat['y'] -= platform_speed
            if plat['y'] > HEIGHT:
                platforms.remove(plat)
                continue
            pygame.draw.rect(screen, WHITE, (0, plat['y'], plat['gap_x'], platform_height))
            pygame.draw.rect(screen, WHITE, (plat['gap_x'] + gap_width, plat['y'], WIDTH - plat['gap_x'] - gap_width, platform_height))

        for plat in platforms:
            plat_top = plat['y']
            plat_bottom = plat['y'] + platform_height
            if (player_y < plat_bottom and player_y + player_size > plat_top and
                player_x + player_size > 0 and player_x < WIDTH):
                if not (plat['gap_x'] < player_x + player_size and plat['gap_x'] + gap_width > player_x):
                    player_y = plat_top - player_size
                    velocity_y = 0

        for plat in platforms:
            if plat['y'] + platform_height < player_y and not plat['scored']:
                score += 1
                plat['scored'] = True

        pygame.draw.rect(screen, RED, (player_x, player_y, player_size, player_size))
        score_text = font.render(f"Score: {score} | {difficulty.upper()}", True, BLACK)
        screen.blit(score_text, (20, 20))
        gradual_text = small_font.render(f"Gradual: {'ON' if gradual_speed else 'OFF'}", True, GREEN if gradual_speed else GRAY)
        screen.blit(gradual_text, (20, 60))

        pygame.display.flip()

    return True, score

def name_entry_screen(final_score):
    name = ""
    entering = True
    while entering:
        screen.fill(BG)
        
        title = title_font.render(f"FINAL SCORE: {final_score}", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        
        prompt = font.render("Enter name:", True, BLACK)
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2))
        
        name_surf = font.render(name + "_", True, BLACK)
        screen.blit(name_surf, (WIDTH//2 - name_surf.get_width()//2, HEIGHT//2 + 60))
        
        info = small_font.render("ENTER=save ESC=leaderboards", True, BLACK)
        screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//2 + 120))
        
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
    global state, difficulty, leaderboard_mode, help_typed, gradual_speed, speed_increase_rate
    
    print("Descent Game - Auto-fit screen!")
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
                # Settings help detection
                if state == "settings":
                    if event.unicode.lower() == 'h' and help_typed:
                        help_typed = False
                    elif event.unicode.lower() == 'e' and help_typed:
                        help_typed = False
                    elif event.unicode.lower() == 'l' and not help_typed:
                        help_typed = True
                    elif event.unicode.lower() == 'p' and help_typed:
                        help_typed = False
        
        if state == "menu":
            play_clicked, leaderboard_clicked, settings_clicked = draw_home_menu()
            if play_clicked:
                state = "playing"
                leaderboard_mode = difficulty  # Default to current difficulty
            elif leaderboard_clicked:
                state = "leaderboards"
            elif settings_clicked:
                state = "settings"
                help_typed = False  # Reset each time
                
        elif state == "settings":
            clicks = draw_settings()
            if clicks["easy"]:
                difficulty = "easy"
                speed_increase_rate = 1
            elif clicks["normal"]:
                difficulty = "normal"
                speed_increase_rate = 2
            elif clicks["hard"]:
                difficulty = "hard"
                speed_increase_rate = 3
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
