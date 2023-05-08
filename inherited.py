from abstract import Drawable, Killable, Moveable
from color import Color

from artist import Artist

import random

class GameObject(Moveable, Drawable):
    def __init__(self): pass

class Target(Drawable, Killable):
    def __init__(self, x, y, color = None, size = None, health = None, shape = None):
        color = color or Color.rand_color()
        size = size or 5
        health = health or 1
        shape = shape or 'c'
        
        Drawable.__init__(self, x=x, y=y, color=color, size=size)
        Killable.__init__(self, health=health)
        self.shape = shape
    
    def draw(self, s):
        Artist.draw(s, self.x, self.y, self.shape, self.color, self.size)
    
    def check_collision(self, ball):
        dist = sum([(self.x - ball.coord[0])**2, (self.y - ball.coord[1])**2])**0.5
        min_dist = self.size + ball.rad
        return dist <= min_dist

    def __str__(self):
        return f"Static Target of Shape({self.shape}), " \
                f"Pos({self.x}, {self.y}), " \
                f"Color({self.color}), Size({self.size}), Health({self.health})"
            
    def __repr__(self):
        return self.__str__()

class MovingTarget(Moveable, Target):
    def __init__(self, x, y, v_x = None, v_y = None, color = None, size = None, health = None, shape = None):
        v_x = random.randint(-2, 2)
        v_y = random.randint(-2, 2)
        color = color or Color.rand_color()
        size = size or 30
        health = health or 1

        Moveable.__init__(self, v_x, v_y)
        Target.__init__(self, x, y, color, size, health, shape)
    
    def move(self):
        self.x += self.v_x
        self.y += self.v_y
    
    def __str__(self):
        return f"Moving Target of Shape({self.shape}), " \
                f"Pos({self.x}, {self.y}), " \
                f"Color({self.color}), Size({self.size}), Health({self.health}), " \
                f"Speed({self.v_x}, {self.v_y})"
    
    def __repr__(self):
        return self.__str__()

class Projectile(Drawable, Killable, Moveable):
    def __init__(self, x, y, v_x, v_y, color, size, health, shape):
        color = color or Color.rand_color()
        size = size or 5
        health = health or 1
        shape = shape or 'c'

        Drawable.__init__(self, x, y, color=color, size=size)
        Killable.__init__(self, health=health)
        Moveable.__init__(self, v_x, v_y)
        self.shape = shape