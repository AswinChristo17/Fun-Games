import pygame
import random
import math
import json
import os
from enum import Enum
from typing import List, Tuple, Dict, Optional

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Zombie Escape"

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Game states
class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAMEOVER = 4
    SETTINGS = 5

# Difficulty settings
class Difficulty(Enum):
    EASY = 1
    NORMAL = 2
    HARD = 3
    ENDLESS = 4

# Powerup types
class PowerupType(Enum):
    SPEED = 1
    FREEZE = 2
    HEALTH = 3
    SHIELD = 4
    NUKE = 5
    SLOWMO = 6

# Asset paths
ASSET_DIR = "assets"
PLAYER_IMG = "player.png"
ZOMBIE_IMGS = ["zombie1.png", "zombie2.png", "zombie3.png", "zombie4.png"]
POWERUP_IMGS = {
    PowerupType.SPEED: "speed.png",
    PowerupType.FREEZE: "freeze.png",
    PowerupType.HEALTH: "health.png",
    PowerupType.SHIELD: "shield.png",
    PowerupType.NUKE: "nuke.png",
    PowerupType.SLOWMO: "slowmo.png"
}

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.speed = 5
        self.max_health = 100
        self.health = self.max_health
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_regen = 0.5
        self.is_sprinting = False
        self.sprint_multiplier = 1.5
        self.active_powerups = {}
        self.has_shield = False
        self.rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
        
        # Load player image
        self.original_image = pygame.Surface((self.width, self.height))
        self.original_image.fill(GREEN)  # Placeholder until we load actual image
        self.image = self.original_image
        
    def move(self, dx: int, dy: int, obstacles=None):
        # Calculate actual movement based on speed and powerups
        actual_speed = self.speed
        
        # Apply sprint if active and have stamina
        if self.is_sprinting and self.stamina > 0:
            actual_speed *= self.sprint_multiplier
            self.stamina -= 1
        elif not self.is_sprinting and self.stamina < self.max_stamina:
            self.stamina += self.stamina_regen
            
        # Apply speed powerup if active
        if PowerupType.SPEED in self.active_powerups:
            actual_speed *= 1.5
            
        # Apply actual movement
        new_x = self.x + dx * actual_speed
        new_y = self.y + dy * actual_speed
        
        # Screen boundary checks
        new_x = max(self.width // 2, min(new_x, SCREEN_WIDTH - self.width // 2))
        new_y = max(self.height // 2, min(new_y, SCREEN_HEIGHT - self.height // 2))
        
        # Update position
        self.x, self.y = new_x, new_y
        self.rect.center = (self.x, self.y)
        
    def take_damage(self, amount: int) -> bool:
        """Return True if player dies from this damage"""
        if self.has_shield:
            self.has_shield = False
            return False
            
        self.health -= amount
        return self.health <= 0
        
    def heal(self, amount: int):
        self.health = min(self.health + amount, self.max_health)
        
    def add_powerup(self, powerup_type: PowerupType, duration: int):
        self.active_powerups[powerup_type] = duration
        
        # Special case for nuke - no duration, immediate effect
        if powerup_type == PowerupType.NUKE:
            self.active_powerups[powerup_type] = 0
            
        # Special case for shield - no duration, one-time effect
        if powerup_type == PowerupType.SHIELD:
            self.has_shield = True
            
        # Special case for health - no duration, immediate effect
        if powerup_type == PowerupType.HEALTH:
            self.heal(25)
            self.active_powerups[powerup_type] = 0
            
    def update_powerups(self):
        # Remove expired powerups
        expired = []
        for powerup, time_left in self.active_powerups.items():
            if time_left <= 0:
                expired.append(powerup)
            else:
                self.active_powerups[powerup] -= 1
                
        for powerup in expired:
            del self.active_powerups[powerup]
            
    def draw(self, screen):
        # Draw player shape
        pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), self.width // 2)
        
        # Draw shield if active
        if self.has_shield:
            pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.width // 2 + 5, 2)
            
        # Draw health bar
        health_width = 40
        health_height = 5
        health_x = self.x - health_width // 2
        health_y = self.y - self.height // 2 - 10
        
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        pygame.draw.rect(screen, GREEN, (health_x, health_y, health_width * (self.health / self.max_health), health_height))
        
        # Draw stamina bar if sprinting is enabled
        if self.max_stamina > 0:
            stamina_y = health_y - 7
            pygame.draw.rect(screen, YELLOW, (health_x, stamina_y, health_width, health_height))
            pygame.draw.rect(screen, BLUE, (health_x, stamina_y, health_width * (self.stamina / self.max_stamina), health_height))


class Zombie:
    def __init__(self, x: int, y: int, zombie_type: str = "normal", difficulty: Difficulty = Difficulty.NORMAL):
        self.x = x
        self.y = y
        self.type = zombie_type
        self.width = 30
        self.height = 30
        self.rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
        
        # Set stats based on type and difficulty
        if zombie_type == "normal":
            self.speed = 2
            self.health = 100
            self.damage = 10
            self.color = RED
        elif zombie_type == "tank":
            self.speed = 1
            self.health = 200
            self.damage = 15
            self.color = (139, 69, 19)  # Brown
        elif zombie_type == "runner":
            self.speed = 3
            self.health = 50
            self.damage = 5
            self.color = (255, 165, 0)  # Orange
        elif zombie_type == "exploder":
            self.speed = 1.5
            self.health = 75
            self.damage = 25
            self.explosion_radius = 100
            self.color = (255, 0, 255)  # Magenta
            
        # Apply difficulty multipliers
        if difficulty == Difficulty.EASY:
            self.speed *= 0.8
            self.damage *= 0.8
        elif difficulty == Difficulty.HARD:
            self.speed *= 1.2
            self.damage *= 1.2
            self.health *= 1.2
            
        # Elite status (random chance)
        self.is_elite = random.random() < 0.1
        if self.is_elite:
            self.speed *= 1.3
            self.health *= 1.5
            self.damage *= 1.2
            self.width += 10
            self.height += 10
            
        # AI state
        self.state = "roam" if random.random() < 0.3 else "chase"
        self.roam_direction = random.uniform(0, 2 * math.pi)
        self.detection_range = 250
        self.roam_timer = random.randint(30, 90)  # Frames until changing direction
        
    def move(self, player_x: int, player_y: int, frozen: bool = False, slowmo: bool = False):
        if frozen:
            return
            
        speed_modifier = 0.5 if slowmo else 1.0
        
        # Determine if we should switch from roam to chase
        if self.state == "roam":
            dist_to_player = math.sqrt((player_x - self.x)**2 + (player_y - self.y)**2)
            if dist_to_player < self.detection_range:
                self.state = "chase"
            else:
                # Continue roaming
                self.roam_timer -= 1
                if self.roam_timer <= 0:
                    self.roam_direction = random.uniform(0, 2 * math.pi)
                    self.roam_timer = random.randint(30, 90)
                
                # Move in roam direction
                dx = math.cos(self.roam_direction)
                dy = math.sin(self.roam_direction)
                
                # Check if we're at screen edge and bounce
                if self.x <= 20 or self.x >= SCREEN_WIDTH - 20:
                    self.roam_direction = math.pi - self.roam_direction
                    dx = -dx
                if self.y <= 20 or self.y >= SCREEN_HEIGHT - 20:
                    self.roam_direction = -self.roam_direction
                    dy = -dy
                
                self.x += dx * self.speed * speed_modifier
                self.y += dy * self.speed * speed_modifier
                
        # Chase mode - move toward player
        if self.state == "chase":
            dx = player_x - self.x
            dy = player_y - self.y
            distance = max(0.1, math.sqrt(dx * dx + dy * dy))  # Prevent division by zero
            
            dx = dx / distance
            dy = dy / distance
            
            self.x += dx * self.speed * speed_modifier
            self.y += dy * self.speed * speed_modifier
            
        # Update rect position
        self.rect.center = (self.x, self.y)
        
    def take_damage(self, amount: int) -> bool:
        """Return True if zombie dies from this damage"""
        self.health -= amount
        return self.health <= 0
        
    def draw(self, screen):
        # Draw zombie with appropriate color
        if self.is_elite:
            # Draw elite glow
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.width // 2 + 3)
            
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.width // 2)
        
        # Draw health bar
        health_width = 30
        health_height = 3
        health_x = self.x - health_width // 2
        health_y = self.y - self.height // 2 - 8
        
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        pygame.draw.rect(screen, GREEN, (health_x, health_y, health_width * (self.health / (150 if self.is_elite else 100)), health_height))


class Powerup:
    def __init__(self, x: int, y: int, powerup_type: PowerupType):
        self.x = x
        self.y = y
        self.type = powerup_type
        self.width = 25
        self.height = 25
        self.duration = 0  # Set based on type
        self.rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
        
        # Set color and duration based on type
        if powerup_type == PowerupType.SPEED:
            self.color = BLUE
            self.duration = 5 * FPS  # 5 seconds
        elif powerup_type == PowerupType.FREEZE:
            self.color = (173, 216, 230)  # Light blue
            self.duration = 3 * FPS  # 3 seconds
        elif powerup_type == PowerupType.HEALTH:
            self.color = GREEN
            self.duration = 0  # Instant effect
        elif powerup_type == PowerupType.SHIELD:
            self.color = (192, 192, 192)  # Silver
            self.duration = 0  # Until hit
        elif powerup_type == PowerupType.NUKE:
            self.color = YELLOW
            self.duration = 0  # Instant effect
        elif powerup_type == PowerupType.SLOWMO:
            self.color = PURPLE
            self.duration = 5 * FPS  # 5 seconds
            
        # Set animation properties
        self.pulse_time = 0
        self.max_pulse = 30
        self.pulse_direction = 1
        
    def update_animation(self):
        # Pulse animation
        self.pulse_time += self.pulse_direction
        if self.pulse_time >= self.max_pulse:
            self.pulse_direction = -1
        elif self.pulse_time <= 0:
            self.pulse_direction = 1
            
    def draw(self, screen):
        # Draw powerup with pulsing effect
        pulse_size = self.width // 2 + self.pulse_time // 10
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), pulse_size)
        
        # Draw icon or symbol in the middle
        inner_color = WHITE
        pygame.draw.circle(screen, inner_color, (int(self.x), int(self.y)), self.width // 4)
        
        # Draw letter or symbol based on type
        font = pygame.font.SysFont(None, 20)
        
        if self.type == PowerupType.SPEED:
            text = "S"
        elif self.type == PowerupType.FREEZE:
            text = "F"
        elif self.type == PowerupType.HEALTH:
            text = "H"
        elif self.type == PowerupType.SHIELD:
            text = "B"  # B for Barrier
        elif self.type == PowerupType.NUKE:
            text = "N"
        elif self.type == PowerupType.SLOWMO:
            text = "T"  # T for Time
            
        text_surf = font.render(text, True, BLACK)
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        screen.blit(text_surf, text_rect)


class Game:
    def __init__(self):
        # Set up the screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        
        # Load settings or use defaults
        self.load_settings()
        
        # Game state variables
        self.state = GameState.MENU
        self.difficulty = Difficulty.NORMAL
        self.score = 0
        self.start_time = 0
        self.current_time = 0
        self.high_scores = self.load_high_scores()
        
        # Create game objects
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.zombies = []
        self.powerups = []
        
        # Game mechanics
        self.spawn_timer = 0
        self.spawn_rate = 60  # Frames between spawns
        self.difficulty_timer = 0
        self.difficulty_increase_rate = 30 * FPS  # 30 seconds
        self.powerup_timer = 0
        self.powerup_spawn_rate = 10 * FPS  # 10 seconds
        
        # Controls
        self.keys = {
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
            "sprint": pygame.K_LSHIFT,
            "pause": pygame.K_ESCAPE
        }
        
        # UI elements
        self.fonts = {
            "small": pygame.font.SysFont(None, 24),
            "medium": pygame.font.SysFont(None, 36),
            "large": pygame.font.SysFont(None, 72)
        }
        
        # Sound effects
        self.sounds = {
            # We'll implement these if we had sound files
        }
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
    def load_settings(self):
        # Default settings
        self.settings = {
            "fullscreen": False,
            "volume": 0.7,
            "music_volume": 0.5,
            "sfx_volume": 0.8,
            "frame_rate": 60,
            "controls": {
                "up": pygame.K_w,
                "down": pygame.K_s,
                "left": pygame.K_a,
                "right": pygame.K_d,
                "sprint": pygame.K_LSHIFT
            }
        }
        
        # Try to load from file
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def save_settings(self):
        try:
            with open("settings.json", "w") as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def load_high_scores(self):
        scores = []
        try:
            if os.path.exists("highscores.json"):
                with open("highscores.json", "r") as f:
                    scores = json.load(f)
        except Exception as e:
            print(f"Error loading high scores: {e}")
            
        return scores
        
    def save_high_score(self):
        try:
            scores = self.load_high_scores()
            scores.append({
                "score": self.score,
                "time": self.format_time(self.current_time - self.start_time),
                "difficulty": self.difficulty.name,
                "date": pygame.time.get_ticks()  # Use as a timestamp
            })
            
            # Sort by score
            scores.sort(key=lambda x: x["score"], reverse=True)
            
            # Keep only top 10
            scores = scores[:10]
            
            with open("highscores.json", "w") as f:
                json.dump(scores, f)
                
            self.high_scores = scores
        except Exception as e:
            print(f"Error saving high score: {e}")
            
    def start_game(self):
        # Reset game state
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.zombies = []
        self.powerups = []
        self.score = 0
        self.start_time = pygame.time.get_ticks()
        self.current_time = self.start_time
        self.spawn_timer = 0
        
        # Set spawn rate based on difficulty
        if self.difficulty == Difficulty.EASY:
            self.spawn_rate = 90  # 1.5 seconds
        elif self.difficulty == Difficulty.NORMAL:
            self.spawn_rate = 60  # 1 second
        elif self.difficulty == Difficulty.HARD:
            self.spawn_rate = 45  # 0.75 seconds
        elif self.difficulty == Difficulty.ENDLESS:
            self.spawn_rate = 60  # Start normal, gets harder
            
        self.state = GameState.PLAYING
        
    def game_over(self):
        self.save_high_score()
        self.state = GameState.GAMEOVER
        
    def spawn_zombie(self):
        # Choose a random edge to spawn from
        edge = random.randint(0, 3)  # 0: top, 1: right, 2: bottom, 3: left
        
        if edge == 0:  # Top
            x = random.randint(0, SCREEN_WIDTH)
            y = 0
        elif edge == 1:  # Right
            x = SCREEN_WIDTH
            y = random.randint(0, SCREEN_HEIGHT)
        elif edge == 2:  # Bottom
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT
        else:  # Left
            x = 0
            y = random.randint(0, SCREEN_HEIGHT)
            
        # Determine zombie type (weighted random)
        zombie_type = random.choices(
            ["normal", "tank", "runner", "exploder"],
            weights=[0.7, 0.1, 0.15, 0.05],
            k=1
        )[0]
        
        # Create and add zombie
        new_zombie = Zombie(x, y, zombie_type, self.difficulty)
        self.zombies.append(new_zombie)
        
    def spawn_powerup(self):
        # Don't spawn too many powerups
        if len(self.powerups) >= 3:
            return
            
        # Choose random position (away from edges)
        x = random.randint(50, SCREEN_WIDTH - 50)
        y = random.randint(50, SCREEN_HEIGHT - 50)
        
        # Choose powerup type (weighted random)
        powerup_type = random.choices(
            list(PowerupType),
            weights=[0.25, 0.2, 0.25, 0.15, 0.05, 0.1],  # SPEED, FREEZE, HEALTH, SHIELD, NUKE, SLOWMO
            k=1
        )[0]
        
        # Create and add powerup
        new_powerup = Powerup(x, y, powerup_type)
        self.powerups.append(new_powerup)
        
    def update(self):
        if self.state == GameState.PLAYING:
            # Update timers
            self.current_time = pygame.time.get_ticks()
            game_time = self.current_time - self.start_time
            
            # Handle player movement
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            if keys[self.keys["up"]]:
                dy = -1
            if keys[self.keys["down"]]:
                dy = 1
            if keys[self.keys["left"]]:
                dx = -1
            if keys[self.keys["right"]]:
                dx = 1
                
            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                dx *= 0.7071  # 1/sqrt(2)
                dy *= 0.7071
                
            # Handle sprinting
            self.player.is_sprinting = keys[self.keys["sprint"]]
            
            # Move player
            self.player.move(dx, dy)
            
            # Update player powerups
            self.player.update_powerups()
            
            # Check for zombie spawning
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_rate:
                self.spawn_zombie()
                self.spawn_timer = 0
                
            # Check for powerup spawning
            self.powerup_timer += 1
            if self.powerup_timer >= self.powerup_spawn_rate:
                self.spawn_powerup()
                self.powerup_timer = 0
                
            # Check for difficulty increase
            self.difficulty_timer += 1
            if self.difficulty_timer >= self.difficulty_increase_rate:
                # Increase difficulty
                if self.difficulty == Difficulty.ENDLESS:
                    # Make game progressively harder
                    self.spawn_rate = max(20, self.spawn_rate - 5)  # Spawn faster, min 3x per second
                
                self.difficulty_timer = 0
                
            # Check if zombies are frozen
            zombies_frozen = PowerupType.FREEZE in self.player.active_powerups
            slow_mo = PowerupType.SLOWMO in self.player.active_powerups
                
            # Update zombies
            for zombie in self.zombies:
                zombie.move(self.player.x, self.player.y, zombies_frozen, slow_mo)
                
            # Check zombie-player collisions
            collisions = []
            for i, zombie in enumerate(self.zombies):
                if self.player.rect.colliderect(zombie.rect):
                    collisions.append(i)
                    
                    # Apply damage and knockback
                    if self.player.take_damage(zombie.damage):
                        self.game_over()
                        return
                        
                    # Knockback effect
                    knockback_dx = self.player.x - zombie.x
                    knockback_dy = self.player.y - zombie.y
                    
                    # Normalize and apply knockback
                    knockback_dist = max(0.1, math.sqrt(knockback_dx * knockback_dx + knockback_dy * knockback_dy))
                    knockback_dx = knockback_dx / knockback_dist * 20
                    knockback_dy = knockback_dy / knockback_dist * 20
                    
                    # Move player with knockback
                    new_x = max(self.player.width // 2, min(self.player.x + knockback_dx, SCREEN_WIDTH - self.player.width // 2))
                    new_y = max(self.player.height // 2, min(self.player.y + knockback_dy, SCREEN_HEIGHT - self.player.height // 2))
                    
                    self.player.x, self.player.y = new_x, new_y
                    self.player.rect.center = (self.player.x, self.player.y)
                    
            # Check powerup collisions
            powerup_collisions = []
            for i, powerup in enumerate(self.powerups):
                if self.player.rect.colliderect(powerup.rect):
                    powerup_collisions.append(i)
                    
                    # Apply powerup effect
                    self.player.add_powerup(powerup.type, powerup.duration)
                    
                    # Handle nuke
                    if powerup.type == PowerupType.NUKE:
                        self.zombies = []  # Clear all zombies
                        self.score += 100  # Bonus points
                    
            # Remove collected powerups
            for i in reversed(powerup_collisions):
                self.powerups.pop(i)
                
            # Update powerup animations
            for powerup in self.powerups:
                powerup.update_animation()
                
            # Score increases with time
            self.score = int((game_time / 1000) * 10)  # 10 points per second
            
    def draw(self):
        # Clear screen
        self.screen.fill(BLACK)
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.PAUSED:
            self.draw_game()  # Draw game in background
            self.draw_pause_menu()
        elif self.state == GameState.GAMEOVER:
            self.draw_game_over()
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
            
        # Update display
        pygame.display.flip()
        
    def draw_menu(self):
        # Draw title
        title = self.fonts["large"].render("ZOMBIE ESCAPE", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Draw menu options
        start_text = self.fonts["medium"].render("Start Game", True, GREEN)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(start_text, start_rect)
        
        settings_text = self.fonts["medium"].render("Settings", True, WHITE)
        settings_rect = settings_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(settings_text, settings_rect)
        
        exit_text = self.fonts["medium"].render("Exit", True, WHITE)
        exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(exit_text, exit_rect)
        
        # Draw difficulty options
        diff_text = self.fonts["small"].render("Difficulty:", True, WHITE)
        diff_rect = diff_text.get_rect(center=(SCREEN_WIDTH // 2, 470))
        self.screen.blit(diff_text, diff_rect)
        
        difficulties = ["Easy", "Normal", "Hard", "Endless"]
        for i, diff in enumerate(difficulties):
            color = GREEN if self.difficulty == Difficulty(i + 1) else WHITE
            diff_option = self.fonts["small"].render(diff, True, color)
            diff_option_rect = diff_option.get_rect(center=(SCREEN_WIDTH // 2 - 100 + i * 70, 500))
            self.screen.blit(diff_option, diff_option_rect)
            
        # Draw high scores
        self.draw_high_scores()
        
    def draw_high_scores(self):
        # Draw high scores title
        hs_title = self.fonts["medium"].render("High Scores", True, YELLOW)
        hs_rect = hs_title.get_rect(center=(SCREEN_WIDTH // 2, 570))
        self.screen.blit(hs_title, hs_rect)
        
        # Draw top 5 scores
        for i, score in enumerate(self.high_scores[:5]):
            score_text = self.fonts["small"].render(
                f"{i+1}. {score['score']} pts - {score['time']} - {score['difficulty']}",
                True, WHITE
            )
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 600 + i * 25))
            self.screen.blit(score_text, score_rect)
            
    def draw_game(self):
        # Draw all game objects
        
        # Draw powerups first (so they appear behind other objects)
        for powerup in self.powerups:
            powerup.draw(self.screen)
            
        # Draw zombies
        for zombie in self.zombies:
            zombie.draw(self.screen)
            
        # Draw player
        self.player.draw(self.screen)
        
        # Draw UI elements
        self.draw_hud()
        
    def draw_hud(self):
        # Draw score
        score_text = self.fonts["medium"].render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        
        # Draw time
        elapsed_time = self.current_time - self.start_time
        time_text = self.fonts["medium"].render(f"Time: {self.format_time(elapsed_time)}", True, WHITE)
        self.screen.blit(time_text, (20, 60))
        
        # Draw active powerups
        powerup_y = 100
        for powerup_type, time_left in self.player.active_powerups.items():
            if time_left > 0:  # Only show powerups with time remaining
                if powerup_type == PowerupType.SPEED:
                    name = "Speed Boost"
                    color = BLUE
                elif powerup_type == PowerupType.FREEZE:
                    name = "Freeze"
                    color = (173, 216, 230)  # Light blue
                elif powerup_type == PowerupType.SLOWMO:
                    name = "Slow Motion"
                    color = PURPLE
                else:
                    continue  # Skip non-timed powerups
                    
                powerup_text = self.fonts["small"].render(f"{name}: {time_left // FPS}s", True, color)
                self.screen.blit(powerup_text, (20, powerup_y))
                powerup_y += 25
                
        # Draw shield indicator if active
        if self.player.has_shield:
            shield_text = self.fonts["small"].render("Shield Active", True, (192, 192, 192))
            self.screen.blit(shield_text, (20, powerup_y))
            
    def draw_pause_menu(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause menu
        pause_text = self.fonts["large"].render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(pause_text, pause_rect)
        
        # Draw menu options
        resume_text = self.fonts["medium"].render("Resume", True, GREEN)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(resume_text, resume_rect)
        
        settings_text = self.fonts["medium"].render("Settings", True, WHITE)
        settings_rect = settings_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(settings_text, settings_rect)
        
        menu_text = self.fonts["medium"].render("Main Menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(menu_text, menu_rect)
        
    def draw_game_over(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Draw game over message
        gameover_text = self.fonts["large"].render("GAME OVER", True, RED)
        gameover_rect = gameover_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(gameover_text, gameover_rect)
        
        # Draw final score
        score_text = self.fonts["medium"].render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(score_text, score_rect)
        
        # Draw survival time
        time_text = self.fonts["medium"].render(
            f"Survival Time: {self.format_time(self.current_time - self.start_time)}",
            True, WHITE
        )
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
        self.screen.blit(time_text, time_rect)
        
        # Draw menu options
        retry_text = self.fonts["medium"].render("Retry", True, GREEN)
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, 380))
        self.screen.blit(retry_text, retry_rect)
        
        menu_text = self.fonts["medium"].render("Main Menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, 430))
        self.screen.blit(menu_text, menu_rect)
        
    def draw_settings(self):
        # Draw title
        settings_text = self.fonts["large"].render("SETTINGS", True, WHITE)
        settings_rect = settings_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(settings_text, settings_rect)
        
        # Draw settings options
        y_pos = 200
        
        # Volume settings
        volume_text = self.fonts["medium"].render(f"Volume: {int(self.settings['volume'] * 100)}%", True, WHITE)
        volume_rect = volume_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(volume_text, volume_rect)
        
        # Draw volume slider
        slider_width = 300
        slider_height = 20
        slider_x = SCREEN_WIDTH // 2 - slider_width // 2
        slider_y = y_pos + 30
        
        pygame.draw.rect(self.screen, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height))
        pygame.draw.rect(self.screen, WHITE, (slider_x, slider_y, int(slider_width * self.settings["volume"]), slider_height))
        
        y_pos += 80
        
        # Fullscreen option
        fullscreen_text = self.fonts["medium"].render("Fullscreen", True, WHITE)
        fullscreen_rect = fullscreen_text.get_rect(midright=(SCREEN_WIDTH // 2 - 20, y_pos))
        self.screen.blit(fullscreen_text, fullscreen_rect)
        
        # Draw checkbox
        checkbox_size = 20
        checkbox_x = SCREEN_WIDTH // 2 + 20
        checkbox_y = y_pos - checkbox_size // 2
        
        pygame.draw.rect(self.screen, WHITE, (checkbox_x, checkbox_y, checkbox_size, checkbox_size), 2)
        if self.settings["fullscreen"]:
            pygame.draw.rect(self.screen, GREEN, (checkbox_x + 4, checkbox_y + 4, checkbox_size - 8, checkbox_size - 8))
            
        y_pos += 50
        
        # Frame rate options
        fps_text = self.fonts["medium"].render("Frame Rate:", True, WHITE)
        fps_rect = fps_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(fps_text, fps_rect)
        
        y_pos += 40
        
        # FPS options
        fps_options = [30, 60, 120]
        for i, fps in enumerate(fps_options):
            color = GREEN if self.settings["frame_rate"] == fps else WHITE
            fps_option = self.fonts["small"].render(f"{fps} FPS", True, color)
            fps_option_rect = fps_option.get_rect(center=(SCREEN_WIDTH // 2 - 100 + i * 100, y_pos))
            self.screen.blit(fps_option, fps_option_rect)
            
        y_pos += 80
            
        # Back button
        back_text = self.fonts["medium"].render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(back_text, back_rect)
        
    def format_time(self, ms: int) -> str:
        """Format milliseconds into mm:ss format"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
        
    def handle_click(self, pos):
        """Handle mouse clicks based on current game state"""
        x, y = pos
        
        if self.state == GameState.MENU:
            # Start game button
            if 300 - 20 <= y <= 300 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.start_game()
                
            # Settings button
            elif 350 - 20 <= y <= 350 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.state = GameState.SETTINGS
                
            # Exit button
            elif 400 - 20 <= y <= 400 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                return False  # Exit game
                
            # Difficulty options
            elif 500 - 15 <= y <= 500 + 15:
                if SCREEN_WIDTH // 2 - 130 <= x <= SCREEN_WIDTH // 2 - 70:
                    self.difficulty = Difficulty.EASY
                elif SCREEN_WIDTH // 2 - 70 <= x <= SCREEN_WIDTH // 2:
                    self.difficulty = Difficulty.NORMAL
                elif SCREEN_WIDTH // 2 <= x <= SCREEN_WIDTH // 2 + 70:
                    self.difficulty = Difficulty.HARD
                elif SCREEN_WIDTH // 2 + 70 <= x <= SCREEN_WIDTH // 2 + 130:
                    self.difficulty = Difficulty.ENDLESS
                    
        elif self.state == GameState.PAUSED:
            # Resume button
            if 300 - 20 <= y <= 300 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.state = GameState.PLAYING
                
            # Settings button
            elif 350 - 20 <= y <= 350 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.state = GameState.SETTINGS
                
            # Main menu button
            elif 400 - 20 <= y <= 400 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.state = GameState.MENU
                
        elif self.state == GameState.GAMEOVER:
            # Retry button
            if 380 - 20 <= y <= 380 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.start_game()
                
            # Main menu button
            elif 430 - 20 <= y <= 430 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.state = GameState.MENU
                
        elif self.state == GameState.SETTINGS:
            # Volume slider
            slider_width = 300
            slider_height = 20
            slider_x = SCREEN_WIDTH // 2 - slider_width // 2
            slider_y = 230
            
            if slider_y <= y <= slider_y + slider_height and slider_x <= x <= slider_x + slider_width:
                # Calculate new volume
                self.settings["volume"] = (x - slider_x) / slider_width
                
            # Fullscreen toggle
            checkbox_size = 20
            checkbox_x = SCREEN_WIDTH // 2 + 20
            checkbox_y = 280 - checkbox_size // 2
            
            if checkbox_y <= y <= checkbox_y + checkbox_size and checkbox_x <= x <= checkbox_x + checkbox_size:
                self.settings["fullscreen"] = not self.settings["fullscreen"]
                
                # Apply fullscreen setting
                if self.settings["fullscreen"]:
                    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    
            # FPS options
            if 370 - 15 <= y <= 370 + 15:
                fps_options = [30, 60, 120]
                for i, fps in enumerate(fps_options):
                    if SCREEN_WIDTH // 2 - 100 + i * 100 - 40 <= x <= SCREEN_WIDTH // 2 - 100 + i * 100 + 40:
                        self.settings["frame_rate"] = fps
                        
            # Back button
            if 450 - 20 <= y <= 450 + 20 and SCREEN_WIDTH // 2 - 80 <= x <= SCREEN_WIDTH // 2 + 80:
                self.save_settings()
                # Return to previous state
                if self.prev_state:
                    self.state = self.prev_state
                else:
                    self.state = GameState.MENU
                    
        return True  # Continue game
        
    def run(self):
        running = True
        
        # Main game loop
        while running:
            # Store previous state when entering settings
            if self.state == GameState.SETTINGS:
                if not hasattr(self, 'prev_state'):
                    self.prev_state = GameState.MENU
            else:
                self.prev_state = self.state
                
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == self.keys["pause"] and self.state in [GameState.PLAYING, GameState.PAUSED]:
                        if self.state == GameState.PLAYING:
                            self.state = GameState.PAUSED
                        else:
                            self.state = GameState.PLAYING
                            
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        running = self.handle_click(event.pos)
                        
                elif event.type == pygame.VIDEORESIZE:
                    if not self.settings["fullscreen"]:
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                        SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                        
            # Update game state
            self.update()
            
            # Draw everything
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(self.settings["frame_rate"])
            
        # Save settings before quitting
        self.save_settings()
        pygame.quit()
        
if __name__ == "__main__":
    # Run the game
    game = Game()
    game.run()