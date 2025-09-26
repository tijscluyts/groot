
import sys
import os
import pygame
import random
import colorsys
import sqlite3

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

pygame.init()

# ---------------- Screen Setup ----------------
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shadow Chase")
clock = pygame.time.Clock()

# ---------------- Colors ----------------
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)  # Platforms
BLACK = (0, 0, 0)

 # ---------------- Background ----------------
background_img = pygame.image.load(resource_path("assets/background.png")).convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

# ---------------- Platform Texture ----------------
platform_texture = pygame.image.load(resource_path("assets/platform.png")).convert_alpha()

# ---------------- Fonts ----------------
title_font = pygame.font.SysFont("chiller", 96)
menu_font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 28)

 # ---------------- Character Sprites ----------------
player_width, player_height = 60, 90
run_frames = [pygame.image.load(resource_path(f"assets/character/block_0_{i}.png")).convert_alpha() for i in range(6)]
jump_up = pygame.image.load(resource_path("assets/character/block_1_0.png")).convert_alpha()
jump_down = pygame.image.load(resource_path("assets/character/block_1_1.png")).convert_alpha()

run_frames = [pygame.transform.scale(f, (player_width, player_height)) for f in run_frames]
jump_up = pygame.transform.scale(jump_up, (player_width, player_height))
jump_down = pygame.transform.scale(jump_down, (player_width, player_height))

# ---------------- Player Setup ----------------
player_rect = pygame.Rect(150, HEIGHT - 150, player_width, player_height)
player_vel_y = 0
jump_velocity = -20
gravity = 1
player_speed = 7
on_ground = False

frame_index = 0
frame_timer = 0
current_sprite = run_frames[0]
facing_right = True

# ---------------- Game States ----------------
START, PLAYING, GAME_OVER = 0, 1, 2
game_state = START
game_over_sound_played = False

# ---------------- Player Trail + Clones ----------------
player_trail = []
clones = []
player_moved = False
player_move_time = None
last_threshold = 0

# ---------------- Score ----------------
score = 0

# ---------------- Stages ----------------
stages = [
    {  # Stage 1
        "platforms": [
            pygame.Rect(0, HEIGHT-50, WIDTH, 60),        # floor
            pygame.Rect(150, HEIGHT-220, 240, 30),
            pygame.Rect(475, HEIGHT-380, 240, 30),
            pygame.Rect(800, HEIGHT-220, 240, 30),
        ],
    },
    {  # Stage 2
        "platforms": [
            pygame.Rect(0, HEIGHT-50, WIDTH, 60),        # floor
            pygame.Rect(300, HEIGHT-220, 240, 30),
            pygame.Rect(650, HEIGHT-380, 240, 30),
        ],
    },
    {  # Stage 3
        "platforms": [
            pygame.Rect(0, HEIGHT-50, WIDTH, 60),        # floor
            pygame.Rect(150, HEIGHT-220, 240, 30),
            pygame.Rect(475, HEIGHT-380, 240, 30),
            pygame.Rect(800, HEIGHT-300, 240, 30),
        ],
    },
    {  # Stage 4
        "platforms": [
            pygame.Rect(0, HEIGHT-50, WIDTH, 60),        # floor
            pygame.Rect(150, HEIGHT-300, 240, 30),
            pygame.Rect(475, HEIGHT-220, 240, 30),
            pygame.Rect(800, HEIGHT-380, 240, 30),
        ],
    }
]

# ---------------- Generate coins 40px above elevated platforms ----------------
for stage in stages:
    stage["collectibles"] = []
    for plat in stage["platforms"]:
        # skip floor for coins
        if plat.y == HEIGHT - 50:
            continue
        coin_rect = pygame.Rect(
            plat.centerx - 15,   # center coin horizontally
            plat.y - 60,         # 60px above platform
            30, 30
        )
        stage["collectibles"].append(coin_rect)

# --- Highscore: setup SQLite ---
conn = sqlite3.connect("highscore.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS highscore (id INTEGER PRIMARY KEY, value INTEGER)")
c.execute("INSERT OR IGNORE INTO highscore (id, value) VALUES (1, 0)")
conn.commit()


def get_highscore():
    c.execute("SELECT value FROM highscore WHERE id=1")
    return c.fetchone()[0]


def set_highscore(new_score):
    c.execute("UPDATE highscore SET value=? WHERE id=1", (new_score,))
    conn.commit()


def copy_stage(stage):
    return [plat.copy() for plat in stage["platforms"]], [coin.copy() for coin in stage["collectibles"]]


