"""
Python implementation of Chrome's Dino Run game.
"""

import pygame
import random
import os
import math
import numpy as np

FLOOR_COLOR    = (0, 200, 0)
OBSTACLE_COLOR = (200, 40, 40)
BIRD_COLOR     = (40, 40, 200)
SKY_COLOR      = (255, 255, 255)

DINO_COLOR        = (80, 80, 80)
CACTUS_SMALL_COLOR = (34, 139, 34)
CACTUS_LARGE_COLOR = (0, 100, 0)
BIRD_RECT_COLOR   = (30, 30, 180)
TRACK_COLOR       = (160, 160, 160)

INIT_SPEED = 15
MAX_SPEED  = 50
SPEED_INC  = 0.01

SCREEN_WIDTH  = 1100
SCREEN_HEIGHT = 600

N_RAYS     = 33
RAY_LENGTH = 800
FOV        = 60

ray_angles = [i * (FOV / N_RAYS) for i in range(-N_RAYS // 2, N_RAYS // 2)]
ray_angles = [a * (math.pi / 180) for a in ray_angles]

ASSETS: dict = {}

def load_assets():
    global ASSETS
    ASSETS = {
        'DinoRun':  [pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
                     pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png"))],
        'DinoJump':  pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png")),
        'DinoDuck': [pygame.image.load(os.path.join("Assets/Dino", "DinoDuck1.png")),
                     pygame.image.load(os.path.join("Assets/Dino", "DinoDuck2.png"))],
        'CactusSmall': [pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
                        pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
                        pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png"))],
        'CactusLarge': [pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
                        pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
                        pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png"))],
        'Bird': [pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
                 pygame.image.load(os.path.join("Assets/Bird", "Bird2.png"))],
        'Track': pygame.image.load(os.path.join("Assets/Other", "Track.png")),
    }


class VisualizationConfig:

    def __init__(self,
                 show_rays:   bool = False,
                 show_vision: bool = False,
                 simple_rects: bool = False,
                 show_help:   bool = True):
        self.show_rays    = show_rays     # draw raycasting lines
        self.show_vision  = show_vision   # draw coloured vision bar at bottom
        self.simple_rects = simple_rects  # replace sprites with solid rectangles
        self.show_help    = show_help     # overlay keybinding cheatsheet

    def handle_keydown(self, event):
        if event.key == pygame.K_r:
            self.show_rays = not self.show_rays
        elif event.key == pygame.K_v:
            self.show_vision = not self.show_vision
        elif event.key == pygame.K_b:
            self.simple_rects = not self.simple_rects
        elif event.key == pygame.K_h:
            self.show_help = not self.show_help

class DinoGame:
    def __init__(self, vis_config: VisualizationConfig | None = None):
        self.vis = vis_config or VisualizationConfig()
        self.time       = 0
        self.game_speed = INIT_SPEED
        self.jump_velocity = 25
        self.gravity       = 3
        self.screen_size   = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.SCREEN = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Dino Run")
        self._init_objects()

    def _init_objects(self):
        self.dinosaur  = Dinosaur(self.gravity, self.jump_velocity)
        self.background = Background()
        self.obstacles  = []
        self.done      = False
        self.collision  = False

    def reset(self):
        self.time       = 0
        self.game_speed = INIT_SPEED
        self._init_objects()

    def render(self):
        self.SCREEN.fill(SKY_COLOR)
        self.background.draw(self.SCREEN, self.vis.simple_rects)
        self.dinosaur.draw(self.SCREEN, self.vis.simple_rects)
        for obstacle in self.obstacles:
            obstacle.draw(self.SCREEN, self.vis.simple_rects)

        if self.vis.show_vision:
            vision = self.get_vision(self.SCREEN, draw=True, return_color=True)
            self._draw_vision_bar(vision)
        elif self.vis.show_rays:
            self.get_vision(self.SCREEN, draw=True, return_color=False)

        self._draw_hud()
        if self.vis.show_help:
            self._draw_help()
        pygame.display.flip()

    def _draw_hud(self):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.time}', True, (0, 0, 0))
        self.SCREEN.blit(score_text, (10, 10))

        speed_text = font.render(f'Speed: {self.game_speed:.1f}', True, (80, 80, 80))
        self.SCREEN.blit(speed_text, (10, 45))

    def _draw_help(self):
        lines = [
            "[R] Rays: " + ("ON" if self.vis.show_rays else "off"),
            "[V] Vision: " + ("ON" if self.vis.show_vision else "off"),
            "[B] Rect mode: " + ("ON" if self.vis.simple_rects else "off"),
            "[H] Hide help",
        ]
        font = pygame.font.Font(None, 26)
        x, y = SCREEN_WIDTH - 200, 10
        bg = pygame.Surface((190, len(lines) * 22 + 10), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 100))
        self.SCREEN.blit(bg, (x - 5, y - 5))
        for i, line in enumerate(lines):
            surf = font.render(line, True, (230, 230, 230))
            self.SCREEN.blit(surf, (x, y + i * 22))

    def _draw_vision_bar(self, vision):
        grid_size   = 20
        bar_height  = grid_size * 2
        vision_y    = self.screen_size[1] - bar_height
        bg_color    = (220, 220, 220)
        line_color  = (200, 200, 200)
        grid_y      = vision_y + (bar_height - grid_size) // 2

        pygame.draw.rect(self.SCREEN, bg_color,
                         (0, vision_y, N_RAYS * grid_size, bar_height))
        for i in range(N_RAYS):
            color = tuple(int(c) for c in vision[i])
            rect  = (i * grid_size, grid_y, grid_size, grid_size)
            pygame.draw.rect(self.SCREEN, color, rect)
            if i < N_RAYS - 1:
                pygame.draw.line(self.SCREEN, line_color,
                                 (rect[0] + grid_size, grid_y),
                                 (rect[0] + grid_size, grid_y + grid_size), 1)

    def update(self, userInput):
        self.background.update(self.game_speed)
        self.dinosaur.update(userInput)
        for obstacle in list(self.obstacles):
            obstacle.update(self.game_speed)
            if obstacle.rect.x < -obstacle.rect.width:
                self.obstacles.remove(obstacle)
        self.generate_obstacle()
        if self.check_collision():
            self.collision = True
            self.done      = True
            self.lose()
        self.time += 1
        self.game_speed = min(self.game_speed + SPEED_INC, MAX_SPEED)

    def get_observation(self):
        return self.get_vision(self.SCREEN, draw=False, return_color=True)

    def get_vision(self, SCREEN, draw=True, return_color=False):
        ray_start_offset = (55, 10)
        vision = np.zeros((N_RAYS, 3))
        ox = self.dinosaur.dino_rect.x + ray_start_offset[0]
        oy = self.dinosaur.dino_rect.y + ray_start_offset[1]
        for ii, an in enumerate(ray_angles):
            ray = RayCast(ox, oy, an, RAY_LENGTH)
            if draw:
                ray.draw(SCREEN)
            first_obstacle = ray.find_first_obstacle(self.obstacles)
            result = ray.draw_intersection(SCREEN, first_obstacle,
                                           draw=draw, return_color=return_color)
            if result is not None:
                vision[ii, :] = result
        return vision

    def lose(self):
        print(f"Game Over! Your score was: {self.time}")
        pygame.quit()

    def check_collision(self):
        for obstacle in self.obstacles:
            if self.dinosaur.dino_rect.colliderect(obstacle.rect):
                return True
        return False

    def generate_obstacle(self):
        if self.obstacles:               # only one obstacle at a time
            return
        if random.random() > 0.15:      # 15% chance each frame
            return
        obstacle_type = random.choice(['small_cactus', 'large_cactus', 'bird'])
        if obstacle_type == 'small_cactus':
            self.obstacles.append(SmallCactus(self.screen_size[0]))
        elif obstacle_type == 'large_cactus':
            self.obstacles.append(LargeCactus(self.screen_size[0]))
        else:
            self.obstacles.append(Bird(self.screen_size[0]))

class Background:
    Y_POS = 380

    def __init__(self):
        self.image  = ASSETS['Track']
        self.x_pos  = 0
        self.width  = self.image.get_width()
        self.height = self.image.get_height()

    def draw(self, SCREEN, simple_rects=False):
        if simple_rects:
            pygame.draw.rect(SCREEN, TRACK_COLOR,
                             (0, self.Y_POS, SCREEN_WIDTH, self.height))
        else:
            SCREEN.blit(self.image, (self.x_pos, self.Y_POS))
            SCREEN.blit(self.image, (self.x_pos + self.width, self.Y_POS))

    def update(self, game_speed):
        self.x_pos -= game_speed
        if self.x_pos <= -self.width:
            self.x_pos = 0

class Dinosaur:
    X_POS        = 80
    Y_POS        = 310
    Y_POS_DUCK   = 340
    FRAMES_PER_IMAGE = 5

    RECT_SIZE_RUN  = (44, 47)
    RECT_SIZE_DUCK = (59, 30)
    RECT_SIZE_JUMP = (44, 47)

    def __init__(self, gravity, jump_velocity):
        self.gravity       = gravity
        self.jump_velocity = jump_velocity
        self.running_imgs  = ASSETS['DinoRun']
        self.jumping_img   = ASSETS['DinoJump']
        self.ducking_imgs  = ASSETS['DinoDuck']

        self.state      = 'running'
        self.y_velocity = 0
        self.step_index = 0
        self.dino_rect  = self.running_imgs[0].get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.image = self.running_imgs[0]

    def update(self, userInput):
        if self.state == 'jumping':
            self._apply_gravity()
        elif userInput[pygame.K_UP] and self.dino_rect.y >= self.Y_POS:
            self.state      = 'jumping'
            self.y_velocity = -self.jump_velocity
            self.image      = self.jumping_img
        elif userInput[pygame.K_DOWN] and self.state != 'jumping':
            self.state = 'ducking'
            self.duck()
        else:
            self.state = 'running'
            self.run()

        if self.step_index >= 2 * self.FRAMES_PER_IMAGE:
            self.step_index = 0

    def _apply_gravity(self):
        self.image = self.jumping_img
        self.dino_rect.y += self.y_velocity
        if self.y_velocity < 0:
            self.y_velocity += self.gravity * 0.6
        else:
            self.y_velocity += self.gravity * 1.0
        if self.dino_rect.y >= self.Y_POS:
            self.dino_rect.y = self.Y_POS
            self.y_velocity  = 0
            self.state       = 'running'
            self.run()

    def duck(self):
        idx = (self.step_index // self.FRAMES_PER_IMAGE) % len(self.ducking_imgs)
        self.image = self.ducking_imgs[idx]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS_DUCK
        self.step_index += 1

    def run(self):
        idx = (self.step_index // self.FRAMES_PER_IMAGE) % len(self.running_imgs)
        self.image = self.running_imgs[idx]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.step_index += 1

    def draw(self, SCREEN, simple_rects=False):
        if simple_rects:
            pygame.draw.rect(SCREEN, DINO_COLOR, self.dino_rect)
        else:
            SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))

class Obstacle:
    RECT_COLOR = OBSTACLE_COLOR

    def __init__(self, images, type_index, screen_width):
        self.images = images
        self.type   = type_index
        self.rect   = self.images[self.type].get_rect()
        self.rect.x = screen_width

    def update(self, game_speed):
        self.rect.x -= game_speed

    def draw(self, SCREEN, simple_rects=False):
        if simple_rects:
            pygame.draw.rect(SCREEN, self.RECT_COLOR, self.rect)
        else:
            SCREEN.blit(self.images[self.type], self.rect)


class SmallCactus(Obstacle):
    RECT_COLOR = CACTUS_SMALL_COLOR

    def __init__(self, screen_width):
        super().__init__(ASSETS['CactusSmall'], 1, screen_width)
        self.rect.y = 325


class LargeCactus(Obstacle):
    RECT_COLOR = CACTUS_LARGE_COLOR

    def __init__(self, screen_width):
        super().__init__(ASSETS['CactusLarge'], 2, screen_width)
        self.rect.y = 300


class Bird(Obstacle):
    FRAMES_PER_IMAGE = 5
    RECT_COLOR = BIRD_RECT_COLOR

    def __init__(self, screen_width):
        super().__init__(ASSETS['Bird'], 0, screen_width)
        self.rect.y = 250
        self.index  = 0

    def draw(self, SCREEN, simple_rects=False):
        if simple_rects:
            pygame.draw.rect(SCREEN, self.RECT_COLOR, self.rect)
        else:
            if self.index >= 2 * self.FRAMES_PER_IMAGE:
                self.index = 0
            SCREEN.blit(self.images[self.index // self.FRAMES_PER_IMAGE], self.rect)
            self.index += 1

class RayCast:
    def __init__(self, x, y, angle, length):
        self.x      = x
        self.y      = y
        self.angle  = angle
        self.length = length

    def cast(self):
        end_x = self.x + self.length * math.cos(self.angle)
        end_y = self.y + self.length * math.sin(self.angle)
        return end_x, end_y

    def draw(self, SCREEN):
        end_x, end_y = self.cast()
        pygame.draw.line(SCREEN, (255, 80, 80),
                         (self.x, self.y), (int(end_x), int(end_y)), 1)

    def find_first_obstacle(self, obstacles):
        closest      = None
        closest_dist = float('inf')
        for obstacle in obstacles:
            pt = self.get_intersection_position(obstacle)
            if pt is not None:
                dist = math.hypot(pt[0] - self.x, pt[1] - self.y)
                if dist < closest_dist:
                    closest_dist = dist
                    closest      = obstacle
        return closest

    def get_intersection_position(self, obstacle):
        ray_start = (self.x, self.y)
        ray_end   = self.cast()
        rect      = obstacle.rect
        edges = [
            ((rect.left,  rect.top),    (rect.right, rect.top)),
            ((rect.right, rect.top),    (rect.right, rect.bottom)),
            ((rect.right, rect.bottom), (rect.left,  rect.bottom)),
            ((rect.left,  rect.bottom), (rect.left,  rect.top)),
        ]
        closest, min_dist = None, float('inf')
        for e0, e1 in edges:
            pt = self._line_intersection(ray_start, ray_end, e0, e1)
            if pt:
                d = math.hypot(pt[0] - self.x, pt[1] - self.y)
                if d < min_dist:
                    min_dist = d
                    closest  = pt
        return closest

    @staticmethod
    def _line_intersection(p1, p2, q1, q2):
        x1, y1 = p1; x2, y2 = p2
        x3, y3 = q1; x4, y4 = q2
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        if 0 <= t <= 1 and 0 <= u <= 1:
            return x1 + t * (x2 - x1), y1 + t * (y2 - y1)
        return None

    def _attenuate(self, color, distance):
        factor = max(0.0, 1.0 - distance / RAY_LENGTH)
        return tuple(int(c * factor) for c in color)

    def draw_intersection(self, SCREEN, obstacle, draw=True, return_color=False):
        if obstacle is None:
            if self.angle > 0:                       # ray points downward → hits floor
                y_inter = 392
                denom = math.tan(self.angle)
                if abs(denom) < 1e-9:
                    return np.zeros(3)
                x_inter = self.x + (y_inter - self.y) / denom
                intersection = (x_inter, y_inter)
                color = FLOOR_COLOR
            else:                                    # ray points upward → sky
                if return_color:
                    return np.array(SKY_COLOR, dtype=float)
                return None
        else:
            intersection = self.get_intersection_position(obstacle)
            if intersection is None:
                return np.zeros(3)
            color = BIRD_COLOR if obstacle.type == 0 else OBSTACLE_COLOR

        if intersection and draw:
            pygame.draw.circle(SCREEN, (0, 220, 0),
                               (int(intersection[0]), int(intersection[1])), 4)
        if return_color:
            dist = math.hypot(intersection[0] - self.x, intersection[1] - self.y)
            return np.array(self._attenuate(color, dist), dtype=float)
        return None

def play_game():
    pygame.init()

    vis = VisualizationConfig(
        show_rays=False,
        show_vision=False,
        simple_rects=False,
        show_help=True,
    )

    load_assets()
    game  = DinoGame(vis_config=vis)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                vis.handle_keydown(event)

        userInput = pygame.key.get_pressed()
        game.update(userInput)
        game.render()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    play_game()
