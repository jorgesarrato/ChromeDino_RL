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
        self.jump_velocity = 20
        self.gravity = 2
        self.screen_size = (800, 600)
        self.dinosaur = Dinosaur(self.gravity, self.jump_velocity)
        self.obstacles = []
        self.SCREEN = pygame.display.set_mode(self.screen_size)
    def reset(self):
        pass
    def render(self):
        self.dinosaur.draw(self.SCREEN)
    def update(self):
        pass
    def get_obsercation(self):
        pass
    def generate_obstacle(self):
        pass

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
        game.dinosaur.update(userInput)
        
        game.SCREEN.fill((255, 255, 255))
        game.render()
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

play_game()