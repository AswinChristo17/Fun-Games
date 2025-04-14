import pygame
import sys
import random
import math
import time
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cosmic Snake Adventure")
clock = pygame.time.Clock()

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
SETTINGS = 3

# Settings
class Settings:
    def __init__(self):
        self.difficulty = 1  # 0: Easy, 1: Medium, 2: Hard
        self.theme = 0  # 0: Classic, 1: Neon, 2: Space, 3: Underwater
        self.snake_style = 0  # 0: Classic, 1: Gradient, 2: Patterned, 3: Glowing
        self.special_foods = True
        self.obstacles = True
        self.grid_visible = True
        self.particle_effects = True
        self.background_motion = True
        self.trail_effect = True

    def get_speed(self):
        speeds = [6, 10, 15]
        return speeds[self.difficulty]

    def get_theme_colors(self):
        if self.theme == 0:  # Classic
            return {
                'background': (50, 50, 50),
                'grid': (70, 70, 70),
                'snake_head': (0, 200, 0),
                'snake_body': (0, 255, 0),
                'food': (255, 0, 0),
                'special_food': (255, 215, 0),
                'obstacle': (128, 128, 128),
                'text': (255, 255, 255),
            }
        elif self.theme == 1:  # Neon
            return {
                'background': (10, 10, 30),
                'grid': (30, 30, 50),
                'snake_head': (255, 0, 255),
                'snake_body': (0, 255, 255),
                'food': (255, 255, 0),
                'special_food': (255, 128, 0),
                'obstacle': (150, 0, 255),
                'text': (0, 255, 255),
            }
        elif self.theme == 2:  # Space
            return {
                'background': (5, 5, 20),
                'grid': (15, 15, 40),
                'snake_head': (200, 200, 255),
                'snake_body': (150, 150, 255),
                'food': (255, 100, 100),
                'special_food': (255, 200, 50),
                'obstacle': (100, 50, 150),
                'text': (200, 200, 255),
            }
        else:  # Underwater
            return {
                'background': (0, 50, 100),
                'grid': (0, 70, 120),
                'snake_head': (0, 255, 200),
                'snake_body': (0, 200, 255),
                'food': (255, 50, 50),
                'special_food': (255, 200, 0),
                'obstacle': (50, 100, 150),
                'text': (200, 255, 255),
            }

settings = Settings()

# Function to create a gradient effect
def get_gradient_color(color1, color2, ratio):
    return (
        int(color1[0] * (1 - ratio) + color2[0] * ratio),
        int(color1[1] * (1 - ratio) + color2[1] * ratio),
        int(color1[2] * (1 - ratio) + color2[2] * ratio)
    )

# Particle system
class Particle:
    def __init__(self, x, y, color, velocity=None, size=None, lifespan=None):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity or [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.size = size or random.randint(2, 5)
        self.lifespan = lifespan or random.randint(20, 40)
        self.age = 0

    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.age += 1
        self.size = max(0, self.size - 0.1)
        return self.age < self.lifespan and self.size > 0

    def draw(self, surface):
        alpha = 255 * (1 - self.age / self.lifespan)
        color_with_alpha = (*self.color, int(alpha))
        gfxdraw.filled_circle(surface, int(self.x), int(self.y), int(self.size), color_with_alpha)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_particles(self, x, y, color, count=5):
        if not settings.particle_effects:
            return

        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

# Star background for space theme
class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.uniform(0.1, 3)
        self.speed = random.uniform(0.1, 0.5)
        self.brightness = random.uniform(0.5, 1.0)

    def update(self):
        if settings.background_motion:
            self.y += self.speed
            if self.y > HEIGHT:
                self.y = 0
                self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        alpha = int(255 * self.brightness * (0.7 + 0.3 * math.sin(time.time() * 2)))
        color = (200, 200, 255, alpha)
        gfxdraw.filled_circle(surface, int(self.x), int(self.y), int(self.size), color)

# Bubble background for underwater theme
class Bubble:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.uniform(1, 5)
        self.speed = random.uniform(0.5, 2.0)
        self.wobble_speed = random.uniform(1.0, 3.0)
        self.wobble_amount = random.uniform(0.5, 2.0)
        self.offset = random.uniform(0, 6.28)

    def update(self):
        if settings.background_motion:
            self.y -= self.speed
            self.x += math.sin((time.time() + self.offset) * self.wobble_speed) * self.wobble_amount
            if self.y < 0:
                self.y = HEIGHT
                self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        alpha = int(128 + 127 * math.sin(time.time() + self.offset))
        color = (200, 255, 255, alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size), 1)

