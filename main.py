import pygame
import os
from math import sin, cos, radians as rad, sqrt

SHIP, PILOT, KILLED = 2, 1, 0
BASE_ACC = 780  # basic acceleration
WSPEED = 200  # angles per second rotating speed
MAX_SPEED = 180
ship_iwidth, ship_iheight = 30, 30  # image size
pygame.init()
width, height = 800, 800
size = width, height
screen = pygame.display.set_mode(size)
col_sprites = pygame.sprite.Group()


def rot_center(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert_alpha()
    return image


def load_map(name):
    fullname = os.path.join('maps', name)
    with open(fullname, 'r', encoding='utf8') as f:
        data = [j for j in [i for i in f.read().split('\n')]]
    return data


class Object(pygame.sprite.Sprite):
    def __init__(self, group, path, x, y, v, a, angle):
        super().__init__(group)

        self.angle = angle  # угол от вертикали (0 - вверх), против часовой, деги на калькуляторе!
        self.base_image = load_image(f'{path}')
        self.image = rot_center(self.base_image, angle)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
        self.vx = -v * sin(rad(angle))
        self.vy = -v * cos(rad(angle))
        self.ax = -a * sin(rad(angle))
        self.ay = -a * cos(rad(angle))

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        if abs(self.vx) < abs(MAX_SPEED * sin(rad(self.angle))) or self.ax * self.vx < 0:
            self.vx += self.ax * dt
        if abs(self.vy) < abs(MAX_SPEED * cos(rad(self.angle))) or self.ay * self.vy < 0:
            self.vy += self.ay * dt


horizontal_borders = pygame.sprite.Group()
vertical_borders = pygame.sprite.Group()
ships_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
pilot_sprites = pygame.sprite.Group()


class Border(pygame.sprite.Sprite):
    modes = ['horizontal', 'vertical']
    def __init__(self, mode, x, y):
        if mode in Border.modes:
            super().__init__(horizontal_borders if mode == 'horizontal' else vertical_borders)
        else:
            raise Exception('WRONG MODE')

        if mode == 'horizontal':
            self.image = pygame.Surface([ship_iwidth, 4])
            self.rect = pygame.Rect(x, y, ship_iwidth, 4)
        elif mode == 'vertical':
            self.image = pygame.Surface([4, ship_iheight])
            self.rect = pygame.Rect(x, y, 4, ship_iheight)
        self.image.fill(pygame.Color('blue'))

    def update(self, *args):
        super().update(self, *args)
        b = pygame.sprite.spritecollideany(self, bullets)
        if pygame.sprite.spritecollideany(self, bullets):
            b.kill()



class Pilot(Object):
    def __init__(self, group, path, x, y, v, a, angle, player):
        super().__init__(group, path, x, y, v, a, angle)
        self.active = False
        self.rotating = False
        self.player = player

    def set_active(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.active = True
        self.add(pilot_sprites)

    def killed(self):
        self.kill()
        self.active = False

    def update(self, dt):
        super().update(dt)
        if self.rotating:
            self.angle += WSPEED * dt
            self.image = pygame.transform.rotate(self.base_image, self.angle)
            self.ax = -BASE_ACC * sin(rad(self.angle))
            self.ay = -BASE_ACC * cos(rad(self.angle))
        b = pygame.sprite.spritecollideany(self, bullets)
        ship = pygame.sprite.spritecollideany(self, ships_sprites)
        if b or ship:
            self.killed()


class Ship(Object):
    def __init__(self, group, path, x, y, v, a, angle, player=None):
        super().__init__(group, path, x, y, v, a, angle)
        self.player = player
        self.timer = 0
        self.active = True
        self.vx_C = self.vy_C = 0  # speed before collision
        self.rotating = False
        self.colliding = {'h': False, 'v': False}
        self.collision_cirlce = CollisionCirlce(self.x + (ship_iwidth - 18) / 2, self.y + 10, 9, self)

    def shot(self):
        self.timer = 0
        self.active = False
        self.collision_cirlce.kill()
        self.kill()
        self.player.pilot.set_active(self.x, self.y, self.angle)

    def pew(self):
        Bullet(bullets, 'bullet.png', self.x + ship_iwidth // 2 - ship_iwidth // 2 * sin(rad(self.angle)),
               self.y + ship_iheight // 2 - ship_iheight // 2 * cos(rad(self.angle)), 500, 0, self.angle, self)

    def revive(self):
        x, y = self.player.pilot.x, self.player.pilot.y
        self.x = x
        self.y = y
        self.add(ships_sprites)
        self.collision_cirlce = CollisionCirlce(self.x + (ship_iwidth - 18) / 2, self.y + 10, 9, self)
        self.active = True
        self.player.pilot.killed()

    def update(self, dt):
        super().update(dt)
        if self.rotating:
            self.angle += WSPEED * dt
            self.image = rot_center(self.base_image, self.angle)
            self.ax = -BASE_ACC * sin(rad(self.angle))
            self.ay = -BASE_ACC * cos(rad(self.angle))
        check_collision = self.collision_cirlce.update(self.x + ship_iwidth // 2 + 4 * sin(rad(self.angle)) - 9,
                                                       self.y + ship_iheight // 2 + 4 * cos(rad(self.angle)) - 9)
        if check_collision['v']:
            print('v')
            if not self.colliding['v']:
                self.colliding['v'] = True
                self.vx_C = self.vx
            if not (self.ax * self.vx_C < 0 and self.vx_C * self.vx < 0):
                self.vx = 0
        else:
            self.colliding['v'] = False
            self.vx_C = 0

        if check_collision['h']:
            print('h')
            if not self.colliding['h']:
                self.colliding['h'] = True
                self.vy_C = self.vy
            if not (self.ay * self.vy_C < 0 and self.vy_C * self.vy < 0):
                self.vy = 0
        else:
            self.colliding['h'] = False
            self.vy_C = 0

        if check_collision['b']:
            self.shot()


class CollisionCirlce(pygame.sprite.Sprite):
    def __init__(self, x, y, r, player):
        super().__init__(col_sprites)
        self.r = r
        self.player = player
        self.image = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA, 32)
        pygame.draw.circle(self.image, pygame.Color("red"), (int(r), int(r)), int(r))
        self.rect = pygame.Rect(x, y, 2 * r, 2 * r)

    def update(self, x, y):
        self.rect.x = int(x)
        self.rect.y = int(y)
        result = {'h': False, 'v': False, 's': [False, []], 'b': False}
        if pygame.sprite.spritecollideany(self, horizontal_borders):
            result['h'] = True
        if pygame.sprite.spritecollideany(self, vertical_borders):
            result['v'] = True
        if len(pygame.sprite.spritecollide(self, col_sprites, False)) > 1:
            result['s'][0] = True
            result['s'][1] = pygame.sprite.spritecollide(self, col_sprites, False)[1:]
        b = pygame.sprite.spritecollideany(self, bullets)
        if pygame.sprite.spritecollideany(self, bullets):
            if b.player != self.player:
                result['b'] = True
                b.kill()

        return result


class Bullet(Object):
    def __init__(self, group, path, x, y, v, a, angle, player):
        super().__init__(group, path, x, y, v, a, angle)
        self.player = player


#  TODO collision with ships
# if check_collision['s'][0]:
#     vx = [self.vx]
#     vy = [self.vy]
#     for sprite in check_collision['s'][1]:
#         vx.append(sprite.player.vx)
#         vy.append(sprite.player.vy)


class Player:
    def __init__(self, ship: Ship, pilot: Pilot, number: int):
        self.ship = ship
        self.ship.player = self
        self.pilot = pilot
        self.pilot.player = self
        self.number = number

    def active_object(self):
        if self.ship.active:
            return self.ship
        elif self.pilot.active:
            return self.pilot
        else:
            return None


offset = 110


class Field:
    def __init__(self, map_name=None):
        self.map = load_map(map_name)
        self.players = []

    def prep_map(self):

        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                if self.map[y][x] == '-':
                    Border('horizontal', offset + x * ship_iwidth, offset + y * ship_iheight)

                elif self.map[y][x] == '|':
                    Border('vertical', offset + x * ship_iwidth, offset + y * ship_iheight)

                elif self.map[y][x] == '⎾':
                    Border('horizontal', offset + x * ship_iwidth, offset + y * ship_iheight)
                    Border('vertical', offset + x * ship_iwidth, offset + y * ship_iheight)

                elif self.map[y][x] == '⎿':
                    Border('horizontal', offset + x * ship_iwidth, offset + y * ship_iheight)
                    Border('vertical', offset + x * ship_iwidth, offset + (y - 1) * ship_iheight)

                elif self.map[y][x] == '⏌':
                    Border('horizontal', offset + x * ship_iwidth, offset + y * ship_iheight)
                    Border('vertical', offset + (x + 1) * ship_iwidth, offset + (y - 1) * ship_iheight)

                elif self.map[y][x] == '⏋':
                    Border('horizontal', offset + x * ship_iwidth, offset + y * ship_iheight)
                    Border('vertical', offset + (x + 1) * ship_iwidth, offset + y * ship_iheight)

    def add_player(self, player: Player):
        self.players.append(player)


# start menu over here
player_number = 2
start_coords = [(offset + 5, offset + 5), (-offset + width - 2 * ship_iwidth, -offset + height - 2 * ship_iheight),
                (offset + width - ship_iwidth, offset), (offset, offset + height - ship_iheight)]

field = Field(map_name='map1.txt')
field.prep_map()
for i in range(player_number):
    ship = Ship(ships_sprites, f'ship_player{i + 1}.png', *start_coords[i], 0, BASE_ACC,
                180 * ((i + 1) % 2) + 45 * (1 if i < 2 else -1), player=None)
    pilot = Pilot(pilot_sprites, f'pilot_player{i + 1}.png', 0, 0, 0, BASE_ACC, 0, player=None)
    pilot.kill()
    field.add_player(Player(ship, pilot, i + 1))

# 180 * ((i + 1) % 2) + 45 * (1 if i < 2 else -1)
running = True
fps = 60
clock = pygame.time.Clock()
while running:
    for player in field.players:
        if type(player.active_object()) == Pilot:
            player.ship.timer += 1
            if player.ship.timer > fps * 5:
                player.ship.revive()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == 275:
                field.players[0].active_object().rotating = True

            if event.key == 273:
                field.players[0].active_object().pew()

            if event.key == 119:
                field.players[1].active_object().pew()

            if event.key == 100:
                field.players[1].active_object().rotating = True

        if event.type == pygame.KEYUP:
            if event.key == 275:
                field.players[0].active_object().rotating = False

            if event.key == 100:
                field.players[1].active_object().rotating = False
            print(event.key)
    #  (0, 70, 139) - dark blue color
    screen.fill(pygame.Color('black'))
    clock.tick(fps)
    col_sprites.draw(screen)
    vertical_borders.draw(screen)
    horizontal_borders.draw(screen)
    vertical_borders.update()
    horizontal_borders.update()
    bullets.draw(screen)
    bullets.update(1 / fps)
    pilot_sprites.draw(screen)
    pilot_sprites.update(1 / fps)
    ships_sprites.draw(screen)
    ships_sprites.update(1 / fps)
    pygame.display.flip()
