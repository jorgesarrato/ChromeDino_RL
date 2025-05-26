"""
Python implementation of Chrome's Dino Run game.
"""

import pygame
import random
import os
import math
import numpy as np

FLOOR_COLOR = (0, 255, 0)
OBSTACLE_COLOR = (255, 0, 0)
BIRD_COLOR = (0, 0, 255)
SKY_COLOR = (255, 255, 255)

N_RAYS = 33
RAY_LENGTH = 800
FOV = 60  # Field of View in degrees

ray_angles = [i * (FOV / N_RAYS) for i in range(-N_RAYS // 2, N_RAYS // 2)]
ray_angles = [angle * (3.14 / 180) for angle in ray_angles]  # Convert to radians


ASSETS = {'DinoRun': [pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
                            pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png"))],
          'DinoJump': pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png")),
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
          'Track': pygame.image.load(os.path.join("Assets/Other", "Track.png"))
          }

class DinoGame:
    def __init__(self):
        self.time = 0 
        self.game_speed = 10
        self.jump_velocity = 20
        self.gravity = 2
        self.screen_size = (1100, 600)
        self.dinosaur = Dinosaur(self.gravity, self.jump_velocity)
        self.background = Background()
        self.obstacles = []
        self.SCREEN = pygame.display.set_mode(self.screen_size)
        self.done = False
        self.collision = False

    def reset(self):
        self.time = 0
        self.game_speed = 10
        self.dinosaur = Dinosaur(self.gravity, self.jump_velocity)
        self.background = Background()
        self.obstacles = []
        self.done = False
        self.collision = False

    def render(self, show_rays=False, show_vision=False):
        self.SCREEN.fill((255, 255, 255))
        self.background.draw(self.SCREEN)
        self.dinosaur.draw(self.SCREEN)
        for obstacle in self.obstacles:
            obstacle.draw(self.SCREEN)
        # Display the score
        if show_vision:
            vision = self.get_vision(self.SCREEN, draw=True, return_color=True)
            self.display_vision(vision)
        elif show_rays:
            _ = self.get_vision(self.SCREEN, draw=True, return_color=False)
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.time}', True, (0, 0, 0))
        self.SCREEN.blit(score_text, (10, 10))
        pygame.display.flip()

    def display_vision(self, vision):
        # Display vision with a thicker background bar
        grid_size = 20
        vision_width = N_RAYS * grid_size
        vision_height = grid_size
        bar_height = grid_size * 2  # Make the background bar thicker than the vision grid
        vision_x = 0
        vision_y = self.screen_size[1] - bar_height
        bg_color = (220, 220, 220)
        line_color = (200, 200, 200)

        # Draw thick background bar
        pygame.draw.rect(self.SCREEN, bg_color, (vision_x, vision_y, vision_width, bar_height))

        # Draw the vision grid centered vertically in the bar
        grid_y = vision_y + (bar_height - vision_height) // 2
        for i in range(N_RAYS):
            color = tuple(int(c) for c in vision[i])
            rect = (i * grid_size, grid_y, grid_size, vision_height)
            pygame.draw.rect(self.SCREEN, color, rect)
            if i < N_RAYS - 1:
                pygame.draw.line(self.SCREEN, line_color, (rect[0] + grid_size, grid_y), (rect[0] + grid_size, grid_y + vision_height), 1)

    def update(self, userInput):
        self.background.update(self.game_speed)
        self.dinosaur.update(userInput)
        for obstacle in self.obstacles:
            obstacle.update(self.game_speed)
            if obstacle.rect.x < -obstacle.rect.width:
                self.obstacles.remove(obstacle)
        self.generate_obstacle()
        if self.check_collision():
            self.collision = True
            self.done = True
            self.lose()
        self.time += 1
            
    def get_observation(self):
        vision = self.get_vision(self.SCREEN, draw=False, return_color=True)
        pass

    def get_vision(self, SCREEN, draw=True, return_color=False):

        ray_start_offset = (55, +10)

        vision = np.zeros((N_RAYS, 3))

        for ii,an in enumerate(ray_angles):
            ray = RayCast(self.dinosaur.dino_rect.x+ray_start_offset[0], self.dinosaur.dino_rect.y+ray_start_offset[1], an, RAY_LENGTH)
            if draw:
                ray.draw(SCREEN)
            first_obstacle = ray.find_first_obstacle(self.obstacles)

            vision[ii,:]  = ray.draw_intersection(SCREEN, first_obstacle, draw = draw, return_color = return_color)
        return vision

    def lose(self):
        print("Game Over! Your score was:", self.time)
        pygame.quit()


    def check_collision(self):
        for obstacle in self.obstacles:
            if self.dinosaur.dino_rect.colliderect(obstacle.rect):
                self.collision = True
                print("Collision detected with obstacle at position:", obstacle.rect.x)
                return True
        return False

    def generate_obstacle(self):
        # Randomly decide if we are adding an obstacle
        # Don't generate an obstacle too close to the last one
        if len(self.obstacles) > 0:
            return
        
        if random.random() > 0.85:
            return

        obstacle_type = random.choice(['small_cactus', 'large_cactus', 'bird'])
        if obstacle_type == 'small_cactus':
            obstacle = SmallCactus(self.screen_size[0])
        elif obstacle_type == 'large_cactus':
            obstacle = LargeCactus(self.screen_size[0])
        else:
            obstacle = Bird(self.screen_size[0])
        self.obstacles.append(obstacle)

class Background:
    def __init__(self):
        self.image = ASSETS['Track']
        self.x_pos = 0
        self.y_pos = 380
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.x_pos, self.y_pos))
        SCREEN.blit(self.image, (self.x_pos + self.width, self.y_pos))

    def update(self, game_speed):
        self.x_pos -= game_speed
        if self.x_pos <= -self.width:
            self.x_pos = 0

