from pygame import *
# initialize pygame modules
init()
from random import randint, uniform
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

# default virus speed range (can be increased by level logic later)
VIRUS_SPEED_MIN = 2
VIRUS_SPEED_MAX = 4

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
        # position tracked as center
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        # initial velocity (random direction)
        ang = math.radians(randint(0, 359))
        self.vx = math.cos(ang) * self.speed
        self.vy = math.sin(ang) * self.speed

        # steering parameters (per-virus randomized slightly)
        self.homing_strength = uniform(0.06, 0.18)  # how strongly it steers toward the core each frame
        self.jitter = uniform(0.6, 1.8)            # randomness multiplier
        self.turn_noise_prob = uniform(0.04, 0.12) # small chance per frame to apply a random turn

    def update(self, target_x, target_y):
        # steering toward target
        dx = target_x - self.pos_x
        dy = target_y - self.pos_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return

        desired_x = dx / dist
        desired_y = dy / dist

        # random jitter vector
        rx = uniform(-1.0, 1.0) * self.jitter
        ry = uniform(-1.0, 1.0) * self.jitter

        # combine current velocity, homing pull, and random jitter
        new_vx = self.vx + desired_x * (self.homing_strength * self.speed) + rx
        new_vy = self.vy + desired_y * (self.homing_strength * self.speed) + ry

        # occasionally apply a stronger random turn
        if uniform(0.0, 1.0) < self.turn_noise_prob:
            turn_ang = math.radians(uniform(-60, 60))
            cos_t = math.cos(turn_ang)
            sin_t = math.sin(turn_ang)
            tvx = new_vx * cos_t - new_vy * sin_t
            tvy = new_vx * sin_t + new_vy * cos_t
            new_vx, new_vy = tvx, tvy

        # normalize to maintain speed magnitude
        mag = math.hypot(new_vx, new_vy)
        if mag != 0:
            self.vx = new_vx / mag * self.speed
            self.vy = new_vy / mag * self.speed

        # update position
        self.pos_x += self.vx
        self.pos_y += self.vy

        # write back to rect (center)
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)


class Bullet(sprite.Sprite):
    """Simple bullet that travels toward a target and can hit viruses."""
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
        # rect used for collision detection
        self.rect = Rect(int(self.pos_x - radius), int(self.pos_y - radius), radius*2, radius*2)

    def update(self):
        self.pos_x += self.vx
        self.pos_y += self.vy
        self.rect.x = int(self.pos_x - self.radius)
        self.rect.y = int(self.pos_y - self.radius)

    def reset(self):
        draw.circle(window, self.color, (int(self.pos_x), int(self.pos_y)), self.radius)


