import pygame
import random

pygame.init()

# Screen setup
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shadow Chase")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)  # Collectibles
GRAY = (100, 100, 100)  # Platforms
BLACK = (0, 0, 0)

# Background
background_img = pygame.image.load("assets/background.png").convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

# Fonts
title_font = pygame.font.SysFont("chiller", 96)
menu_font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 28)

# Load character sprites
player_width, player_height = 60, 90
run_frames = [pygame.image.load(f"assets/character/block_0_{i}.png").convert_alpha() for i in range(6)]
jump_up = pygame.image.load("assets/character/block_1_0.png").convert_alpha()
jump_down = pygame.image.load("assets/character/block_1_1.png").convert_alpha()

run_frames = [pygame.transform.scale(f, (player_width, player_height)) for f in run_frames]
jump_up = pygame.transform.scale(jump_up, (player_width, player_height))
jump_down = pygame.transform.scale(jump_down, (player_width, player_height))

# Player setup
player_rect = pygame.Rect(150, HEIGHT - 150, player_width, player_height)
player_vel_y = 0
jump_velocity = -20
gravity = 1
player_speed = 7
on_ground = False

# Animation
frame_index = 0
frame_timer = 0
current_sprite = run_frames[0]
facing_right = True

# Game states
START, PLAYING, GAME_OVER = 0, 1, 2
game_state = START
game_over_sound_played = False  # Tracks if game over sound has played

# Player trail + clones
player_trail = []
clones = []
player_moved = False
player_move_time = None
last_threshold = 0

# Score
score = 0

# ---------------- Stages ----------------
stages = [
    {"platforms":[pygame.Rect(0, HEIGHT-60, WIDTH, 60),
                  pygame.Rect(225, HEIGHT-270, 180, 30),
                  pygame.Rect(525, HEIGHT-375, 270, 30),
                  pygame.Rect(900, HEIGHT-300, 225, 30)],
     "collectibles":[pygame.Rect(240, HEIGHT-315, 30, 30),
                     pygame.Rect(570, HEIGHT-420, 30, 30),
                     pygame.Rect(930, HEIGHT-345, 30, 30)]},
    {"platforms":[pygame.Rect(0, HEIGHT-60, WIDTH, 60),
                  pygame.Rect(300, HEIGHT-225, 225, 30),
                  pygame.Rect(750, HEIGHT-450, 300, 30)],
     "collectibles":[pygame.Rect(330, HEIGHT-270, 30, 30),
                     pygame.Rect(780, HEIGHT-495, 30, 30),
                     pygame.Rect(975, HEIGHT-105, 30, 30)]},
    {"platforms":[pygame.Rect(0, HEIGHT-60, WIDTH, 60),
                  pygame.Rect(150, HEIGHT-330, 270, 30),
                  pygame.Rect(525, HEIGHT-225, 225, 30),
                  pygame.Rect(900, HEIGHT-420, 300, 30)],
     "collectibles":[pygame.Rect(180, HEIGHT-375, 30, 30),
                     pygame.Rect(555, HEIGHT-255, 30, 30),
                     pygame.Rect(930, HEIGHT-465, 30, 30)]},
    {"platforms":[pygame.Rect(0, HEIGHT-60, WIDTH, 60),
                  pygame.Rect(375, HEIGHT-300, 225, 30),
                  pygame.Rect(675, HEIGHT-375, 150, 30),
                  pygame.Rect(1050, HEIGHT-225, 300, 30)],
     "collectibles":[pygame.Rect(405, HEIGHT-345, 30, 30),
                     pygame.Rect(705, HEIGHT-420, 30, 30),
                     pygame.Rect(1080, HEIGHT-270, 30, 30)]},
]

def copy_stage(stage):
    return [plat.copy() for plat in stage["platforms"]], [c.copy() for c in stage["collectibles"]]

# Start with random stage
stage_index = random.randint(0, len(stages)-1)
last_stage_index = stage_index
platforms, collectibles = copy_stage(stages[stage_index])

# ---------------- Start & Game Over Screens ----------------
def draw_start_screen():
    screen.fill((10, 10, 10))
    title_text = title_font.render("Shadow Chase", True, (200, 0, 0))
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//3))
    if pygame.time.get_ticks() // 500 % 2 == 0:
        press_text = menu_font.render("Press SPACE to Begin", True, (180, 180, 180))
        screen.blit(press_text, (WIDTH//2 - press_text.get_width()//2, HEIGHT//2))

def draw_game_over_screen():
    screen.fill((0, 0, 0))
    over_text = title_font.render("Game Over", True, (255, 0, 0))
    screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//3))
    score_text = menu_font.render(f"Score: {score}", True, (200, 200, 200))
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    restart_text = menu_font.render("Press SPACE to Restart", True, (180, 180, 180))
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))

# ---------------- Music ----------------
pygame.mixer.music.load("assets/music/music.mp3")
pygame.mixer.music.play(-1)