# Grid lines for the background
class Grid:
    def __init__(self):
        self.visible = True

    def draw(self, surface, color):
        if not settings.grid_visible:
            return

        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(surface, color, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(surface, color, (0, y), (WIDTH, y), 1)

# Snake class
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
        self.score = 0
        self.grid = [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
        self.last_move_time = time.time()
        self.special_effect = None
        self.special_effect_end = 0
        self.grow_queue = 0
        self.trail = []

    def update(self):
        current = time.time()
        speed_factor = 1.0

        # Apply special effects
        if self.special_effect == 'speed_boost':
            speed_factor = 1.5
        elif self.special_effect == 'slow_motion':
            speed_factor = 0.5

        # End special effect if time is up
        if self.special_effect and current > self.special_effect_end:
            self.special_effect = None

        # Update based on speed
        move_delay = 1.0 / settings.get_speed() / speed_factor
        if current - self.last_move_time >= move_delay:
            self.last_move_time = current

            # Update trail if enabled
            if settings.trail_effect:
                for i in range(len(self.trail)):
                    self.trail[i]['alpha'] -= 5
                self.trail = [t for t in self.trail if t['alpha'] > 0]

                # Add current positions to trail
                for i, pos in enumerate(self.positions):
                    if i % 2 == 0:  # Only add every other position to avoid too many trail particles
                        self.trail.append({
                            'pos': pos,
                            'alpha': 128
                        })

            # Calculate new head position
            head = self.positions[0]
            new_head = ((head[0] + self.direction[0]) % GRID_WIDTH,
                        (head[1] + self.direction[1]) % GRID_HEIGHT)

            # Check if the snake hit itself
            if new_head in self.positions:
                return False

            # Check if the snake hit an obstacle
            if self.grid[new_head[0]][new_head[1]] == 2:  # 2 represents an obstacle
                return False

            # Add the new head to the beginning of positions list
            self.positions.insert(0, new_head)

            # Check if we need to grow the snake
            if self.grow_queue > 0:
                self.grow_queue -= 1
            else:
                # Remove the tail if not growing
                self.positions.pop()

            return True
        return True

    def grow(self, amount=1):
        self.grow_queue += amount

    def check_food_collision(self, food):
        if self.positions[0] == food.position:
            self.score += food.value
            self.grow(food.growth)

            # Apply special effects based on food type
            if food.food_type == 'speed_boost':
                self.special_effect = 'speed_boost'
                self.special_effect_end = time.time() + 5  # 5 seconds boost
            elif food.food_type == 'slow_motion':
                self.special_effect = 'slow_motion'
                self.special_effect_end = time.time() + 5  # 5 seconds slow motion

            return True
        return False

    def change_direction(self, new_direction):
        # Prevent 180 degree turns
        if (self.direction[0] + new_direction[0] != 0 or
            self.direction[1] + new_direction[1] != 0):
            self.direction = new_direction

    def draw(self, surface, theme_colors):
        # Draw trail
        if settings.trail_effect:
            for trail_piece in self.trail:
                x, y = trail_piece['pos']
                alpha = trail_piece['alpha']
                color = (*theme_colors['snake_body'], alpha)

                rect = pygame.Rect(
                    x * GRID_SIZE,
                    y * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                )
                shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(shape_surf, color, shape_surf.get_rect(), border_radius=int(GRID_SIZE/4))
                surface.blit(shape_surf, rect)

        # Draw snake body based on style
        for i, (x, y) in enumerate(self.positions):
            if i == 0:  # Head
                color = theme_colors['snake_head']
                rect = pygame.Rect(
                    x * GRID_SIZE,
                    y * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                )
                pygame.draw.rect(surface, color, rect, border_radius=int(GRID_SIZE/3))

                # Draw eyes
                eye_size = GRID_SIZE // 4
                eye_offset = GRID_SIZE // 4

                # Position eyes based on direction
                if self.direction == (1, 0):  # Right
                    left_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset, y * GRID_SIZE + eye_offset)
                    right_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset, y * GRID_SIZE + GRID_SIZE - eye_offset - eye_size)
                elif self.direction == (-1, 0):  # Left
                    left_eye = (x * GRID_SIZE + eye_offset, y * GRID_SIZE + eye_offset)
                    right_eye = (x * GRID_SIZE + eye_offset, y * GRID_SIZE + GRID_SIZE - eye_offset - eye_size)
                elif self.direction == (0, 1):  # Down
                    left_eye = (x * GRID_SIZE + eye_offset, y * GRID_SIZE + GRID_SIZE - eye_offset - eye_size)
                    right_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset - eye_size, y * GRID_SIZE + GRID_SIZE - eye_offset - eye_size)
                else:  # Up
                    left_eye = (x * GRID_SIZE + eye_offset, y * GRID_SIZE + eye_offset)
                    right_eye = (x * GRID_SIZE + GRID_SIZE - eye_offset - eye_size, y * GRID_SIZE + eye_offset)

                pygame.draw.rect(surface, BLACK, (left_eye[0], left_eye[1], eye_size, eye_size))
                pygame.draw.rect(surface, BLACK, (right_eye[0], right_eye[1], eye_size, eye_size))

            else:  # Body
                if settings.snake_style == 0:  # Classic
                    color = theme_colors['snake_body']
                elif settings.snake_style == 1:  # Gradient
                    ratio = i / max(len(self.positions) - 1, 1)
                    color = get_gradient_color(theme_colors['snake_head'], theme_colors['snake_body'], ratio)
                elif settings.snake_style == 2:  # Patterned
                    color = theme_colors['snake_body'] if i % 2 == 0 else theme_colors['snake_head']
                else:  # Glowing
                    pulse = (math.sin(time.time() * 3 + i * 0.2) + 1) / 2
                    color = get_gradient_color(theme_colors['snake_body'], theme_colors['snake_head'], pulse)

                rect = pygame.Rect(
                    x * GRID_SIZE,
                    y * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                )
                pygame.draw.rect(surface, color, rect, border_radius=int(GRID_SIZE/4))

