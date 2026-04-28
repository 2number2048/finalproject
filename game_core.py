from pygame import *
# initialize pygame modules
init()
from random import randint, uniform
import math
from entities import Antivirus, SystemSprite, Virus, Bullet, Boss, spawn_virus, spawn_boss
import entities

def run():
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

    # --- Game Objects ---
    antivirus = entities.Antivirus('antivirus.png', 686, 386, 65, 65, 7)
    core = SystemSprite('core.png', 625, 450, 125, 125, 0)
    viruses = sprite.Group()
    for i in range(5):
        viruses.add(spawn_virus(VIRUS_SPEED_MIN, VIRUS_SPEED_MAX, window_width, window_height))
    bullets = sprite.Group()

    # Core health
    CORE_MAX_HP = 100
    core_hp = CORE_MAX_HP
    DAMAGE_PER_HIT = 10
    HP_BAR_POS = (20, 20)
    HP_BAR_SIZE = (300, 24)
    CORE_HEAL_PER_LEVEL = 20

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

    # Virus spawn config
    VIRUS_SPAWN_INTERVAL_MS = 1200
    MAX_VIRUSES = 40
    SPAWN_EVENT = USEREVENT + 1
    time.set_timer(SPAWN_EVENT, VIRUS_SPAWN_INTERVAL_MS)

    # Consumable spawn
    CONSUMABLE_SPAWN_INTERVAL_MS = 12000
    CONSUMABLE_EVENT = USEREVENT + 2
    CONSUMABLE_HEAL = 20
    time.set_timer(CONSUMABLE_EVENT, CONSUMABLE_SPAWN_INTERVAL_MS)
    consumables = sprite.Group()

    # Level system
    LEVEL = 1
    ENEMIES_BASE = 10
    ENEMIES_INCREMENT = 15
    def enemies_for_level(l):
        return ENEMIES_BASE + (l-1) * ENEMIES_INCREMENT
    level_total_enemies = enemies_for_level(LEVEL)
    level_spawned = 0

    boss_active = False
    boss_spawned = False
    BULLET_DAMAGE = 1

    MENU = 0; GAME = 1; UPGRADE = 2
    state = MENU
    upgrade_choices = []
    upgrade_buttons = []
    upgrade_pending = False

    def prepare_upgrades_for_level(level):
        pool = [
            {'key': 'faster_fire', 'title': 'Faster Fire', 'desc': 'Reduce cooldown by 50ms'},
            {'key': 'more_damage', 'title': 'Increased Damage', 'desc': '+1 bullet damage'},
            {'key': 'bullet_speed', 'title': 'Bullet Speed', 'desc': '+2 bullet speed'},
            {'key': 'spread_shot', 'title': 'Spread Shot', 'desc': '+1 pellet (wider spread)'},
            {'key': 'pierce', 'title': 'Piercing Rounds', 'desc': '+1 pierce per bullet'},
        ]
        import random
        random.shuffle(pool)
        return pool[:3]

    def apply_upgrade_choice(av, choice_key):
        if choice_key == 'faster_fire': av.shoot_cooldown_ms = max(50, av.shoot_cooldown_ms - 50)
        elif choice_key == 'more_damage': av.bullet_damage += 1
        elif choice_key == 'bullet_speed': av.bullet_speed += 2
        elif choice_key == 'spread_shot':
            av.pellets = min(7, av.pellets + 1); av.spread_deg = min(60, av.spread_deg + 8)
        elif choice_key == 'pierce': av.bullet_pierce += 1

    run = True
    FPS = 60
    clock = time.Clock()
    start_rect = Rect(0,0,0,0)

    while run:
        mouse_pos = mouse.get_pos()
        for e in event.get():
            if e.type == QUIT: run = False
            if e.type == MOUSEBUTTONDOWN and state == MENU and start_rect.collidepoint(mouse_pos):
                state = GAME
                core_hp = CORE_MAX_HP; viruses.empty(); bullets.empty();
                LEVEL = 1; level_total_enemies = enemies_for_level(LEVEL); level_spawned = 0
                VIRUS_SPAWN_INTERVAL_MS = 1200; time.set_timer(SPAWN_EVENT, VIRUS_SPAWN_INTERVAL_MS)
                for i in range(min(5, level_total_enemies)): viruses.add(spawn_virus(VIRUS_SPEED_MIN, VIRUS_SPEED_MAX, window_width, window_height))
                game_start_ticks = time.get_ticks(); elapsed_seconds = 0.0
            if e.type == MOUSEBUTTONDOWN and state == GAME:
                tx,ty = mouse_pos
                if antivirus.can_shoot():
                    for s in antivirus.shoot(tx,ty): bullets.add(s)
                    antivirus.mark_shot()
            if e.type == SPAWN_EVENT and state == GAME:
                if level_spawned < level_total_enemies and len(viruses) < MAX_VIRUSES:
                    viruses.add(spawn_virus(VIRUS_SPEED_MIN, VIRUS_SPEED_MAX, window_width, window_height)); level_spawned += 1
            if e.type == CONSUMABLE_EVENT and state == GAME:
                if len(consumables) < 2: consumables.add(entities.spawn_consumable(window_width, window_height, heal_amount=CONSUMABLE_HEAL))

        if state == MENU:
            window.fill(BLACK)
            title = font_main.render('SYSTEM DEFENSE', True, CYAN); window.blit(title, (window_width//2 - title.get_width()//2, 300))
            hs_text = font_sub.render(f'HIGH SCORE: {int(high_score)}s', True, WHITE); window.blit(hs_text, (window_width//2 - hs_text.get_width()//2, 380))
            btn_render = font_sub.render('INITIALIZE SYSTEM', True, WHITE)
            start_rect = btn_render.get_rect(center=(window_width//2, 550)); window.blit(btn_render, start_rect)

        elif state == GAME:
            window.blit(background, (0,0))
            antivirus.update(); antivirus.reset(window); core.reset(window)
            # HP bar
            hp_x,hp_y = HP_BAR_POS; hp_w,hp_h = HP_BAR_SIZE
            draw.rect(window,(50,50,50),(hp_x-2,hp_y-2,hp_w+4,hp_h+4)); draw.rect(window,(100,0,0),(hp_x,hp_y,hp_w,hp_h))
            if core_hp>0: draw.rect(window,(0,200,0),(hp_x,hp_y,int(hp_w*max(0,min(core_hp/CORE_MAX_HP,1.0))),hp_h))
            window.blit(font_sub.render(f'CORE HP: {core_hp}/{CORE_MAX_HP}',True,WHITE),(hp_x,hp_y+hp_h+6))
            # timer
            if game_start_ticks is not None: elapsed_seconds=(time.get_ticks()-game_start_ticks)/1000.0
            else: elapsed_seconds=0.0
            window.blit(font_sub.render(f'TIME: {int(elapsed_seconds)}s',True,WHITE),(window_width-120,20))
            for v in viruses: v.update(core.rect.centerx, core.rect.centery); v.reset(window)
            for b in bullets: b.update();
                # off-screen check
            for b in bullets:
                if b.pos_x < -50 or b.pos_x > window_width + 50 or b.pos_y < -50 or b.pos_y > window_height + 50: b.kill()
                else: b.reset(window)
            for c in consumables: c.update(); c.reset(window)
            picked = sprite.spritecollide(antivirus, consumables, True)
            for p in picked: core_hp = min(CORE_MAX_HP, core_hp + getattr(p,'heal_amount',CONSUMABLE_HEAL))
            collisions = sprite.groupcollide(viruses, bullets, False, False)
            for v, blist in collisions.items():
                for b in blist:
                    if getattr(v,'is_boss',False):
                        v.hp -= getattr(b,'damage',BULLET_DAMAGE)
                        if v.hp <= 0: v.kill(); boss_active=False; upgrade_pending=True
                    else: v.kill()
                    if getattr(b,'on_hit',None) is not None:
                        if b.on_hit(): b.kill()
                    else: b.kill()
            player_hits = sprite.spritecollide(antivirus, viruses, False)
            if player_hits:
                boss_touch = any(getattr(v,'is_boss',False) for v in player_hits)
                if boss_touch:
                    core_hp = 0; time.set_timer(SPAWN_EVENT,0); viruses.empty(); bullets.empty();
                    if game_start_ticks is not None:
                        final_secs=(time.get_ticks()-game_start_ticks)/1000.0
                        if final_secs>high_score: high_score=final_secs; save_high_score(high_score)
                    game_start_ticks=None; state=MENU
                else:
                    killed=0
                    for v in player_hits: v.kill(); killed+=1
                    core_hp -= DAMAGE_PER_HIT * killed
                    if core_hp<=0:
                        core_hp=0; time.set_timer(SPAWN_EVENT,0); viruses.empty(); bullets.empty();
                        if game_start_ticks is not None:
                            final_secs=(time.get_ticks()-game_start_ticks)/1000.0
                            if final_secs>high_score: high_score=final_secs; save_high_score(high_score)
                        game_start_ticks=None; state=MENU
            if level_spawned>=level_total_enemies and not boss_spawned and len(viruses)==0 and state==GAME:
                b = spawn_boss(LEVEL, VIRUS_SPEED_MIN, VIRUS_SPEED_MAX, window_width, window_height)
                viruses.add(b); boss_active=True; boss_spawned=True
            if boss_spawned and not boss_active and len(viruses)==0 and state==GAME:
                if upgrade_pending:
                    upgrade_choices = prepare_upgrades_for_level(LEVEL); upgrade_buttons = []
                    btn_w=520; btn_h=80; gap=20; total_h=btn_h*3+gap*2; start_y=window_height//2-total_h//2
                    for i,choice in enumerate(upgrade_choices): upgrade_buttons.append(Rect(window_width//2-btn_w//2, start_y + i*(btn_h+gap), btn_w, btn_h))
                    state = UPGRADE; upgrade_pending=False
                else:
                    LEVEL += 1; core_hp = min(CORE_MAX_HP, core_hp + CORE_HEAL_PER_LEVEL)
                    level_total_enemies = enemies_for_level(LEVEL); level_spawned = 0; boss_spawned=False
                    VIRUS_SPAWN_INTERVAL_MS = max(350, VIRUS_SPAWN_INTERVAL_MS - 150); VIRUS_SPEED_MIN += 1; VIRUS_SPEED_MAX += 1; MAX_VIRUSES = min(100, MAX_VIRUSES + 5)
                    time.set_timer(SPAWN_EVENT, VIRUS_SPAWN_INTERVAL_MS)
                    for i in range(min(5, level_total_enemies)): viruses.add(spawn_virus(VIRUS_SPEED_MIN, VIRUS_SPEED_MAX, window_width, window_height))
            display.update(); clock.tick(FPS)

    # end run()

if __name__ == '__main__':
    run()