# --- Initial Stage and Collectibles Setup ---
stage_index = random.randint(0, len(stages) - 1)
last_stage_index = stage_index
platforms, plat_collectibles = copy_stage(stages[stage_index])
collectibles = []
for coin in plat_collectibles:
    coin_type = "blue" if random.random() < 0.05 else "normal"
    collectibles.append({"rect": coin.copy(), "type": coin_type, "spawn_time": pygame.time.get_ticks()})

 # ---------------- Coin Animation ----------------
coin_frames = [pygame.image.load(resource_path(f"assets/coin/coin_{i}.png")).convert_alpha() for i in range(5)]
coin_size = 30
coin_frames = [pygame.transform.scale(f, (coin_size, coin_size)) for f in coin_frames]
coin_frame_index = 0
coin_frame_timer = 0
coin_frame_speed = 5

# ---------------- Blue Coin / Invincibility ----------------
invincible = False
invincible_timer = 0
invincible_duration = 5000  # 5 seconds


# ---------------- Screens ----------------
def draw_start_screen():
    screen.fill((10, 10, 10))
    title_text = title_font.render("Shadow Chase", True, (200, 0, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3))
    if pygame.time.get_ticks() // 500 % 2 == 0:
        press_text = menu_font.render("Press SPACE to Begin", True, (180, 180, 180))
        screen.blit(press_text, (WIDTH // 2 - press_text.get_width() // 2, HEIGHT // 2))


def draw_game_over_screen():
    screen.fill((0, 0, 0))
    over_text = title_font.render("Game Over", True, (255, 0, 0))
    screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 3))
    score_text = menu_font.render(f"Score: {score}", True, (200, 200, 200))
    highscore = get_highscore()
    highscore_text = menu_font.render(f"Highscore: {highscore}", True, (255, 255, 0))
    screen.blit(highscore_text, (WIDTH // 2 - highscore_text.get_width() // 2, HEIGHT // 2 + 120))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    restart_text = menu_font.render("Press SPACE to Restart", True, (180, 180, 180))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))


 # ---------------- Music ----------------
try:
    pygame.mixer.music.load(resource_path("assets/music/music.mp3"))
    pygame.mixer.music.play(-1)
except Exception:
    pass

# ---------------- Main Loop ----------------
running = True
while running:
    dt = clock.tick(60)
    keys = pygame.key.get_pressed()

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ---------------- START STATE ----------------
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
            stage_index = random.randint(0, len(stages) - 1)
            last_stage_index = stage_index
            platforms, plat_collectibles = copy_stage(stages[stage_index])
            collectibles = []
            for coin in plat_collectibles:
                coin_type = "blue" if random.random() < 0.05 else "normal"
                collectibles.append({"rect": coin.copy(), "type": coin_type, "spawn_time": pygame.time.get_ticks()})
            game_over_sound_played = False
            invincible = False

    # ---------------- PLAYING STATE ----------------
    elif game_state == PLAYING:
        screen.blit(background_img, (0, 0))

        # --- Player movement input ---
        moved_this_frame = False
        if keys[pygame.K_LEFT]:
            player_rect.x -= player_speed
            facing_right = False
            moved_this_frame = True
        if keys[pygame.K_RIGHT]:
            player_rect.x += player_speed
            facing_right = True
            moved_this_frame = True

        # --- Wrap around screen edges ---
        if player_rect.right < 0:
            player_rect.left = WIDTH
        elif player_rect.left > WIDTH:
            player_rect.right = 0

        if keys[pygame.K_SPACE] and on_ground:
            try:
                pygame.mixer.Sound(resource_path("assets/music/jump.mp3")).play().set_volume(0.1)
            except Exception:
                pass
            player_vel_y = jump_velocity
            on_ground = False
            moved_this_frame = True

        if moved_this_frame:
            player_moved = True
            if player_move_time is None:
                player_move_time = pygame.time.get_ticks()

        # --- Physics ---
        player_vel_y += gravity
        player_rect.y += player_vel_y

        # --- Platform collision ---
        on_ground = False
        for plat in platforms:
            if player_rect.colliderect(plat) and player_vel_y >= 0:
                if plat.top < HEIGHT - 60:
                    if not keys[pygame.K_DOWN]:
                        player_rect.bottom = plat.top
                        player_vel_y = 0
                        on_ground = True
                else:
                    player_rect.bottom = plat.top
                    player_vel_y = 0
                    on_ground = True

        # --- Trail recording ---
        if player_moved:
            player_trail.append((player_rect.x, player_rect.y))

        # --- Clone spawning ---
        if player_moved and len(clones) == 0 and pygame.time.get_ticks() - player_move_time >= 1500:
            delay_frames = int(1.5 * 60)
            clone_trail = player_trail[-delay_frames:] if len(player_trail) >= delay_frames else player_trail.copy()
            if clone_trail:
                init_x, init_y = clone_trail[0]
            else:
                init_x, init_y = player_rect.x, player_rect.y
            if len(clone_trail) >= 2:
                fx = clone_trail[-1][0] - clone_trail[0][0]
                initial_facing = True if fx >= 0 else False
            else:
                initial_facing = facing_right
            clones.append({
                "rect": pygame.Rect(init_x, init_y, player_width, player_height),
                "trail": clone_trail.copy(),
                "delay": delay_frames,
                "facing_right": initial_facing,
                "frame_index": 0,
                "frame_timer": 0,
                "prev_x": init_x,
                "prev_y": init_y,
                "last_dy": 0
            })

        if score // 10 > last_threshold and len(clones) > 0:
            last_threshold = score // 10
            delay_frames = int(1.5 * 60 * (len(clones) + 1))
            clone_trail = player_trail[-delay_frames:] if len(player_trail) >= delay_frames else player_trail.copy()
            if clone_trail:
                init_x, init_y = clone_trail[0]
            else:
                init_x, init_y = player_rect.x, player_rect.y
            if len(clone_trail) >= 2:
                fx = clone_trail[-1][0] - clone_trail[0][0]
                initial_facing = True if fx >= 0 else False
            else:
                initial_facing = facing_right
            clones.append({
                "rect": pygame.Rect(init_x, init_y, player_width, player_height),
                "trail": clone_trail.copy(),
                "delay": delay_frames,
                "facing_right": initial_facing,
                "frame_index": 0,
                "frame_timer": 0,
                "prev_x": init_x,
                "prev_y": init_y,
                "last_dy": 0
            })

        # --- Update clones ---
        for clone in clones:
            clone["trail"].append((player_rect.x, player_rect.y))
            if len(clone["trail"]) > clone["delay"]:
                bx, by = clone["trail"].pop(0)
                prev_x = clone.get("prev_x", clone["rect"].x)
                prev_y = clone.get("prev_y", clone["rect"].y)
                dx = bx - prev_x
                dy = by - prev_y
                clone["rect"].x = bx
                clone["rect"].y = by
                if dx > 0:
                    clone["facing_right"] = True
                elif dx < 0:
                    clone["facing_right"] = False
                clone["prev_x"] = bx
                clone["prev_y"] = by
                clone["last_dy"] = dy
            if player_rect.colliderect(clone["rect"]) and not invincible:
                game_state = GAME_OVER

        # --- Update coin animation ---
        coin_frame_timer += 1
        if coin_frame_timer >= coin_frame_speed:
            coin_frame_timer = 0
            coin_frame_index = (coin_frame_index + 1) % len(coin_frames)

        # --- Collectibles collision ---
        for coin in collectibles[:]:
            if player_rect.colliderect(coin["rect"]):
                try:
                    pygame.mixer.Sound(resource_path("assets/music/coin.mp3")).play().set_volume(0.4)
                except Exception:
                    pass
                if coin["type"] == "blue":
                    invincible = True
                    invincible_timer = pygame.time.get_ticks()
                else:
                    score += 1
                collectibles.remove(coin)

        # --- Update invincibility ---
        if invincible:
            if pygame.time.get_ticks() - invincible_timer >= invincible_duration:
                invincible = False

        # --- Stage transition ---
        if not collectibles:
            try:
                pygame.mixer.Sound(resource_path("assets/music/level.mp3")).play().set_volume(0.2)
            except Exception:
                pass
            available = [i for i in range(len(stages)) if i != last_stage_index]
            stage_index = random.choice(available)
            last_stage_index = stage_index
            platforms, plat_collectibles = copy_stage(stages[stage_index])
            collectibles = []
            for coin in plat_collectibles:
                coin_type = "blue" if random.random() < 0.08 else "normal"
                collectibles.append({"rect": coin.copy(), "type": coin_type, "spawn_time": pygame.time.get_ticks()})

        # --- Draw platforms with texture ---
        for plat in platforms[1:]:
            tex_w, tex_h = platform_texture.get_size()
            for x in range(plat.x, plat.x + plat.width, tex_w):
                for y in range(plat.y, plat.y + plat.height, tex_h):
                    screen.blit(platform_texture, (x, y))

        # --- Draw collectibles ---
        for coin in collectibles:
            if coin["type"] == "blue":  # special coin
                # Calculate a cycling hue based on time
                t = pygame.time.get_ticks() / 500  # speed of color cycle
                hue = (t % 1.0)  # hue goes from 0.0 to 1.0
                r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1, 1)]

                # Apply color overlay
                colored_coin = coin_frames[coin_frame_index].copy()
                colored_coin.fill((r, g, b, 255), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(colored_coin, (coin["rect"].x, coin["rect"].y))
            else:
                # normal coin
                screen.blit(coin_frames[coin_frame_index], (coin["rect"].x, coin["rect"].y))

        # --- Draw player ---
        if not on_ground:
            current_sprite = jump_up if player_vel_y < 0 else jump_down
        else:
            frame_timer += 1
            if frame_timer >= 5:
                frame_timer = 0
                frame_index = (frame_index + 1) % len(run_frames)
            current_sprite = run_frames[frame_index]

        sprite_to_draw = current_sprite if facing_right else pygame.transform.flip(current_sprite, True, False)

        # Apply invincibility color cycling
        if invincible:
            t = pygame.time.get_ticks() / 500  # speed of color cycling
            hue = (t % 1.0)
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1, 1)]
            tinted_sprite = sprite_to_draw.copy()
            tinted_sprite.fill((r, g, b, 255), special_flags=pygame.BLEND_RGBA_MULT)
            sprite_to_draw = tinted_sprite

        screen.blit(sprite_to_draw, (player_rect.x, player_rect.y))

        # --- Draw clones ---
        for clone in clones:
            clone_on_ground = False
            for plat in platforms:
                if clone["rect"].colliderect(plat) and abs(clone["rect"].bottom - plat.top) <= 6:
                    clone_on_ground = True
                    break
            last_dy = clone.get("last_dy", 0)
            if not clone_on_ground:
                clone_sprite = jump_up if last_dy < 0 else jump_down
            else:
                clone["frame_timer"] += 1
                if clone["frame_timer"] >= 5:
                    clone["frame_timer"] = 0
                    clone["frame_index"] = (clone["frame_index"] + 1) % len(run_frames)
                clone_sprite = run_frames[clone["frame_index"]]
            sprite_to_draw_clone = clone_sprite if clone["facing_right"] else pygame.transform.flip(clone_sprite, True,
                                                                                                    False)
            shadow = sprite_to_draw_clone.copy()
            shadow.fill((150, 150, 150, 140), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(shadow, (clone["rect"].x, clone["rect"].y))

        # --- HUD ---
        screen.blit(small_font.render(f"Score: {score}", True, BLACK), (10, 10))
        screen.blit(small_font.render(f"Clones: {len(clones)}", True, BLACK), (10, 40))
        if invincible:
            screen.blit(small_font.render("INVINCIBLE!", True, (0, 0, 255)), (10, 70))

    # ---------------- GAME OVER ----------------
    elif game_state == GAME_OVER:
        if not game_over_sound_played:
            # --- Highscore Check ---
            old_highscore = get_highscore()
            if score > old_highscore:
                set_highscore(score)
            try:
                pygame.mixer.Sound(resource_path("assets/music/game-over.mp3")).play().set_volume(0.5)
            except Exception:
                pass
            game_over_sound_played = True

        draw_game_over_screen()
        if keys[pygame.K_SPACE]:
            player_rect = pygame.Rect(150, HEIGHT - 150, player_width, player_height)
            player_vel_y = 0
            on_ground = False
            score = 0
            last_threshold = 0
            player_moved = False
            player_move_time = None
            player_trail = []
            clones = []
            stage_index = random.randint(0, len(stages) - 1)
            last_stage_index = stage_index
            platforms, plat_collectibles = copy_stage(stages[stage_index])
            collectibles = []
            for coin in plat_collectibles:
                coin_type = "blue" if random.random() < 0.05 else "normal"
                collectibles.append({"rect": coin.copy(), "type": coin_type, "spawn_time": pygame.time.get_ticks()})
            game_state = PLAYING
            game_over_sound_played = False
            invincible = False

    pygame.display.flip()

conn.close()
pygame.quit()

# Add main guard for PyInstaller compatibility
if __name__ == "__main__":
    pass  # The script already runs as main, but this guard is needed for PyInstaller
