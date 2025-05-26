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
    def __init__(self, show_screen=True):
        self.time = 0 
        self.game_speed = 30
        self.jump_velocity = 20
        self.gravity = 2
        self.screen_size = (1100, 600)
        self.dinosaur = Dinosaur(self.gravity, self.jump_velocity)
        self.background = Background()
        self.obstacles = []
        if show_screen:
            self.SCREEN = pygame.display.set_mode(self.screen_size)
        else:
            self.SCREEN = pygame.Surface((self.screen_size[0], self.screen_size[1]))
        self.done = False
        self.collision = False
        self.observation_mode = 'easy'
        self.max_time = 10000

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
        """font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.time}', True, (0, 0, 0))
        self.SCREEN.blit(score_text, (10, 10))"""
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
        if self.time >= self.max_time:
            self.done = True
        self.time += 1

    def reward(self):
        # Initialize storage for passed obstacles if not already present
        if not hasattr(self, 'passed_obstacles'):
            self.passed_obstacles = set()
        if not hasattr(self, 'passed_types'):
            self.passed_types = set()

        # Check for newly passed obstacles
        reward = 0.01

        return reward
            
    def get_observation(self):
        #vision = self.get_vision(self.SCREEN, draw=False, return_color=True)
        if self.observation_mode == 'easy':
            # Return distance to the first obstacle in front of the dinosaur, type of obstacle, flag for ducking, and height of the dinosaur
            first_obstacle = None
            for obstacle in self.obstacles:
                if obstacle.rect.x > self.dinosaur.dino_rect.x:
                    first_obstacle = obstacle
                    break
            if first_obstacle is not None:
                distance = first_obstacle.rect.x
                obstacle_type = first_obstacle.type
            ducking = 1 if self.dinosaur.state == 'ducking' else 0
            height = self.dinosaur.dino_rect.y

            observation = np.array([distance if first_obstacle is not None else -1])
        return observation

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
                return True
        return False

    def generate_obstacle(self):
        # Randomly decide if we are adding an obstacle
        # Don't generate an obstacle too close to the last one
        if len(self.obstacles) > 0:
            return
        
        if random.random() > 0.85:
            return

        obstacle_type = random.choice(['small_cactus'])
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

#play_game()

class GymEnv_Dino:
    def __init__(self, game):
        self.game = game
        self.action_space = [pygame.K_UP, pygame.K_DOWN]
        self.observation_space = np.zeros((N_RAYS, 3), dtype=np.float32)

    def reset(self):
        self.game.reset()
        return self.game.get_observation()

    def step(self, action):
        userInput = {pygame.K_UP: False,
                      pygame.K_DOWN: False}
        if action == 0:  # Jump
            userInput[pygame.K_UP] = True
        elif action == 1:  # Duck
            userInput[pygame.K_DOWN] = True
        self.game.update(userInput)
        observation = self.game.get_observation()
        reward = self.game.reward()
        done = self.game.done
        return observation, reward, done, {}

    def render(self):
        self.game.render(show_rays=False, show_vision=False)

    def close(self):
        pygame.quit()


import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque



# Q-Network
class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )

    def forward(self, x):
        return self.fc(x)


def train_dqn(env, episodes=100, gamma=0.99, lr=1e-3, epsilon_decay=0.995,
              epsilon_min=0.05, batch_size=256, memory_size=10000, target_update=10):
    
    input_dim = env.reset().shape[0]
    output_dim = 2  # actions: 0 (jump), 1 (duck)

    policy_net = DQN(input_dim, output_dim)
    target_net = DQN(input_dim, output_dim)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=lr)
    memory = deque(maxlen=memory_size)

    epsilon = 1.0

    for episode in range(episodes):
        obs = env.reset()
        total_reward = 0
        done = False

        while not done:
            if random.random() < epsilon:
                action = random.randint(0, 1)
            else:
                with torch.no_grad():
                    q_values = policy_net(torch.tensor(obs).float().unsqueeze(0))
                    action = torch.argmax(q_values).item()

            next_obs, reward, done, _ = env.step(action)
            memory.append((obs, action, reward, next_obs, done))
            obs = next_obs
            total_reward += reward

            # Sample and train
            if len(memory) >= batch_size:
                batch = random.sample(memory, batch_size)
                obs_batch, act_batch, rew_batch, next_batch, done_batch = zip(*batch)

                obs_batch = torch.tensor(obs_batch, dtype=torch.float32)
                act_batch = torch.tensor(act_batch, dtype=torch.int64).unsqueeze(1)
                rew_batch = torch.tensor(rew_batch, dtype=torch.float32).unsqueeze(1)
                next_batch = torch.tensor(next_batch, dtype=torch.float32)
                done_batch = torch.tensor(done_batch, dtype=torch.float32).unsqueeze(1)

                current_q = policy_net(obs_batch).gather(1, act_batch)
                max_next_q = target_net(next_batch).max(1)[0].unsqueeze(1)
                expected_q = rew_batch + gamma * max_next_q * (1 - done_batch)

                loss = nn.MSELoss()(current_q, expected_q)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        if episode % target_update == 0:
            target_net.load_state_dict(policy_net.state_dict())

        epsilon = max(epsilon_min, epsilon * epsilon_decay)
        print(f"Episode {episode}, Total Reward: {total_reward}, Epsilon: {epsilon:.3f}")

    return policy_net


def play(env, model, episodes=5):
    pygame.init()
    for ep in range(episodes):
        rewards = 0
        obs = env.reset()
        done = False
        while not done:
            action = model(torch.tensor(obs).float().unsqueeze(0)).argmax().item()
            obs, reward, done, _ = env.step(action)
            print(obs)
            rewards += reward
            env.render()
            pygame.display.flip()
            pygame.time.delay(30)

        print(f"Episode {ep + 1}, Total Reward: {rewards}")


# Initialize pygame screen and game
#import pygame
game = DinoGame(show_screen=False)
env = GymEnv_Dino(game)

# Train the model
trained_model = train_dqn(env)

game = DinoGame(show_screen=True)
env = GymEnv_Dino(game)

# Play with the trained model
play(env, trained_model)

# Quit pygame after playing
env.close()