class Dinosaur:
    X_POS = 80
    Y_POS = 310
    Y_POS_DUCK = 340
    frames_per_image = 5  # Number of frames per image for running animation

    def __init__(self, gravity, jump_velocity):
        self.gravity = gravity
        self.jump_velocity = jump_velocity
        self.running_imgs = ASSETS['DinoRun']
        self.jumping_img = ASSETS['DinoJump']
        self.ducking_imgs = ASSETS['DinoDuck']
        
        self.state = 'run'  # Possible states: 'jumping', 'ducking', 'running'
        self.y_velocity = 0 
        self.step_index = 0
        self.dino_rect = self.running_imgs[0].get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS

        self.image = self.running_imgs[0]  # Initial image
        
    def update(self, userInput):
        if self.state == 'jumping':
            self.jump()
        elif userInput[pygame.K_UP] and self.dino_rect.y >= self.Y_POS:
            self.state = 'jumping'
            self.y_velocity = -self.jump_velocity
            self.image = self.jumping_img
        elif userInput[pygame.K_DOWN] and self.dino_rect.y >= self.Y_POS:
            self.state = 'ducking'
            self.duck()
        else:
            # If not jumping or ducking, determine if should run or stand up from duck
            if self.dino_rect.y == self.Y_POS_DUCK:
                # Stand up from duck
                self.dino_rect.y = self.Y_POS
                self.state = 'running'
                self.run()
            elif self.dino_rect.y == self.Y_POS:
                self.state = 'running'
                self.run()

        if self.step_index >= 2 * self.frames_per_image:
            self.step_index = 0

        # Update y position and velocity if jumping
        if self.state == 'jumping':
            self.dino_rect.y += self.y_velocity
            # Use a smoother velocity curve by reducing gravity as the dino rises, and increasing as it falls
            if self.y_velocity < 0:
                self.y_velocity += self.gravity * 0.6  # slower rise
            else:
                self.y_velocity += self.gravity * 1  # faster fall
            if self.dino_rect.y >= self.Y_POS:
                self.dino_rect.y = self.Y_POS
                self.y_velocity = 0
                self.state = 'running'
                self.run()

    def jump(self):
        self.image = self.jumping_img
        pass

    def duck(self):
        img_index = (self.step_index // self.frames_per_image) % len(self.ducking_imgs)
        self.image = self.ducking_imgs[img_index]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS_DUCK
        self.step_index += 1

    def run(self):
        img_index = (self.step_index // self.frames_per_image) % len(self.running_imgs)
        self.image = self.running_imgs[img_index]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.step_index += 1

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))


class Obstacle:
    def __init__(self, image, type, SCREEN_WIDTH):
        self.image = image
        self.type = type
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self, game_speed):
        self.rect.x -= game_speed

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)


class SmallCactus(Obstacle):
    image = ASSETS['CactusSmall']
    def __init__(self, SCREEN_WIDTH):
        self.type = 1
        super().__init__(self.image, self.type, SCREEN_WIDTH)
        self.rect.y = 325


