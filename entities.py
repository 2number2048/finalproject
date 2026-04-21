from pygame import *
from random import randint, uniform
import math

class SystemSprite(sprite.Sprite):
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        super().__init__()
        self.image = transform.scale(image.load(player_image), (size_x, size_y))
        self.speed = player_speed
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y

    def reset(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

class Antivirus(SystemSprite):
    def update(self):
        keys = key.get_pressed()
        if keys[K_a] and self.rect.x > 5: self.rect.x -= self.speed
        if keys[K_d] and self.rect.x < display.get_window_size()[0] - 70: self.rect.x += self.speed
        if keys[K_w] and self.rect.y > 5: self.rect.y -= self.speed
        if keys[K_s] and self.rect.y < display.get_window_size()[1] - 70: self.rect.y += self.speed

class Virus(SystemSprite):
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        super().__init__(player_image, player_x, player_y, size_x, size_y, player_speed)
        # position tracked as center
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)
        ang = math.radians(randint(0, 359))
        self.vx = math.cos(ang) * self.speed
        self.vy = math.sin(ang) * self.speed
        self.homing_strength = uniform(0.06, 0.18)
        self.jitter = uniform(0.6, 1.8)
        self.turn_noise_prob = uniform(0.04, 0.12)
        self.is_boss = False

    def update(self, target_x, target_y):
        dx = target_x - self.pos_x
        dy = target_y - self.pos_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        desired_x = dx / dist
        desired_y = dy / dist
        rx = uniform(-1.0, 1.0) * self.jitter
        ry = uniform(-1.0, 1.0) * self.jitter
        new_vx = self.vx + desired_x * (self.homing_strength * self.speed) + rx
        new_vy = self.vy + desired_y * (self.homing_strength * self.speed) + ry
        if uniform(0.0, 1.0) < self.turn_noise_prob:
            turn_ang = math.radians(uniform(-60, 60))
            cos_t = math.cos(turn_ang)
            sin_t = math.sin(turn_ang)
            tvx = new_vx * cos_t - new_vy * sin_t
            tvy = new_vx * sin_t + new_vy * cos_t
            new_vx, new_vy = tvx, tvy
        mag = math.hypot(new_vx, new_vy)
        if mag != 0:
            self.vx = new_vx / mag * self.speed
            self.vy = new_vy / mag * self.speed
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

    def reset(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

class Bullet(sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, speed=15, color=(0,255,0), radius=6):
        super().__init__()
        self.radius = radius
        self.color = color
        self.pos_x = float(x)
        self.pos_y = float(y)
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self.vx = 0
            self.vy = 0
        else:
            self.vx = dx / dist * speed
            self.vy = dy / dist * speed
        self.rect = Rect(int(self.pos_x - radius), int(self.pos_y - radius), radius*2, radius*2)

    def update(self):
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.x = int(self.pos_x - self.radius)
        self.rect.y = int(self.pos_y - self.radius)

    def reset(self, surface):
        draw.circle(surface, self.color, (int(self.pos_x), int(self.pos_y)), self.radius)

class Boss(Virus):
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed, hp):
        super().__init__(player_image, player_x, player_y, size_x, size_y, player_speed)
        self.hp = hp
        self.max_hp = hp
        self.is_boss = True

    def reset(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))
        bar_w = max(40, self.rect.width)
        bar_h = 8
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.top - bar_h - 6
        draw.rect(surface, (80, 0, 0), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        fill_w = int(bar_w * max(0, min(self.hp / self.max_hp, 1.0)))
        draw.rect(surface, (200, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        draw.rect(surface, (0, 200, 0), (bar_x, bar_y, fill_w, bar_h))


def spawn_virus(speed_min, speed_max, window_width, window_height):
    side = randint(1, 4)
    x, y = 0, 0
    if side == 1: x, y = randint(0, window_width), -70
    elif side == 2: x, y = randint(0, window_width), window_height + 70
    elif side == 3: x, y = -70, randint(0, window_height)
    else: x, y = window_width + 70, randint(0, window_height)
    return Virus('virus1.png', x, y, 65, 65, randint(speed_min, speed_max))


def spawn_boss(level, speed_min, speed_max, window_width, window_height):
    side = randint(1, 4)
    if side == 1:
        x, y = randint(0, window_width), -150
    elif side == 2:
        x, y = randint(0, window_width), window_height + 150
    elif side == 3:
        x, y = -150, randint(0, window_height)
    else:
        x, y = window_width + 150, randint(0, window_height)
    boss_size = 140
    boss_speed = max(1, speed_min - 1)
    boss_hp = 6 + level * 4
    return Boss('virus1.png', x, y, boss_size, boss_size, boss_speed, boss_hp)