# Food class
class Food:
    def __init__(self, grid, snake_positions):
        self.grid = grid
        self.reset(snake_positions)

    def reset(self, snake_positions):
        # Select food type
        if settings.special_foods and random.random() < 0.2:  # 20% chance for special food
            self.food_type = random.choice(['normal', 'bonus', 'speed_boost', 'slow_motion'])
        else:
            self.food_type = 'normal'

        # Set properties based on food type
        if self.food_type == 'normal':
            self.value = 1
            self.growth = 1
            self.color = None  # Will use theme color
        elif self.food_type == 'bonus':
            self.value = 5
            self.growth = 2
            self.color = YELLOW
        elif self.food_type == 'speed_boost':
            self.value = 2
            self.growth = 1
            self.color = CYAN
        elif self.food_type == 'slow_motion':
            self.value = 2
            self.growth = 1
            self.color = PURPLE

        # Find an available position
        available_positions = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if (x, y) not in snake_positions and self.grid[x][y] != 2:
                    available_positions.append((x, y))

        if available_positions:
            self.position = random.choice(available_positions)
        else:
            # If no positions available, just pick a random spot (game is likely almost over anyway)
            self.position = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))

    def draw(self, surface, theme_colors):
        x, y = self.position

        if self.food_type == 'normal':
            color = theme_colors['food']
            pygame.draw.circle(surface, color,
                              (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2),
                              GRID_SIZE // 2 - 2)
        elif self.food_type == 'bonus':
            # Star-shaped bonus food
            color = theme_colors['special_food']
            center_x = x * GRID_SIZE + GRID_SIZE // 2
            center_y = y * GRID_SIZE + GRID_SIZE // 2
            radius = GRID_SIZE // 2 - 2
            points = []

            for i in range(10):
                angle = math.pi * 2 * i / 10
                r = radius if i % 2 == 0 else radius // 2
                points.append((
                    center_x + int(math.cos(angle) * r),
                    center_y + int(math.sin(angle) * r)
                ))

            pygame.draw.polygon(surface, color, points)
        elif self.food_type == 'speed_boost':
            # Lightning bolt for speed boost
            color = self.color
            rect = pygame.Rect(x * GRID_SIZE + 2, y * GRID_SIZE + 2, GRID_SIZE - 4, GRID_SIZE - 4)
            pygame.draw.rect(surface, color, rect)

            # Lightning shape inside
            points = [
                (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + 3),
                (x * GRID_SIZE + GRID_SIZE // 3, y * GRID_SIZE + GRID_SIZE // 2),
                (x * GRID_SIZE + GRID_SIZE // 2 + 2, y * GRID_SIZE + GRID_SIZE // 2),
                (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE - 3)
            ]
            pygame.draw.polygon(surface, theme_colors['background'], points)
        elif self.food_type == 'slow_motion':
            # Clock-like shape for slow motion
            color = self.color
            center_x = x * GRID_SIZE + GRID_SIZE // 2
            center_y = y * GRID_SIZE + GRID_SIZE // 2
            radius = GRID_SIZE // 2 - 2

            pygame.draw.circle(surface, color, (center_x, center_y), radius)
            pygame.draw.circle(surface, theme_colors['background'], (center_x, center_y), radius - 3)
            pygame.draw.line(surface, color, (center_x, center_y),
                            (center_x, center_y - radius + 3), 2)
            pygame.draw.line(surface, color, (center_x, center_y),
                            (center_x + radius - 3, center_y), 2)

# Obstacle generator
class ObstacleGenerator:
    def __init__(self, grid, snake_positions):
        self.grid = grid
        self.obstacles = []
        self.generate_obstacles(snake_positions)

    def generate_obstacles(self, snake_positions):
        if not settings.obstacles:
            return

        # Clear previous obstacles
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if self.grid[x][y] == 2:  # 2 represents obstacle
                    self.grid[x][y] = 0

        self.obstacles = []

        # Create a safe zone around the snake's starting position
        safe_zone = []
        for pos in snake_positions:
            safe_zone.append(pos)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = (pos[0] + dx) % GRID_WIDTH, (pos[1] + dy) % GRID_HEIGHT
                    safe_zone.append((nx, ny))

        # Generate random obstacles based on difficulty
        num_obstacles = [3, 5, 8][settings.difficulty]

        for _ in range(num_obstacles):
            self.generate_obstacle_pattern(safe_zone)

    def generate_obstacle_pattern(self, safe_zone):
        pattern_type = random.choice(['line', 'cluster', 'maze_piece'])

        if pattern_type == 'line':
            # Generate a line of obstacles
            length = random.randint(3, 8)
            direction = random.choice([(0, 1), (1, 0)])  # Vertical or horizontal

            # Find starting position not in safe zone
            while True:
                start_x = random.randint(0, GRID_WIDTH - 1)
                start_y = random.randint(0, GRID_HEIGHT - 1)
                if (start_x, start_y) not in safe_zone:
                    break

            for i in range(length):
                x = (start_x + direction[0] * i) % GRID_WIDTH
                y = (start_y + direction[1] * i) % GRID_HEIGHT
                if (x, y) not in safe_zone:
                    self.grid[x][y] = 2
                    self.obstacles.append((x, y))

        elif pattern_type == 'cluster':
            # Generate a cluster of obstacles
            while True:
                center_x = random.randint(0, GRID_WIDTH - 1)
                center_y = random.randint(0, GRID_HEIGHT - 1)
                if (center_x, center_y) not in safe_zone:
                    break

            size = random.randint(3, 5)
            for _ in range(size):
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)
                x = (center_x + dx) % GRID_WIDTH
                y = (center_y + dy) % GRID_HEIGHT
                if (x, y) not in safe_zone:
                    self.grid[x][y] = 2
                    self.obstacles.append((x, y))

        elif pattern_type == 'maze_piece':
            # Generate a maze-like piece
            while True:
                start_x = random.randint(0, GRID_WIDTH - 3)
                start_y = random.randint(0, GRID_HEIGHT - 3)
                valid = True
                for dx in range(3):
                    for dy in range(3):
                        if (start_x + dx, start_y + dy) in safe_zone:
                            valid = False
                            break
                    if not valid:
                        break
                if valid:
                    break

            # Create a small maze piece (C-shape, L-shape, etc.)
            shape_type = random.randint(0, 3)

            if shape_type == 0:  # C-shape
                for dx in [0, 1, 2]:
                    self.grid[(start_x + dx) % GRID_WIDTH][start_y % GRID_HEIGHT] = 2
                    self.obstacles.append(((start_x + dx) % GRID_WIDTH, start_y % GRID_HEIGHT))

                for dy in [1, 2]:
                    self.grid[start_x % GRID_WIDTH][(start_y + dy) % GRID_HEIGHT] = 2
                    self.obstacles.append((start_x % GRID_WIDTH, (start_y + dy) % GRID_HEIGHT))

                for dx in [0, 1, 2]:
                    self.grid[(start_x + dx) % GRID_WIDTH][(start_y + 2) % GRID_HEIGHT] = 2
                    self.obstacles.append(((start_x + dx) % GRID_WIDTH, (start_y + 2) % GRID_HEIGHT))

            elif shape_type == 1:  # L-shape
                for dx in [0, 1, 2]:
                    self.grid[(start_x + dx) % GRID_WIDTH][start_y % GRID_HEIGHT] = 2
                    self.obstacles.append(((start_x + dx) % GRID_WIDTH, start_y % GRID_HEIGHT))

                for dy in [1, 2]:
                    self.grid[start_x % GRID_WIDTH][(start_y + dy) % GRID_HEIGHT] = 2
                    self.obstacles.append((start_x % GRID_WIDTH, (start_y + dy) % GRID_HEIGHT))

            elif shape_type == 2:  # T-shape
                for dx in [0, 1, 2]:
                    self.grid[(start_x + dx) % GRID_WIDTH][start_y % GRID_HEIGHT] = 2
                    self.obstacles.append(((start_x + dx) % GRID_WIDTH, start_y % GRID_HEIGHT))

                for dy in [1, 2]:
                    self.grid[(start_x + 1) % GRID_WIDTH][(start_y + dy) % GRID_HEIGHT] = 2
                    self.obstacles.append(((start_x + 1) % GRID_WIDTH, (start_y + dy) % GRID_HEIGHT))

            else:  # Z-shape
                for dx in [0, 1]:
                    self.grid[(start_x + dx) % GRID_WIDTH][start_y % GRID_HEIGHT] = 2
                    self.obstacles.append(((start_x + dx) % GRID_WIDTH, start_y % GRID_HEIGHT))

                self.grid[(start_x + 1) % GRID_WIDTH][(start_y + 1) % GRID_HEIGHT] = 2
                self.obstacles.append(((start_x + 1) % GRID_WIDTH, (start_y + 1) % GRID_HEIGHT))

                for dx in [1, 2]:
                    self.grid[(start_x + dx) % GRID_WIDTH][(start_y + 2) % GRID_HEIGHT] = 2
                    self.obstacles.append(((start_x + dx) % GRID_WIDTH, (start_y + 2) % GRID_HEIGHT))

    def draw(self, surface, theme_colors):
        for x, y in self.obstacles:
            rect = pygame.Rect(
                x * GRID_SIZE,
                y * GRID_SIZE,
                GRID_SIZE,
                GRID_SIZE
            )

            if settings.theme == 0:  # Classic concrete blocks
                pygame.draw.rect(surface, theme_colors['obstacle'], rect)
                pygame.draw.rect(surface, get_gradient_color(theme_colors['obstacle'], BLACK, 0.3), rect, 1)

                # Add brick pattern
                for i in range(2):
                    line_y = y * GRID_SIZE + (i + 1) * GRID_SIZE // 3
                    pygame.draw.line(surface, get_gradient_color(theme_colors['obstacle'], BLACK, 0.3),
                                    (x * GRID_SIZE, line_y),
                                    ((x + 1) * GRID_SIZE, line_y), 1)

                if x % 2 == 0:
                    line_x = x * GRID_SIZE + GRID_SIZE // 2
                    pygame.draw.line(surface, get_gradient_color(theme_colors['obstacle'], BLACK, 0.3),
                                    (line_x, y * GRID_SIZE),
                                    (line_x, (y + 1) * GRID_SIZE), 1)

            elif settings.theme == 1:  # Neon barriers
                border_width = 2
                pygame.draw.rect(surface, theme_colors['obstacle'], rect)

                inner_rect = pygame.Rect(
                    x * GRID_SIZE + border_width,
                    y * GRID_SIZE + border_width,
                    GRID_SIZE - 2 * border_width,
                    GRID_SIZE - 2 * border_width
                )
                pygame.draw.rect(surface, get_gradient_color(theme_colors['obstacle'], WHITE, 0.2), inner_rect)

                # Add pulsing effect
                glow = abs(math.sin(time.time() * 3)) * 50
                glow_color = get_gradient_color(theme_colors['obstacle'], WHITE, 0.7)
                pygame.draw.rect(surface, glow_color, rect, 1)

            elif settings.theme == 2:  # Space asteroids
                # Draw rocky asteroid
                pygame.draw.rect(surface, theme_colors['obstacle'], rect, border_radius=int(GRID_SIZE/3))

                # Add crater details
                center_x = x * GRID_SIZE + GRID_SIZE // 2
                center_y = y * GRID_SIZE + GRID_SIZE // 2
                pygame.draw.circle(surface, get_gradient_color(theme_colors['obstacle'], BLACK, 0.3),
                                  (center_x - 3, center_y - 3), GRID_SIZE // 6)
                pygame.draw.circle(surface, get_gradient_color(theme_colors['obstacle'], BLACK, 0.3),
                                  (center_x + 4, center_y + 2), GRID_SIZE // 8)

            else:  # Underwater coral
                pygame.draw.rect(surface, theme_colors['obstacle'], rect, border_radius=int(GRID_SIZE/4))

                # Add coral-like details
                for i in range(3):
                    detail_x = x * GRID_SIZE + i * GRID_SIZE // 3 + GRID_SIZE // 6
                    pygame.draw.line(surface, get_gradient_color(theme_colors['obstacle'], WHITE, 0.2),
                                    (detail_x, y * GRID_SIZE + GRID_SIZE),
                                    (detail_x, y * GRID_SIZE + GRID_SIZE // 2), 2)

# Game class
class Game:
    def __init__(self):
        self.state = MENU
        self.snake = Snake()
        self.food = Food(self.snake.grid, self.snake.positions)
        self.obstacles = ObstacleGenerator(self.snake.grid, self.snake.positions)
        self.grid = Grid()
        self.particle_system = ParticleSystem()
        self.high_score = 0
        self.last_score = 0
        self.game_over_time = 0

        # Create stars or bubbles for background
        self.stars = [Star() for _ in range(100)]
        self.bubbles = [Bubble() for _ in range(50)]

        # Attempt to load font
        try:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
            self.large_font = pygame.font.Font(None, 72)
        except:
            print("Warning: Default font not found, using system font")
            self.font = pygame.font.SysFont('Arial', 36)
            self.small_font = pygame.font.SysFont('Arial', 24)
            self.large_font = pygame.font.SysFont('Arial', 72)

    def reset(self):
        self.snake.reset()
        self.food = Food(self.snake.grid, self.snake.positions)
        self.obstacles = ObstacleGenerator(self.snake.grid, self.snake.positions)
        self.particle_system = ParticleSystem()

    def update(self):
        self.particle_system.update()

        # Update stars or bubbles based on theme
        if settings.theme == 2:  # Space theme
            for star in self.stars:
                star.update()
        elif settings.theme == 3:  # Underwater theme
            for bubble in self.bubbles:
                bubble.update()

        if self.state == PLAYING:
            # Update snake and check for collisions
            if not self.snake.update():
                self.state = GAME_OVER
                self.game_over_time = time.time()
                self.last_score = self.snake.score
                if self.snake.score > self.high_score:
                    self.high_score = self.snake.score
                return

            # Check for food collision
            if self.snake.check_food_collision(self.food):
                # Create particles at food location
                x, y = self.food.position
                center_x = x * GRID_SIZE + GRID_SIZE // 2
                center_y = y * GRID_SIZE + GRID_SIZE // 2

                if settings.particle_effects:
                    self.particle_system.add_particles(center_x, center_y, YELLOW, 15)

                # Reset food
                self.food.reset(self.snake.positions)

    def draw(self):
        theme_colors = settings.get_theme_colors()

        # Fill screen with background color
        screen.fill(theme_colors['background'])

        # Draw stars or bubbles based on theme
        if settings.theme == 2:  # Space theme
            for star in self.stars:
                star.draw(screen)
        elif settings.theme == 3:  # Underwater theme
            for bubble in self.bubbles:
                bubble.draw(screen)

        # Draw grid
        self.grid.draw(screen, theme_colors['grid'])

        if self.state == MENU:
            self.draw_menu()
        elif self.state == PLAYING:
            # Draw game elements
            self.obstacles.draw(screen, theme_colors)
            self.food.draw(screen, theme_colors)
            self.snake.draw(screen, theme_colors)
            self.particle_system.draw(screen)
            self.draw_hud()
        elif self.state == GAME_OVER:
            # Still draw game elements in background
            self.obstacles.draw(screen, theme_colors)
            self.food.draw(screen, theme_colors)
            self.snake.draw(screen, theme_colors)
            self.particle_system.draw(screen)

            # Draw game over screen
            self.draw_game_over()
        elif self.state == SETTINGS:
            self.draw_settings()

    def draw_hud(self):
        theme_colors = settings.get_theme_colors()

        # Draw score
        score_text = self.font.render(f"Score: {self.snake.score}", True, theme_colors['text'])
        screen.blit(score_text, (10, 10))

        # Draw high score
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, theme_colors['text'])
        high_score_rect = high_score_text.get_rect()
        high_score_rect.topright = (WIDTH - 10, 10)
        screen.blit(high_score_text, high_score_rect)

        # Draw special effect indicator if active
        if self.snake.special_effect:
            effect_name = self.snake.special_effect.replace('_', ' ').title()
            time_left = max(0, int(self.snake.special_effect_end - time.time()))
            effect_text = self.small_font.render(f"{effect_name}: {time_left}s", True, YELLOW)
            effect_rect = effect_text.get_rect()
            effect_rect.centerx = WIDTH // 2
            effect_rect.y = 10
            screen.blit(effect_text, effect_rect)

    def draw_menu(self):
        theme_colors = settings.get_theme_colors()

        # Draw title
        title_text = self.large_font.render("Cosmic Snake Adventure", True, theme_colors['text'])
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Draw menu options
        options = [
            ("Press SPACE to Play", WIDTH // 2, HEIGHT // 2),
            ("Press S for Settings", WIDTH // 2, HEIGHT // 2 + 50),
            (f"High Score: {self.high_score}", WIDTH // 2, HEIGHT // 2 + 100),
            ("Press ESC to Quit", WIDTH // 2, HEIGHT // 2 + 150)
        ]

        for text, x, y in options:
            text_surface = self.font.render(text, True, theme_colors['text'])
            text_rect = text_surface.get_rect(center=(x, y))
            screen.blit(text_surface, text_rect)

        # Draw animated snake in background
        t = time.time()
        snake_body = []
        for i in range(10):
            x = int(WIDTH // 2 + math.sin(t + i * 0.2) * 100)
            y = int(HEIGHT * 3 // 4 + math.cos(t + i * 0.2) * 50)
            snake_body.append((x, y))

        for i, (x, y) in enumerate(snake_body):
            if i == 0:  # Head
                color = theme_colors['snake_head']
            else:
                color = theme_colors['snake_body']

            pygame.draw.circle(screen, color, (x, y), 10)

    def draw_game_over(self):
        theme_colors = settings.get_theme_colors()

        # Create semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Draw game over text
        game_over_text = self.large_font.render("Game Over", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(game_over_text, game_over_rect)

        # Draw score
        score_text = self.font.render(f"Score: {self.last_score}", True, theme_colors['text'])
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(score_text, score_rect)

        # Draw high score
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, theme_colors['text'])
        high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(high_score_text, high_score_rect)

        # Draw restart message with animation
        if time.time() - self.game_over_time > 1:  # Wait 1 second before showing
            restart_alpha = int(255 * abs(math.sin(time.time() * 2)))
            restart_text = self.font.render("Press SPACE to Restart", True, theme_colors['text'])
            restart_text.set_alpha(restart_alpha)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3))
            screen.blit(restart_text, restart_rect)

            menu_text = self.font.render("Press M for Menu", True, theme_colors['text'])
            menu_rect = menu_text.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3 + 50))
            screen.blit(menu_text, menu_rect)

    def draw_settings(self):
        theme_colors = settings.get_theme_colors()

        # Draw title
        title_text = self.large_font.render("Settings", True, theme_colors['text'])
        title_rect = title_text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_text, title_rect)

        # Draw settings options
        settings_options = [
            ("Difficulty", ["Easy", "Medium", "Hard"][settings.difficulty], 1),
            ("Theme", ["Classic", "Neon", "Space", "Underwater"][settings.theme], 2),
            ("Snake Style", ["Classic", "Gradient", "Patterned", "Glowing"][settings.snake_style], 3),
            ("Special Foods", "ON" if settings.special_foods else "OFF", 4),
            ("Obstacles", "ON" if settings.obstacles else "OFF", 5),
            ("Grid", "ON" if settings.grid_visible else "OFF", 6),
            ("Particle Effects", "ON" if settings.particle_effects else "OFF", 8),
            ("Background Motion", "ON" if settings.background_motion else "OFF", 9),
            ("Trail Effect", "ON" if settings.trail_effect else "OFF", 10),
            ("", "Back to Menu (M)", 12)
        ]

        y_start = 120
        y_step = 40

        for label, value, position in settings_options:
            y = y_start + y_step * position

            if label:  # Skip label for the back option
                label_text = self.font.render(label + ":", True, theme_colors['text'])
                label_rect = label_text.get_rect(right=WIDTH // 2 - 20, y=y)
                screen.blit(label_text, label_rect)

            value_text = self.font.render(value, True, YELLOW)
            value_rect = value_text.get_rect(left=WIDTH // 2 + 20, y=y)
            screen.blit(value_text, value_rect)

        # Draw indicators for currently selected option
        selected_option = self.get_selected_setting_index()
        if selected_option < len(settings_options) - 1:  # Exclude Back option
            option_y = y_start + y_step * settings_options[selected_option][2]
            pygame.draw.polygon(screen, theme_colors['snake_head'], [
                (WIDTH // 2 - 40, option_y + 10),
                (WIDTH // 2 - 55, option_y + 20),
                (WIDTH // 2 - 40, option_y + 30)
            ])
            pygame.draw.polygon(screen, theme_colors['snake_head'], [
                (WIDTH // 2 + 10, option_y + 10),
                (WIDTH // 2 + 25, option_y + 20),
                (WIDTH // 2 + 10, option_y + 30)
            ])

    def get_selected_setting_index(self):
        # This function determines which setting is currently selected
        # For simplicity, we'll cycle through them based on time
        return int(time.time() * 0.5) % 10

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if self.state == MENU:
                if event.key == pygame.K_SPACE:
                    self.state = PLAYING
                    self.reset()
                elif event.key == pygame.K_s:
                    self.state = SETTINGS
                elif event.key == pygame.K_ESCAPE:
                    return False

            elif self.state == PLAYING:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.snake.change_direction((0, -1))
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.snake.change_direction((0, 1))
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.snake.change_direction((-1, 0))
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.snake.change_direction((1, 0))
                elif event.key == pygame.K_ESCAPE:
                    self.state = MENU

            elif self.state == GAME_OVER:
                if event.key == pygame.K_SPACE:
                    self.state = PLAYING
                    self.reset()
                elif event.key == pygame.K_m:
                    self.state = MENU

            elif self.state == SETTINGS:
                if event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                    self.state = MENU
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    # Previous setting
                    pass
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    # Next setting
                    pass
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    # Decrease setting value
                    self.adjust_setting(-1)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    # Increase setting value
                    self.adjust_setting(1)

        return True

    def adjust_setting(self, direction):
        # This would adjust the currently selected setting
        selected = self.get_selected_setting_index()

        if selected == 0:  # Difficulty
            settings.difficulty = (settings.difficulty + direction) % 3
        elif selected == 1:  # Theme
            settings.theme = (settings.theme + direction) % 4
        elif selected == 2:  # Snake Style
            settings.snake_style = (settings.snake_style + direction) % 4
        elif selected == 3:  # Special Foods
            settings.special_foods = not settings.special_foods
        elif selected == 4:  # Obstacles
            settings.obstacles = not settings.obstacles
        elif selected == 5:  # Grid
            settings.grid_visible = not settings.grid_visible
        elif selected == 6:  # Particle Effects
            settings.particle_effects = not settings.particle_effects
        elif selected == 7:  # Background Motion
            settings.background_motion = not settings.background_motion
        elif selected == 8:  # Trail Effect
            settings.trail_effect = not settings.trail_effect

# Main game loop
def main():
    game = Game()
    running = True

    while running:
        # Process events
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False

        # Update game state
        game.update()

        # Draw everything
        game.draw()

        # Update display
        pygame.display.flip()

        # Control frame rate
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
