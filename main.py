from pygame import *
# initialize pygame modules
init()
from random import randint, uniform
import math
from entities import Antivirus, SystemSprite, Virus, Bullet, Boss, spawn_virus, spawn_boss
import entities

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

# Use classes and spawn helpers from the `entities` module. The local definitions were removed
# to avoid shadowing the imported classes (Antivirus, Virus, Bullet, Boss) and spawn functions.

# --- Game Objects ---
# instantiate Antivirus from the entities module to ensure upgrade methods are present
antivirus = entities.Antivirus('antivirus.png', 686, 386, 65, 65, 7)
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
UPGRADE = 2
state = MENU

# Upgrade UI state
upgrade_choices = []
upgrade_buttons = []
upgrade_pending = False

def prepare_upgrades_for_level(level):
    """Return a list of 3 upgrade dicts appropriate for the level."""
    pool = [
        {'key': 'faster_fire', 'title': 'Faster Fire', 'desc': 'Reduce cooldown by 50ms'},
        {'key': 'more_damage', 'title': 'Increased Damage', 'desc': '+1 bullet damage'},
        {'key': 'bullet_speed', 'title': 'Bullet Speed', 'desc': '+2 bullet speed'},
        {'key': 'spread_shot', 'title': 'Spread Shot', 'desc': '+1 pellet (wider spread)'},
        {'key': 'pierce', 'title': 'Piercing Rounds', 'desc': '+1 pierce per bullet'},
    ]
    # simple selection: choose 3 unique entries pseudo-randomly based on level
    chosen = []
    tries = list(range(len(pool)))
    # deterministic-ish variation
    import random
    random.shuffle(tries)
    for i in range(3):
        chosen.append(pool[tries[i]])
    return chosen

def apply_upgrade_choice(av, choice_key):
    if choice_key == 'faster_fire':
        av.shoot_cooldown_ms = max(50, av.shoot_cooldown_ms - 50)
    elif choice_key == 'more_damage':
        av.bullet_damage += 1
    elif choice_key == 'bullet_speed':
        av.bullet_speed += 2
    elif choice_key == 'spread_shot':
        av.pellets = min(7, av.pellets + 1)
        av.spread_deg = min(60, av.spread_deg + 8)
    elif choice_key == 'pierce':
        av.bullet_pierce += 1

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
        # Shooting: left mouse click handled by Antivirus upgrades when in GAME
        if e.type == MOUSEBUTTONDOWN and state == GAME:
            tx, ty = mouse_pos
            if antivirus.can_shoot():
                shots = antivirus.shoot(tx, ty)
                for s in shots:
                    bullets.add(s)
                antivirus.mark_shot()
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

        # Bullet-virus collision: bullets may pierce so we manage bullet lifetimes manually
        collisions = sprite.groupcollide(viruses, bullets, False, False)
        for v, blist in collisions.items():
            for b in blist:
                # apply damage to boss or remove normal virus
                if getattr(v, 'is_boss', False):
                    v.hp -= getattr(b, 'damage', BULLET_DAMAGE)
                    print(f"[combat] boss hit, hp={v.hp}/{v.max_hp}")
                    if v.hp <= 0:
                        v.kill()
                        boss_active = False
                        # mark that an upgrade should be offered before next level
                        upgrade_pending = True
                else:
                    # normal virus dies on any hit
                    v.kill()
                # manage bullet pierce - if on_hit returns True bullet dies
                if getattr(b, 'on_hit', None) is not None:
                    if b.on_hit():
                        b.kill()
                else:
                    # fallback: remove bullet after one hit
                    b.kill()

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
            if upgrade_pending:
                # pause game and show upgrade choices
                upgrade_choices = prepare_upgrades_for_level(LEVEL)
                upgrade_buttons = []
                # create rectangles for 3 buttons centered on screen
                btn_w = 520
                btn_h = 80
                gap = 20
                total_h = btn_h * 3 + gap * 2
                start_y = window_height//2 - total_h//2
                for i, choice in enumerate(upgrade_choices):
                    rect = Rect(window_width//2 - btn_w//2, start_y + i * (btn_h + gap), btn_w, btn_h)
                    upgrade_buttons.append(rect)
                state = UPGRADE
                upgrade_pending = False
            else:
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

    elif state == UPGRADE:
        # draw a dimmed background and upgrade choices
        window.fill((10, 10, 20))
        title = font_main.render("UPGRADE AVAILABLE", True, CYAN)
        window.blit(title, (window_width//2 - title.get_width()//2, 120))
        desc = font_sub.render("Choose one upgrade to enhance your antivirus", True, WHITE)
        window.blit(desc, (window_width//2 - desc.get_width()//2, 200))

        # draw buttons
        for i, rect in enumerate(upgrade_buttons):
            # hover effect
            color = (40, 40, 80) if rect.collidepoint(mouse_pos) else (30, 30, 60)
            draw.rect(window, color, rect)
            draw.rect(window, (200,200,200), rect, 2)
            choice = upgrade_choices[i]
            t = font_sub.render(choice['title'], True, WHITE)
            s = font_sub.render(choice['desc'], True, CYAN)
            window.blit(t, (rect.x + 18, rect.y + 12))
            window.blit(s, (rect.x + 18, rect.y + 44))

        # handle click on upgrade buttons
        if mouse.get_pressed()[0]:
            # check which button clicked
            for i, rect in enumerate(upgrade_buttons):
                if rect.collidepoint(mouse_pos):
                    choice = upgrade_choices[i]
                    apply_upgrade_choice(antivirus, choice['key'])
                    # after selection, advance level as if boss defeated
                    LEVEL += 1
                    level_total_enemies = enemies_for_level(LEVEL)
                    level_spawned = 0
                    boss_spawned = False
                    # make gameplay progressively harder
                    VIRUS_SPAWN_INTERVAL_MS = max(350, VIRUS_SPAWN_INTERVAL_MS - 150)
                    VIRUS_SPEED_MIN += 1
                    VIRUS_SPEED_MAX += 1
                    MAX_VIRUSES = min(100, MAX_VIRUSES + 5)
                    time.set_timer(SPAWN_EVENT, VIRUS_SPAWN_INTERVAL_MS)
                    initial = min(5, level_total_enemies)
                    for j in range(initial):
                        viruses.add(spawn_virus())
                    level_spawned = initial
                    print(f"Applied upgrade: {choice['title']} - new stats: cooldown={antivirus.shoot_cooldown_ms} damage={antivirus.bullet_damage} speed={antivirus.bullet_speed} pellets={antivirus.pellets} pierce={antivirus.bullet_pierce}")
                    state = GAME
                    break


    display.update()
    clock.tick(FPS)