class Boss(Virus):
    """A boss variant that has HP and a larger sprite."""
    def __init__(self, player_image, player_x, player_y, size_x, size_y, player_speed, hp):
        # call Virus init to set up movement
        super().__init__(player_image, player_x, player_y, size_x, size_y, player_speed)
        self.hp = hp
        self.max_hp = hp
        self.is_boss = True

    def reset(self):
        # draw the boss image
        window.blit(self.image, (self.rect.x, self.rect.y))
        # draw a small HP bar above the boss
        bar_w = max(40, self.rect.width)
        bar_h = 8
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.top - bar_h - 6
        draw.rect(window, (80, 0, 0), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        fill_w = int(bar_w * max(0, min(self.hp / self.max_hp, 1.0)))
        draw.rect(window, (200, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        draw.rect(window, (0, 200, 0), (bar_x, bar_y, fill_w, bar_h))

def spawn_virus():
    side = randint(1, 4)
    x, y = 0, 0
    if side == 1: x, y = randint(0, window_width), -70
    elif side == 2: x, y = randint(0, window_width), window_height + 70
    elif side == 3: x, y = -70, randint(0, window_height)
    else: x, y = window_width + 70, randint(0, window_height)
    # choose speed based on current level range
    speed = randint(VIRUS_SPEED_MIN, VIRUS_SPEED_MAX)
    return Virus('virus1.png', x, y, 65, 65, speed)


def spawn_boss():
    # spawn the boss from a random side
    side = randint(1, 4)
    if side == 1:
        x, y = randint(0, window_width), -150
    elif side == 2:
        x, y = randint(0, window_width), window_height + 150
    elif side == 3:
        x, y = -150, randint(0, window_height)
    else:
        x, y = window_width + 150, randint(0, window_height)
    # boss stats scale with level
    boss_size = 140
    # make boss a bit slower than regular viruses
    boss_speed = max(1, VIRUS_SPEED_MIN - 1)
    boss_hp = 6 + LEVEL * 4
    b = Boss('virus1.png', x, y, boss_size, boss_size, boss_speed, boss_hp)
    return b

# --- Game Objects ---
antivirus = Antivirus('antivirus.png', 686, 386, 65, 65, 7)
core = SystemSprite('core.png', 625, 450, 125, 125, 0)
viruses = sprite.Group()
for i in range(5):
    viruses.add(spawn_virus())
# group for bullets fired by the antivirus
bullets = sprite.Group()

# Core health
CORE_MAX_HP = 100
core_hp = CORE_MAX_HP
DAMAGE_PER_HIT = 10
# HP bar layout
HP_BAR_POS = (20, 20)
HP_BAR_SIZE = (300, 24)

# Timer & high-score
HIGH_SCORE_FILE = 'highscore.txt'

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            return float(f.read().strip())
    except Exception:
        return 0.0

def save_high_score(value):
    try:
        with open(HIGH_SCORE_FILE, 'w') as f:
            f.write(str(float(value)))
    except Exception:
        pass

game_start_ticks = None
elapsed_seconds = 0.0
high_score = load_high_score()

# Virus spawn configuration: spawn every N milliseconds while below a cap
VIRUS_SPAWN_INTERVAL_MS = 1200  # spawn interval in milliseconds
MAX_VIRUSES = 40
SPAWN_EVENT = USEREVENT + 1
# Start a repeating timer that posts SPAWN_EVENT every VIRUS_SPAWN_INTERVAL_MS
time.set_timer(SPAWN_EVENT, VIRUS_SPAWN_INTERVAL_MS)

# Level system
LEVEL = 1
ENEMIES_BASE = 10
ENEMIES_INCREMENT = 15
def enemies_for_level(l):
    return ENEMIES_BASE + (l-1) * ENEMIES_INCREMENT
level_total_enemies = enemies_for_level(LEVEL)
level_spawned = 0

# Boss & combat tuning
boss_active = False
boss_spawned = False
BULLET_DAMAGE = 1

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
                # reset core HP and groups when starting a new game
                core_hp = CORE_MAX_HP
                viruses.empty()
                bullets.empty()
                # reset level to 1
                LEVEL = 1
                level_total_enemies = enemies_for_level(LEVEL)
                level_spawned = 0
                # reset difficulty ranges
                VIRUS_SPEED_MIN = 2
                VIRUS_SPEED_MAX = 4
                MAX_VIRUSES = 40
                VIRUS_SPAWN_INTERVAL_MS = 1200
                # restart spawn timer
                time.set_timer(SPAWN_EVENT, VIRUS_SPAWN_INTERVAL_MS)
                # spawn an initial small batch (counts toward level spawn)
                initial = min(5, level_total_enemies)
                for i in range(initial):
                    viruses.add(spawn_virus())
                level_spawned = initial
                # start timer for this run
                game_start_ticks = time.get_ticks()
                elapsed_seconds = 0.0
        # Shooting: left mouse click spawns a bullet when in GAME
        if e.type == MOUSEBUTTONDOWN and state == GAME:
            bx, by = antivirus.rect.centerx, antivirus.rect.centery
            tx, ty = mouse_pos
            bullets.add(Bullet(bx, by, tx, ty, speed=18, color=CYAN, radius=6))
        # Timer-based spawn event
        if e.type == SPAWN_EVENT and state == GAME:
            # only spawn while we haven't spawned the total for this level
            if level_spawned < level_total_enemies and len(viruses) < MAX_VIRUSES:
                viruses.add(spawn_virus())
                level_spawned += 1
                print(f"[spawn] virus spawned (level {LEVEL}) spawned_for_level={level_spawned}/{level_total_enemies} total_active={len(viruses)}")

    # 2. Logic & Drawing
    if state == MENU:
        window.fill(BLACK) # Dark cyber feel
        
        # Draw Title
        title = font_main.render("SYSTEM DEFENSE", True, CYAN)
        window.blit(title, (window_width//2 - title.get_width()//2, 300))
        # High score display
        hs_text = font_sub.render(f"HIGH SCORE: {int(high_score)}s", True, WHITE)
        window.blit(hs_text, (window_width//2 - hs_text.get_width()//2, 380))

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

        # Draw core HP bar
        hp_x, hp_y = HP_BAR_POS
        hp_w, hp_h = HP_BAR_SIZE
        # background
        draw.rect(window, (50,50,50), (hp_x - 2, hp_y - 2, hp_w + 4, hp_h + 4))
        # empty bar
        draw.rect(window, (100, 0, 0), (hp_x, hp_y, hp_w, hp_h))
        # filled portion
        if core_hp > 0:
            filled_w = int(hp_w * max(0, min(core_hp / CORE_MAX_HP, 1.0)))
            draw.rect(window, (0, 200, 0), (hp_x, hp_y, filled_w, hp_h))
        # HP text
        hp_text = font_sub.render(f"CORE HP: {core_hp}/{CORE_MAX_HP}", True, WHITE)
        window.blit(hp_text, (hp_x, hp_y + hp_h + 6))

        # Draw run timer (seconds survived)
        if game_start_ticks is not None:
            elapsed_seconds = (time.get_ticks() - game_start_ticks) / 1000.0
        else:
            elapsed_seconds = 0.0
        timer_text = font_sub.render(f"TIME: {int(elapsed_seconds)}s", True, WHITE)
        window.blit(timer_text, (window_width - timer_text.get_width() - 20, 20))

        # Update viruses toward the core
        for v in viruses:
            v.update(core.rect.centerx, core.rect.centery)
            v.reset()

        # Draw current level
        level_text = font_sub.render(f"LEVEL {LEVEL}", True, WHITE)
        window.blit(level_text, (window_width//2 - level_text.get_width()//2, 100))

        # Check for viruses reaching the core
        core_hits = sprite.spritecollide(core, viruses, True)
        if core_hits:
            # If any of the colliding sprites is a boss, instant loss
            boss_touch = any(getattr(v, 'is_boss', False) for v in core_hits)
            if boss_touch:
                core_hp = 0
                print("Boss reached core - instant loss")
                # stop spawning and clear entities
                time.set_timer(SPAWN_EVENT, 0)
                viruses.empty()
                bullets.empty()
                # compute final time and update high score
                final_secs = 0.0
                if game_start_ticks is not None:
                    final_secs = (time.get_ticks() - game_start_ticks) / 1000.0
                if final_secs > high_score:
                    high_score = final_secs
                    save_high_score(high_score)
                    print(f"New high score: {high_score:.1f}s")
                game_start_ticks = None
                state = MENU
            else:
                core_hp -= DAMAGE_PER_HIT * len(core_hits)
                print(f"[core] hit by {len(core_hits)} virus(es); HP={core_hp}")
                if core_hp <= 0:
                    core_hp = 0
                    print("Core destroyed - returning to menu")
                    # stop spawning and clear entities
                    time.set_timer(SPAWN_EVENT, 0)
                    viruses.empty()
                    bullets.empty()
                    # compute final time and update high score
                    final_secs = 0.0
                    if game_start_ticks is not None:
                        final_secs = (time.get_ticks() - game_start_ticks) / 1000.0
                    if final_secs > high_score:
                        high_score = final_secs
                        save_high_score(high_score)
                        print(f"New high score: {high_score:.1f}s")
                    game_start_ticks = None
                    state = MENU

        # Spawning is handled by the timer event (SPAWN_EVENT) in the event loop

        # Update bullets, draw them, and remove off-screen bullets
        for b in bullets:
            b.update()
            # remove bullets that go off-screen
            if b.pos_x < -50 or b.pos_x > window_width + 50 or b.pos_y < -50 or b.pos_y > window_height + 50:
                b.kill()
            else:
                b.reset()

        # Bullet-virus collision: bullets always removed; viruses take damage if boss, otherwise die
        collisions = sprite.groupcollide(viruses, bullets, False, True)
        for v, blist in collisions.items():
            hits = len(blist)
            if getattr(v, 'is_boss', False):
                # boss takes damage per bullet
                v.hp -= BULLET_DAMAGE * hits
                print(f"[combat] boss hit x{hits}, hp={v.hp}/{v.max_hp}")
                if v.hp <= 0:
                    # boss defeated
                    v.kill()
                    boss_active = False
                    boss_spawned = True
            else:
                # normal viruses die from any bullet hits
                v.kill()

        # If viruses touch the player, handle boss instant-loss or normal damage
        player_hits = sprite.spritecollide(antivirus, viruses, False)
        if player_hits:
            # if any is a boss, instant loss
            boss_touch = any(getattr(v, 'is_boss', False) for v in player_hits)
            if boss_touch:
                core_hp = 0
                print("Boss touched player - instant loss")
                # stop spawning and clear entities
                time.set_timer(SPAWN_EVENT, 0)
                viruses.empty()
                bullets.empty()
                # compute final time and update high score
                final_secs = 0.0
                if game_start_ticks is not None:
                    final_secs = (time.get_ticks() - game_start_ticks) / 1000.0
                if final_secs > high_score:
                    high_score = final_secs
                    save_high_score(high_score)
                    print(f"New high score: {high_score:.1f}s")
                game_start_ticks = None
                state = MENU
            else:
                # remove normal viruses that hit the player and apply damage
                killed = 0
                for v in player_hits:
                    v.kill()
                    killed += 1
                core_hp -= DAMAGE_PER_HIT * killed
                print(f"[player] antivirus hit by {killed} virus(es); CORE HP={core_hp}")
                if core_hp <= 0:
                    core_hp = 0
                    print("Core destroyed by player collision - returning to menu")
                    # stop spawning and clear entities
                    time.set_timer(SPAWN_EVENT, 0)
                    viruses.empty()
                    bullets.empty()
                    # compute final time and update high score
                    final_secs = 0.0
                    if game_start_ticks is not None:
                        final_secs = (time.get_ticks() - game_start_ticks) / 1000.0
                    if final_secs > high_score:
                        high_score = final_secs
                        save_high_score(high_score)
                        print(f"New high score: {high_score:.1f}s")
                    game_start_ticks = None
                    state = MENU

        # Level flow: when all normal enemies spawned and cleared, spawn boss once
        if level_spawned >= level_total_enemies and not boss_spawned and len(viruses) == 0 and state == GAME:
            # spawn the boss for this level
            b = spawn_boss()
            viruses.add(b)
            boss_active = True
            boss_spawned = True
            print(f"[boss] spawned for level {LEVEL} with hp={b.hp}")

        # If boss was spawned and now there are no viruses, boss defeated -> advance level
        if boss_spawned and not boss_active and len(viruses) == 0 and state == GAME:
            LEVEL += 1
            # prepare next level
            level_total_enemies = enemies_for_level(LEVEL)
            level_spawned = 0
            boss_spawned = False
            # make gameplay progressively harder
            VIRUS_SPAWN_INTERVAL_MS = max(350, VIRUS_SPAWN_INTERVAL_MS - 150)
            VIRUS_SPEED_MIN += 1
            VIRUS_SPEED_MAX += 1
            MAX_VIRUSES = min(100, MAX_VIRUSES + 5)
            # apply new timer
            time.set_timer(SPAWN_EVENT, VIRUS_SPAWN_INTERVAL_MS)
            # spawn an initial small batch for the new level
            initial = min(5, level_total_enemies)
            for i in range(initial):
                viruses.add(spawn_virus())
            level_spawned = initial
            print(f"Level up! Now level {LEVEL} - enemies={level_total_enemies}, spawn_ms={VIRUS_SPAWN_INTERVAL_MS}, speed={VIRUS_SPEED_MIN}-{VIRUS_SPEED_MAX}")


    display.update()
    clock.tick(FPS)