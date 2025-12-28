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

# Fixed window size (not fullscreen)
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Descent Game")
clock = pygame.time.Clock()

# Colors
RED = (255, 0, 0)
BLACK = (0, 0, 0)  # Changed to black text
WHITE = (255, 255, 255)
BG = (20, 20, 20)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)

# Fonts
title_font = pygame.font.SysFont(None, 72)
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 36)

# Game state
state = "menu"
player_size = 40
player_x = WIDTH // 2 - player_size // 2
player_y = HEIGHT // 4
player_speed = 8
gravity = 0.3
velocity_y = 0
platform_height = 25
gap_width = 150
platforms = []
platform_speed = 2
spawn_timer = 0
score = 0
difficulty = "normal"
game_mode = "easy"

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
    
    text_surf = small_font.render(text, True, BLACK)  # Black text
    screen.blit(text_surf, (x + (w - text_surf.get_width()) // 2, y + (h - text_surf.get_height()) // 2))
    return False

def draw_home_menu():
    screen.fill(BG)
    
    # Logo - big red square
    logo_size = 120
    pygame.draw.rect(screen, RED, (WIDTH//2 - logo_size//2, HEIGHT//4 - logo_size//2, logo_size, logo_size))
    
    # Title - black text
    title = title_font.render("DESCENT", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4 - 120))
    
    # Buttons - more spacing
    btn_w, btn_h = 200, 60
    btn_y = HEIGHT//2
    play_clicked = draw_button("PLAY", WIDTH//2 - btn_w//2, btn_y, btn_w, btn_h)
    leaderboard_clicked = draw_button("LEADERBOARD", WIDTH//2 - btn_w//2, btn_y + 80, btn_w, btn_h)
    settings_clicked = draw_button("SETTINGS", WIDTH//2 - btn_w//2, btn_y + 160, btn_w, btn_h)
    
    return play_clicked, leaderboard_clicked, settings_clicked

def draw_settings():
    screen.fill(BG)
    
    # Title - black text
    title = title_font.render("SETTINGS", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    # Difficulty buttons - centered perfectly
    btn_w, btn_h = 120, 50
    y_start = HEIGHT//3
    easy_x = WIDTH//2 - btn_w*1.5 - 20
    normal_x = WIDTH//2 - btn_w//2
    hard_x = WIDTH//2 + btn_w*0.5 + 20
    
    easy_clicked = draw_button("EASY", easy_x, y_start, btn_w, btn_h, selected=difficulty == "easy")
    normal_clicked = draw_button("NORMAL", normal_x, y_start, btn_w, btn_h, selected=difficulty == "normal")
    hard_clicked = draw_button("HARD", hard_x, y_start, btn_w, btn_h, selected=difficulty == "hard")
    
    # Clear leaderboard buttons - perfectly centered under each
    clear_y = y_start + 80
    clear_easy = draw_button("Clear Easy", easy_x, clear_y, btn_w, 35)
    clear_normal = draw_button("Clear Normal", normal_x, clear_y, btn_w, 35)
    clear_hard = draw_button("Clear Hard", hard_x, clear_y, btn_w, 35)
    
    # Back button
    back_clicked = draw_button("BACK", WIDTH//2 - 100, HEIGHT - 100, 200, 50)
    
    return {
        "easy": easy_clicked, "normal": normal_clicked, "hard": hard_clicked,
        "clear_easy": clear_easy, "clear_normal": clear_normal, "clear_hard": clear_hard,
        "back": back_clicked
    }

def draw_leaderboards():
    screen.fill(BG)
    
    # Title
    title = title_font.render("LEADERBOARDS", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))
    
    # More spacing between modes
    y_offset = 120
    for mode in ["easy", "normal", "hard"]:
        # Mode title
        mode_title = font.render(f"{mode.upper()}:", True, BLACK)
        screen.blit(mode_title, (50, y_offset))
        y_offset += 60  # More space
        
        scores = load_scores(mode)
        if not scores:
            no_scores = small_font.render("No scores yet", True, BLACK)
            screen.blit(no_scores, (80, y_offset))
        else:
            for i, entry in enumerate(scores):
                line = small_font.render(f"{i+1}. {entry['name']} - {entry['score']}", True, BLACK)
                screen.blit(line, (80, y_offset))
                y_offset += 45  # More space between scores
        y_offset += 40  # Extra space between modes

    # Back button
    back_clicked = draw_button("BACK", WIDTH//2 - 100, HEIGHT - 80, 200, 50)
    return back_clicked

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
    global player_x, player_y, velocity_y, platforms, platform_speed, spawn_timer, score
    reset_game()
    running = True
    settings = DIFFICULTY[difficulty]
    
    while running:
        clock.tick(60)
        screen.fill(BG)

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
        controls = small_font.render("A/D or Arrows: Move | W/Up/Space: Jump | ESC: Menu", True, BLACK)
        screen.blit(controls, (20, HEIGHT - 50))

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
                    return True  # Go to leaderboards
                elif event.key == pygame.K_RETURN:
                    if name.strip():
                        save_score(game_mode, name, final_score)
                    else:
                        save_score(game_mode, "PLAYER", final_score)
                    entering = False
                    return True  # Go to leaderboards
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 12 and event.unicode.isprintable():
                        name += event.unicode
    return False

def main():
    global state, difficulty
    
    print("Descent Game - Fixed version!")
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
        
        if state == "menu":
            play_clicked, leaderboard_clicked, settings_clicked = draw_home_menu()
            if play_clicked:
                state = "playing"
            elif leaderboard_clicked:
                state = "leaderboards"
            elif settings_clicked:
                state = "settings"
                
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
                show_leaderboards = name_entry_screen(final_score)
                if show_leaderboards:
                    state = "leaderboards"
                else:
                    state = "menu"
            else:
                state = "menu"
                
        elif state == "leaderboards":
            back_clicked = draw_leaderboards()
            if back_clicked:
                state = "menu"
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()
