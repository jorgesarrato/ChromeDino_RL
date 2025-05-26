"""
Python implementation of Chrome's Dino Run game.
"""

import pygame
import random
import os

class DinoGame:
    def __init__(self):
        self.time = 0 
        self.score = 0
        self.game_speed = 8
        self.jump_velocity = 26
        self.gravity = 2
        self.screen_size = (800, 600)
        self.dinosaur = Dinosaur(self.gravity, self.jump_velocity)
        self.background = Background()
        self.obstacles = []
        self.SCREEN = pygame.display.set_mode(self.screen_size)

    def reset(self):
        pass

    def render(self):
        self.SCREEN.fill((255, 255, 255))
        self.background.draw(self.SCREEN)
        self.dinosaur.draw(self.SCREEN)
        for obstacle in self.obstacles:
            print("Drawing obstacle at position:", obstacle.rect.x)
            obstacle.draw(self.SCREEN)

    def update(self, userInput):
        self.background.update(self.game_speed)
        self.dinosaur.update(userInput)
        for obstacle in self.obstacles:
            obstacle.update(self.game_speed)
            if obstacle.rect.x < -obstacle.rect.width:
                self.obstacles.remove(obstacle)
        self.generate_obstacle()

    def get_observation(self):
        pass

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
        self.image = pygame.image.load(os.path.join("Assets/Other", "Track.png"))
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
        self.running_imgs = [pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
                            pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png"))]
        self.jumping_img = pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png"))
        self.ducking_imgs = [pygame.image.load(os.path.join("Assets/Dino", "DinoDuck1.png")),
           pygame.image.load(os.path.join("Assets/Dino", "DinoDuck2.png"))]
        
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
            self.y_velocity += self.gravity
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
    image = [pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png"))]
    def __init__(self, SCREEN_WIDTH):
        self.type = 1
        super().__init__(self.image, self.type, SCREEN_WIDTH)
        self.rect.y = 325


class LargeCactus(Obstacle):
    image = [pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png"))]
    def __init__(self, SCREEN_WIDTH):
        self.type = 2
        super().__init__(self.image, self.type, SCREEN_WIDTH)
        self.rect.y = 300


class Bird(Obstacle):
    frames_per_image = 5  # Number of frames per image for running animation
    image = [pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
        pygame.image.load(os.path.join("Assets/Bird", "Bird2.png"))]

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
        game.render()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

play_game()