# ---------------- Main Loop ----------------
running = True
while running:
    dt = clock.tick(60)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if game_state == START:
        draw_start_screen()
        if keys[pygame.K_SPACE]:
            game_state = PLAYING
            score = 0
            last_threshold = 0
            player_trail = []
            clones = []
            player_moved = False
            player_move_time = None
            stage_index = random.randint(0, len(stages)-1)
            last_stage_index = stage_index
            platforms, collectibles = copy_stage(stages[stage_index])
            game_over_sound_played = False  # Reset

    elif game_state == PLAYING:
        # Background
        screen.blit(background_img, (0,0))

        # Movement
        moved_this_frame = False
        if keys[pygame.K_LEFT]:
            player_rect.x -= player_speed
            facing_right = False
            moved_this_frame = True
        if keys[pygame.K_RIGHT]:
            player_rect.x += player_speed
            facing_right = True
            moved_this_frame = True
            if player_rect.x + player_width > WIDTH:
                player_rect.x = WIDTH - player_width
        if keys[pygame.K_SPACE] and on_ground:
            pygame.mixer.Sound("assets/music/jump.mp3").play().set_volume(0.1)
            player_vel_y = jump_velocity
            on_ground = False
            moved_this_frame = True
        if moved_this_frame:
            player_moved = True
            if player_move_time is None:
                player_move_time = pygame.time.get_ticks()

        # Gravity
        player_vel_y += gravity
        player_rect.y += player_vel_y

        # Platform collisions with fall-through
        on_ground = False
        for plat in platforms:
            if player_rect.colliderect(plat) and player_vel_y >= 0:
                if plat.top < HEIGHT - 60:  # Non-floor platforms
                    if not keys[pygame.K_DOWN]:
                        player_rect.bottom = plat.top
                        player_vel_y = 0
                        on_ground = True
                else:  # Floor
                    player_rect.bottom = plat.top
                    player_vel_y = 0
                    on_ground = True

        # Trail
        if player_moved:
            player_trail.append((player_rect.x, player_rect.y))

        # Clone spawning logic
        if player_moved and len(clones) == 0 and pygame.time.get_ticks() - player_move_time >= 1500:
            delay_frames = int(1.5*60)
            clone_trail = player_trail[-delay_frames:] if len(player_trail)>=delay_frames else player_trail.copy()
            clones.append({"rect": pygame.Rect(player_rect.x, player_rect.y, player_width, player_height),
                           "trail": clone_trail, "delay": delay_frames,
                           "facing_right": facing_right})
        if score // 10 > last_threshold and len(clones) > 0:
            last_threshold = score // 10
            delay_frames = int(1.5*60*(len(clones)+1))
            clone_trail = player_trail[-delay_frames:] if len(player_trail)>=delay_frames else player_trail.copy()
            clones.append({"rect": pygame.Rect(player_rect.x, player_rect.y, player_width, player_height),
                           "trail": clone_trail, "delay": delay_frames,
                           "facing_right": facing_right})

        # Update clones
        for clone in clones:
            clone["trail"].append((player_rect.x, player_rect.y))
            if len(clone["trail"]) > clone["delay"]:
                bx, by = clone["trail"].pop(0)
                clone["rect"].x = bx
                clone["rect"].y = by
            if player_rect.colliderect(clone["rect"]):
                game_state = GAME_OVER

        # Collectibles
        for c in collectibles[:]:
            if player_rect.colliderect(c):
                pygame.mixer.Sound("assets/music/coin.mp3").play().set_volume(0.4)
                score += 1
                collectibles.remove(c)

        # Stage transition
        if not collectibles:
            pygame.mixer.Sound("assets/music/level.mp3").play().set_volume(0.2)
            available = [i for i in range(len(stages)) if i != last_stage_index]
            stage_index = random.choice(available)
            last_stage_index = stage_index
            platforms, collectibles = copy_stage(stages[stage_index])

        # Draw world
        for plat in platforms:
            pygame.draw.rect(screen, GRAY, plat)
        for c in collectibles:
            pygame.draw.rect(screen, YELLOW, c)

        # Draw player sprite
        if not on_ground:
            current_sprite = jump_up if player_vel_y<0 else jump_down
        else:
            frame_timer +=1
            if frame_timer >=5:
                frame_timer =0
                frame_index = (frame_index+1)%len(run_frames)
            current_sprite = run_frames[frame_index]
        sprite_to_draw = current_sprite if facing_right else pygame.transform.flip(current_sprite, True, False)
        screen.blit(sprite_to_draw, (player_rect.x, player_rect.y))

        # Draw clones
        for clone in clones:
            clone_sprite = run_frames[0] if on_ground else (jump_up if player_vel_y<0 else jump_down)
            clone_sprite = clone_sprite if clone["facing_right"] else pygame.transform.flip(clone_sprite, True, False)
            screen.blit(clone_sprite, (clone["rect"].x, clone["rect"].y))

        # HUD
        screen.blit(small_font.render(f"Score: {score}", True, BLACK), (10, 10))
        screen.blit(small_font.render(f"Clones: {len(clones)}", True, BLACK), (10, 40))

    elif game_state == GAME_OVER:
        # Play game over sound once
        if not game_over_sound_played:
            pygame.mixer.Sound("assets/music/game-over.mp3").play().set_volume(0.5)
            game_over_sound_played = True

        draw_game_over_screen()
        if keys[pygame.K_SPACE]:
            # Reset game
            player_rect = pygame.Rect(150, HEIGHT - 150, player_width, player_height)
            player_vel_y = 0
            on_ground = False
            score = 0
            last_threshold = 0
            player_moved = False
            player_move_time = None
            player_trail = []
            clones = []
            stage_index = random.randint(0, len(stages)-1)
            last_stage_index = stage_index
            platforms, collectibles = copy_stage(stages[stage_index])
            game_state = PLAYING
            game_over_sound_played = False  # Reset flag

    pygame.display.flip()

pygame.quit()
