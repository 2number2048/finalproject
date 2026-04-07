from pygame import *
from random import randint

window_width = 1372
window_height = 772
window = display.set_mode((window_width, window_height))
display.set_caption('System Defense')
background = transform.scale(image.load('windowdesktop.jpg'), (window_width, window_height))


run = True
FPS = 60
clock = time.Clock()
finish = False

class SystemSprite(sprite.Sprite):
    def __init__(self, player_image, player_x, player_y, player_speed):
        super().__init__()
        self.image = transform.scale(image.load(player_image), (65, 65))
        self.speed = player_speed
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y
    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))

class Antivirus(SystemSprite):
    def update(self):
        keys = key.get_pressed()
        if keys[K_LEFT] and self.rect.x > 5:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < window_width - 80:
            self.rect.x += self.speed
        if keys[K_UP] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_DOWN] and self.rect.y < window_height - 80:
            self.rect.y += self.speed

antivirus = Antivirus('antivirus.png', 686, 386, 5)
    

while run:
    for e in event.get():
        if e.type == QUIT:
            run = False

    window.blit(background, (0, 0))
    antivirus.update()
    antivirus.reset()


    display.update()
    clock.tick(FPS)
