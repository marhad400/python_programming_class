from cannon import MovingCannon, ArtificialCannon
from targets import TargetMaster
from color import Color
from artist import Artist

import threading
import pygame
import time
import random

class ScoreTable:
    def __init__(self, targets_destroyed = 0, projectiles_used = 0):
        self.targets_destroyed = targets_destroyed
        self.projectiles_used = projectiles_used
        self.font = pygame.font.SysFont("dejavusansmono", 25)
    
    @property
    def score(self):
        return self.targets_destroyed - self.projectiles_used

    def draw(self, screen):
        Artist.draw_score(
            screen, 
            self.font, 
            self.targets_destroyed, self.projectiles_used, self.score,
            Color.RED, Color.WHITE
            )

class Manager:

    def __init__(self, num_targets):
        self.screen_size = (800, 600)
        self.init_pygame()
        self.init_clock()
        self.done = False

        self.init_cannons()

        self.score_t = ScoreTable()
        self.num_targets = num_targets
        self.bomb_spawning_thread = None
        self.start_bomb_thread()
        
        self.update_display()

    def init_pygame(self):
        pygame.display.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("The Gun of Khiryanov II")

    def update_display(self):
        pygame.display.flip()

    def init_clock(self):
        self.clock = pygame.time.Clock()
        self.refresh_rate = 15

    def init_cannons(self):
        self.user_cannon = MovingCannon(
            x = 30, y = self.screen_size[1]//2,
            color = Color.LIGHT_BLUE
        )

        self.artificial_cannon = ArtificialCannon(
            x = self.screen_size[0] - 30, y = self.screen_size[1]//2,
            color = Color.RED
        )

        self.target_master = TargetMaster()

    def process_states(self):
        self.screen.fill(Color.BLACK)

        self.handle_events()
        
        self.handle_angles()


        self.handle_cannon_movement()
        self.handle_target_movement()
        self.handle_bomb_movement()
        self.handle_projectile_movement()

        self.handle_dead_projectiles()

        self.handle_collisions()

        self.handle_new_missions()

        self.handle_drawing()

        self.update_display()
    
    def handle_angles(self):
        if pygame.mouse.get_focused():
            mouse_pos = pygame.mouse.get_pos()
            self.user_cannon.set_angle(mouse_pos)
        
        self.artificial_cannon.set_angle((self.user_cannon.x, self.user_cannon.y))

    def handle_cannon_movement(self):
        key_to_move = {
            pygame.K_LEFT: self.user_cannon.move_left,
            pygame.K_RIGHT: self.user_cannon.move_right,
            pygame.K_UP: self.user_cannon.move_up,
            pygame.K_DOWN: self.user_cannon.move_down,
            
            pygame.K_a: self.user_cannon.move_left,
            pygame.K_d: self.user_cannon.move_right,
            pygame.K_w: self.user_cannon.move_up,
            pygame.K_s: self.user_cannon.move_down
        }

        type_switcher = {
            pygame.K_1: 's',
            pygame.K_2: 'c',
            pygame.K_3: 't'
        }

        keys_pressed = pygame.key.get_pressed()
        for key, move_func in key_to_move.items():
            if keys_pressed[key]:
                move_func(self.screen_size)
        
        for key, chosen_type in type_switcher.items():
            if keys_pressed[key]:
                self.user_cannon.change_chosen(chosen_type)
        
        self.user_cannon.gain()

        if self.artificial_cannon.determine_move(self.user_cannon, self.screen_size):
            self.artificial_cannon.end_thread()
        else:
            self.artificial_cannon.start_thread()
        
        self.artificial_cannon.determine_target_spawning(
            self.target_master, self.screen_size, self.score_t.score, 0.05
            )

    def handle_target_movement(self):
        self.target_master.move_all(self.screen_size)

    def handle_projectile_movement(self):
        self.user_cannon.projectile_master.move_all(self.screen_size)
        self.artificial_cannon.projectile_master.move_all(self.screen_size)


    def handle_dead_projectiles(self):
        self.user_cannon.projectile_master.remove_dead()
        self.artificial_cannon.projectile_master.remove_dead()

    def handle_bomb_movement(self):
        for target in self.target_master.target_list:
            target.bomb_master.move_all()

    def handle_exploded_bombs(self):
        for target in self.target_master.target_list:
            target.bomb_master.remove_exploded()

    def handle_collisions(self):
        self.handle_target_collisions()
        self.handle_user_collision()
    
    def handle_target_collisions(self):
        for projectile in self.user_cannon.projectile_master.projectile_list:
            for target in self.target_master.target_list:
                if target.check_collision(projectile):
                    self.target_master.target_list.remove(target)
                    self.score_t.targets_destroyed += 1
                
    def handle_user_collision(self):
        for projectile in self.artificial_cannon.projectile_master.projectile_list:
            if self.user_cannon.check_collision(projectile):
                self.user_cannon.deal()

    def handle_drawing(self):
        self.draw_projectiles()
        self.draw_targets()
        self.draw_cannons()
        self.draw_bombs()
        self.draw_score()

    def draw_projectiles(self):
        self.user_cannon.projectile_master.draw_all(self.screen)
        self.artificial_cannon.projectile_master.draw_all(self.screen)

    def draw_targets(self):
        self.target_master.draw_all(self.screen)

    def draw_cannons(self):
        self.user_cannon.draw(self.screen)
        self.artificial_cannon.draw(self.screen)

    def draw_bombs(self):
        for target in self.target_master.target_list:
            target.bomb_master.draw_all(self.screen)

    def draw_score(self):
        self.score_t.draw(self.screen)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.user_cannon.activate()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.user_cannon.strike()
                    self.score_t.projectiles_used += 1

    def handle_new_missions(self):
        if not self.target_master.target_list and not self.user_cannon.projectile_master.projectile_list:
            self.create_mission()

    def create_mission(self):
        for _ in range(self.num_targets):
            self.target_master.create_random_target(
                self.screen_size,
                self.target_master.calculate_target_size(self.score_t.score),
            )
    
    def start_bomb_thread(self):
        if not self.bomb_spawning_thread:
            self.bomb_spawning_thread = threading.Thread(
                target=self.spawn_bombs, daemon=True
                )
            self.bomb_spawning_thread.start()
    
    def spawn_bombs(self):
        while self.bomb_spawning_thread:
            time.sleep(0.5)

            if self.bomb_spawning_thread:
                random.shuffle(self.target_master.target_list)
                
                for target in self.target_master.target_list:
                    time.sleep(0.1)
                    
                    target.bomb_master.create_bomb(
                        target.x, target.y + target.size, 5, 0.8
                    )

        
    def end_bomb_thread(self):
        self.bomb_spawning_thread = None

    def game_loop(self):
        while not self.done:
            self.clock.tick(self.refresh_rate)

            self.process_states()

m = Manager(num_targets=10)
m.game_loop()