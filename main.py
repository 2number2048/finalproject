from pygame import *
from random import randint
import math # Add this at the top of your file

window_width = 1372
window_height = 1400
window = display.set_mode((window_width, window_height))
display.set_caption('System Defense')
background = transform.scale(image.load('windowdesktop.jpg'), (window_width, window_height))


run = True
FPS = 60
clock = time.Clock()
finish = False

class SystemSprite(sprite.Sprite):
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        super().__init__()
        self.image = transform.scale(image.load(player_image), (size_x, size_y))
        self.speed = player_speed
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y
    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))

class Antivirus(SystemSprite):
    def update(self):
        keys = key.get_pressed()
        if keys[K_a] and self.rect.x > 5:
            self.rect.x -= self.speed
        if keys[K_d] and self.rect.x < window_width - 80:
            self.rect.x += self.speed
        if keys[K_w] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_s] and self.rect.y < window_height - 80:
            self.rect.y += self.speed

class Core(SystemSprite):
    def __init__(self, player_image, player_x, player_y, player_speed):
        super().__init__(player_image, player_x, player_y, player_speed)
        self.health = 100
        self.image = transform.scale(image.load(player_image), (125, 125)) # Make the core larger
    def update(self):
        pass # Core doesn't move, but you can add health-related logic here if needed
        

class Virus(SystemSprite):
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        super().__init__(player_image, player_x, player_y, size_x, size_y, player_speed)
        # Store the position as floats for smoother movement
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

    def update(self, target_x, target_y):
        # 1. Calculate the distance to the player
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        distance = math.hypot(dx, dy)

        if distance != 0:
            # 2. Normalize the direction (make the total vector length 1)
            dx /= distance
            dy /= distance

            # 3. Move the virus toward the player based on speed
            self.pos_x += dx * self.speed
            self.pos_y += dy * self.speed

            # 4. Update the actual rectangle position
            self.rect.x = int(self.pos_x)
            self.rect.y = int(self.pos_y)
def spawn_virus():
    side = randint(1, 4)
    if side == 1: # Top
        x = randint(0, window_width)
        y = -70
    elif side == 2: # Bottom
        x = randint(0, window_width)
        y = window_height + 70
    elif side == 3: # Left
        x = -70
        y = randint(0, window_height)
    else: # Right
        x = window_width + 70
        y = randint(0, window_height)
    
    return Virus('virus1.png', x, y, 65, 65, randint(2, 4))

# Create a group to manage multiple viruses
viruses = sprite.Group()
for i in range(5): # Start with 5 viruses
    viruses.add(spawn_virus())


antivirus = Antivirus('antivirus.png', 686, 386, 65, 65, 5)
core = SystemSprite('core.png', 625, 450, 125, 125, 0)

    
while run:
    for e in event.get():
        if e.type == QUIT:
            run = False

    if not finish:
        window.blit(background, (0, 0))
        
        # Update and Draw Antivirus
        antivirus.update()
        antivirus.reset()
        core.reset() # Draw the core (it doesn't move, so we just reset it)

        # Update and Draw all Viruses
        for v in viruses:
            # Pass the antivirus center coordinates to each virus
            v.update(antivirus.rect.centerx, antivirus.rect.centery)
            v.reset()

        # Optional: Check for collisions
        if sprite.spritecollide(antivirus, viruses, False):
            print("System Compromised!")
            # finish = True 

    display.update()
    clock.tick(FPS)