class LargeCactus(Obstacle):
    image = ASSETS['CactusLarge']
    def __init__(self, SCREEN_WIDTH):
        self.type = 2
        super().__init__(self.image, self.type, SCREEN_WIDTH)
        self.rect.y = 300


class Bird(Obstacle):
    frames_per_image = 5  # Number of frames per image for running animation
    image = ASSETS['Bird']

    def __init__(self, SCREEN_WIDTH):
        self.type = 0
        super().__init__(self.image, self.type, SCREEN_WIDTH)
        self.rect.y = 250
        self.index = 0
        

    def draw(self, SCREEN):
        if self.index >= 2* self.frames_per_image:
            self.index = 0
        SCREEN.blit(self.image[self.index//self.frames_per_image], self.rect)
        self.index += 1



# Cast rays to simulate the dinosaur's vision
class RayCast():
    def __init__(self, x, y, angle, length):
        self.x = x
        self.y = y
        self.angle = angle
        self.length = length
    def cast(self):
        end_x = self.x + self.length * math.cos(self.angle)
        end_y = self.y + self.length * math.sin(self.angle)
        return (end_x, end_y)
    def draw(self, SCREEN):
        end_x, end_y = self.cast()
        pygame.draw.line(SCREEN, (255, 0, 0), (self.x, self.y), (end_x, end_y), 2)
        pygame.draw.line(SCREEN, (255, 0, 0), (self.x, self.y), (end_x, end_y), 2)
    def get_intersection_position(self, obstacle):
        # Calculate the intersection point between the ray and the obstacle (rectangle)
        ray_start = (self.x, self.y)
        ray_end = self.cast()
        rect = obstacle.rect

        # Define the four edges of the rectangle as line segments
        edges = [
            ((rect.left, rect.top), (rect.right, rect.top)),     # Top edge
            ((rect.right, rect.top), (rect.right, rect.bottom)), # Right edge
            ((rect.right, rect.bottom), (rect.left, rect.bottom)), # Bottom edge
            ((rect.left, rect.bottom), (rect.left, rect.top)),   # Left edge
        ]

        closest_intersection = None
        min_dist = float('inf')

        for edge_start, edge_end in edges:
            intersection = self.line_intersection(ray_start, ray_end, edge_start, edge_end)
            if intersection:
                dist = math.hypot(intersection[0] - self.x, intersection[1] - self.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_intersection = intersection

        return closest_intersection

    def line_intersection(self, p1, p2, q1, q2):
        # Returns the intersection point of line segments p1-p2 and q1-q2, or None if they don't intersect
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = q1
        x4, y4 = q2

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None  # Parallel lines

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            intersection_x = x1 + t * (x2 - x1)
            intersection_y = y1 + t * (y2 - y1)
            return (intersection_x, intersection_y)
        return None
    
    def attenuate(self, color, distance):
        # Attenuate the color based on the distance
        attenuation_factor = max(0, 1 - (distance / RAY_LENGTH))
        return tuple(int(c * attenuation_factor) for c in color)
    
    def draw_intersection(self, SCREEN, obstacle, draw = True, return_color = False):
        if obstacle is None:
            # If ray goes downwards, draw intersection at height 100
            if self.angle > 0:
                y_inter = 392
                x_inter = self.x + (y_inter - self.y) / math.tan(self.angle)
                intersection = (x_inter, y_inter)
                color = FLOOR_COLOR
            else:
                # If it goes upwards, draw intersection at the end of the ray
                intersection = self.cast()
                color = SKY_COLOR
                return color
        else:
            # If there is an obstacle, get the intersection position
            intersection = self.get_intersection_position(obstacle)
            if obstacle.type == 0:
                color = BIRD_COLOR
            else:
                color = OBSTACLE_COLOR

        print(color)
        if intersection and draw:
            pygame.draw.circle(SCREEN, (0, 255, 0), (int(intersection[0]), int(intersection[1])), 5)
        if return_color:
            print(color)
            return self.attenuate(color, math.hypot(intersection[0] - self.x, intersection[1] - self.y))


    def find_first_obstacle(self, obstacles):
        for obstacle in obstacles:
            intersection = self.get_intersection_position(obstacle)
            if intersection:
                dist = math.hypot(intersection[0] - self.x, intersection[1] - self.y)
                if dist < RAY_LENGTH:
                    return obstacle
        return None


def play_game():
    pygame.init()
    game = DinoGame()
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        userInput = pygame.key.get_pressed()
        game.update(userInput)
        game.render(show_rays=True,show_vision=True)
        clock.tick(30)

    pygame.quit()

play_game()