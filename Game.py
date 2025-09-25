import pygame
import random

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Treadmill Runner")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)      # Bad food
GREEN = (0, 255, 0)    # Good food
BLUE = (0, 0, 255)     # Player
GRAY = (100, 100, 100) # Treadmill

# Treadmill setup
treadmill_y = HEIGHT - 100
treadmill_height = 20

# Player setup
player_width, player_height = 50, 50
start_x = WIDTH // 4
player_x = start_x
player_y = treadmill_y - player_height
player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
player_jump = False
jump_velocity = -15
gravity = 1
player_vel_y = 0

# Drift settings
drift_speed = 0.0       # starts at 0
drift_increment = 0.1   # amount added/subtracted per food

# Food setup
food_width, food_height = 30, 30
foods = []
food_spawn_chance = 3  # % chance per frame

# Score
score = 0
game_over = False

# Main loop
while not game_over:
    screen.fill(WHITE)
    dt = clock.tick(60)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not player_jump:
                player_jump = True
                player_vel_y = jump_velocity

    # Player jump physics
    if player_jump:
        player_rect.y += player_vel_y
        player_vel_y += gravity
        if player_rect.y >= treadmill_y - player_height:
            player_rect.y = treadmill_y - player_height
            player_jump = False
            player_vel_y = 0

    # Apply drift (left movement)
    player_rect.x -= drift_speed
    # Prevent player from moving off the right
    if player_rect.x + player_width > WIDTH:
        player_rect.x = WIDTH - player_width

    # Spawn food from right side
    if random.randint(0, 100) < food_spawn_chance:
        food_x = WIDTH
        food_y = treadmill_y - food_height
        food_type = random.choice(["red", "green"])
        food_rect = pygame.Rect(food_x, food_y, food_width, food_height)
        foods.append((food_rect, food_type))

    # Move foods left (treadmill motion)
    for food in foods[:]:
        rect, f_type = food
        rect.x -= 5  # treadmill speed

        # Collision with player
        if player_rect.colliderect(rect):
            score += 1
            if f_type == "red":
                drift_speed += drift_increment
            elif f_type == "green":
                drift_speed = max(0, drift_speed - drift_increment)
            foods.remove(food)

        # Remove food if off-screen
        elif rect.x + food_width < 0:
            foods.remove(food)

    # Draw treadmill
    pygame.draw.rect(screen, GRAY, (0, treadmill_y, WIDTH, treadmill_height))
    # Draw player
    pygame.draw.rect(screen, BLUE, player_rect)
    # Draw foods
    for rect, f_type in foods:
        color = RED if f_type == "red" else GREEN
        pygame.draw.rect(screen, color, rect)

    # Check if player falls off left side
    if player_rect.x < 0:
        game_over = True

    # Display score and drift speed
    font = pygame.font.SysFont(None, 36)
    score_surf = font.render(f"Score: {score}", True, (0, 0, 0))
    drift_surf = font.render(f"Drift Speed: {drift_speed:.2f}", True, (0, 0, 0))
    screen.blit(score_surf, (10, 10))
    screen.blit(drift_surf, (10, 50))

    pygame.display.flip()

pygame.quit()
