import pygame
import random
import sys
import os
import json

# Initialize with error handling
try:
    pygame.init()
except Exception as e:
    print(f"Pygame init failed: {e}")
    input("Press Enter to exit...")
    sys.exit()

WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vertical Descent")
clock = pygame.time.Clock()

# Colors
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BG = (20, 20, 20)

# Fonts
font = pygame.font.SysFont(None, 36)

# Player / game globals
player_size = 30
player_x = WIDTH // 2
player_y = 50
player_speed = 5
gravity = 0.5
velocity_y = 0
platform_height = 20
gap_width = 100
platforms = []
platform_speed = 1
spawn_timer = 0
score = 0

# High score file
SCORE_FILE = "highscores.json"

def load_scores():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass
    return []

def save_score(name, score):
    scores = load_scores()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:5]
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f)

def draw_highscores():
    scores = load_scores()
    y_offset = 100
    title = font.render("HIGH SCORES", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, y_offset))
    y_offset += 40
    if not scores:
        txt = font.render("No scores yet", True, WHITE)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y_offset))
        return
    for entry in scores:
        line = f"{entry['name']} - {entry['score']}"
        text = font.render(line, True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y_offset))
        y_offset += 30

def spawn_platform():
    gap_x = random.randint(0, WIDTH - gap_width)
    platforms.append({'y': HEIGHT, 'gap_x': gap_x, 'scored': False})

def reset_game():
    global player_x, player_y, velocity_y, platforms, platform_speed, spawn_timer, score
    player_x = WIDTH // 2
    player_y = 50
    velocity_y = 0
    platforms = []
    platform_speed = 1
    spawn_timer = 0
    score = 0

def main_game():
    global player_x, player_y, velocity_y, platforms, platform_speed, spawn_timer, score
    reset_game()
    running = True
    game_over = False

    while running:
        clock.tick(60)
        screen.fill(BG)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                game_over = False

        # Input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            player_x -= player_speed
        if keys[pygame.K_d]:
            player_x += player_speed
        if keys[pygame.K_w]:
            velocity_y = -5
        if keys[pygame.K_s]:
            player_y += player_speed

        # Gravity
        velocity_y += gravity
        player_y += velocity_y

        # Boundaries
        if player_x < 0:
            player_x = 0
        if player_x > WIDTH - player_size:
            player_x = WIDTH - player_size
        if player_y > HEIGHT:
            game_over = True
            running = False
        if player_y < 0:
            game_over = True
            running = False

        # Spawn platforms
        spawn_timer += 1
        if spawn_timer > 60:
            spawn_platform()
            spawn_timer = 0
            platform_speed += 0.05

        # Move and clean up platforms
        for plat in platforms[:]:
            plat['y'] -= platform_speed
            if plat['y'] > HEIGHT:
                platforms.remove(plat)
                continue
            pygame.draw.rect(screen, WHITE, (0, plat['y'], plat['gap_x'], platform_height))
            pygame.draw.rect(screen, WHITE, (plat['gap_x'] + gap_width, plat['y'], WIDTH - plat['gap_x'] - gap_width, platform_height))

        # Collision
        for plat in platforms:
            if (plat['y'] < player_y + player_size and plat['y'] + platform_height > player_y and
                not (plat['gap_x'] < player_x + player_size and plat['gap_x'] + gap_width > player_x)):
                player_y = plat['y'] - player_size
                velocity_y = 0

        # Scoring
        for plat in platforms:
            if plat['y'] + platform_height < player_y and not plat['scored']:
                score += 1
                plat['scored'] = True

        # Draw player
        pygame.draw.rect(screen, RED, (player_x, player_y, player_size, player_size))

        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()

    return game_over, score

def game_over_and_scores(final_score):
    global score
    score = final_score

    # Enter name
    name = ""
    entering = True
    while entering:
        screen.fill(BG)
        prompt = font.render("Game Over! Enter name:", True, WHITE)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 150))
        name_text = font.render(name + "_", True, WHITE)
        screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, 200))
        info = font.render("ENTER=save ESC=skip", True, WHITE)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 250))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    entering = False
                elif event.key == pygame.K_RETURN:
                    if name.strip():
                        save_score(name, score)
                    else:
                        save_score("PLAYER", score)
                    entering = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 10 and event.unicode.isprintable():
                        name += event.unicode

    # Highscores + play again
    while True:
        screen.fill(BG)
        draw_highscores()
        info1 = font.render("ENTER = play again", True, WHITE)
        info2 = font.render("ESC = quit", True, WHITE)
        screen.blit(info1, (WIDTH // 2 - info1.get_width() // 2, HEIGHT - 90))
        screen.blit(info2, (WIDTH // 2 - info2.get_width() // 2, HEIGHT - 60))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_RETURN:
                    return True

def main():
    print("Vertical Descent starting... Close window or ESC to quit.")
    while True:
        game_over, final_score = main_game()
        if not game_over:
            break
        play_again = game_over_and_scores(final_score)
        if not play_again:
            break
    print("Thanks for playing!")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
