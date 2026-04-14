from pygame import *
from random import randint
import math

# --- Setup ---
window_width = 1372
window_height = 1000 # Adjusted height for standard monitors
window = display.set_mode((window_width, window_height))
display.set_caption('System Defense')

# Colors & Fonts
font.init()
font_main = font.SysFont('Arial', 80, bold=True)
font_sub = font.SysFont('Arial', 40)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
BLACK = (0, 0, 0)

# Load images (ensure these files exist)
background = transform.scale(image.load('windowdesktop.jpg'), (window_width, window_height))

# --- Classes ---
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
        if keys[K_a] and self.rect.x > 5: self.rect.x -= self.speed
        if keys[K_d] and self.rect.x < window_width - 70: self.rect.x += self.speed
        if keys[K_w] and self.rect.y > 5: self.rect.y -= self.speed
        if keys[K_s] and self.rect.y < window_height - 70: self.rect.y += self.speed

class Virus(SystemSprite):
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed):
        super().__init__(player_image, player_x, player_y, size_x, size_y, player_speed)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

    def update(self, target_x, target_y):
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        distance = math.hypot(dx, dy)
        if distance != 0:
            dx /= distance
            dy /= distance
            self.pos_x += dx * self.speed
            self.pos_y += dy * self.speed
            self.rect.x = int(self.pos_x)
            self.rect.y = int(self.pos_y)

def spawn_virus():
    side = randint(1, 4)
    x, y = 0, 0
    if side == 1: x, y = randint(0, window_width), -70
    elif side == 2: x, y = randint(0, window_width), window_height + 70
    elif side == 3: x, y = -70, randint(0, window_height)
    else: x, y = window_width + 70, randint(0, window_height)
    return Virus('virus1.png', x, y, 65, 65, randint(2, 4))

# --- Game Objects ---
antivirus = Antivirus('antivirus.png', 686, 386, 65, 65, 7)
core = SystemSprite('core.png', 625, 450, 125, 125, 0)
viruses = sprite.Group()
for i in range(5):
    viruses.add(spawn_virus())

# --- Game States ---
MENU = 0
GAME = 1
state = MENU

run = True
FPS = 60
clock = time.Clock()

start_rect = Rect(0, 0, 0, 0)

while run:
    # 1. Event Handling
    mouse_pos = mouse.get_pos()
    for e in event.get():
        if e.type == QUIT:
            run = False
        if e.type == MOUSEBUTTONDOWN and state == MENU:
            # Check if "START" button is clicked
            if start_rect.collidepoint(mouse_pos):
                state = GAME

    # 2. Logic & Drawing
    if state == MENU:
        window.fill(BLACK) # Dark cyber feel
        
        # Draw Title
        title = font_main.render("SYSTEM DEFENSE", True, CYAN)
        window.blit(title, (window_width//2 - title.get_width()//2, 300))
        
        # Draw Button
        start_text = "INITIALIZE SYSTEM"
        # Make button glow if hovered
        color = CYAN if start_rect.collidepoint(mouse_pos) else WHITE
        btn_render = font_sub.render(start_text, True, color)
        start_rect = btn_render.get_rect(center=(window_width//2, 550))
        
        window.blit(btn_render, start_rect)

    elif state == GAME:
        window.blit(background, (0, 0))
        
        antivirus.update()
        antivirus.reset()
        core.reset()

        for v in viruses:
            v.update(antivirus.rect.centerx, antivirus.rect.centery)
            v.reset()

        if sprite.spritecollide(antivirus, viruses, False):
            # You can add logic for losing here
            pass

    display.update()
    clock.tick(FPS)