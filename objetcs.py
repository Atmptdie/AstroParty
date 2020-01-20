import pygame
from utils import load_image, rot_center
from math import sin, cos, radians as rad, sqrt
col_sprites = pygame.sprite.Group()





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
        if abs(self.vx) < abs(Ship.MAX_SPEED * sin(rad(self.angle))) or self.ax * self.vx < 0:
            self.vx += self.ax * dt
        if abs(self.vy) < abs(Ship.MAX_SPEED * cos(rad(self.angle))) or self.ay * self.vy < 0:
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
            self.image = pygame.Surface([Ship.ship_iwidth, 4])
            self.rect = pygame.Rect(x, y, Ship.ship_iwidth, 4)
        elif mode == 'vertical':
            self.image = pygame.Surface([4, Ship.ship_iheight])
            self.rect = pygame.Rect(x, y, 4, Ship.ship_iheight)
        self.image.fill(pygame.Color('blue'))

    def update(self, *args):
        super().update(self, *args)
        b = pygame.sprite.spritecollideany(self, bullets)
        if pygame.sprite.spritecollideany(self, bullets):
            b.kill()


class Pilot(Object):
    BASE_SPEED = 120

    def __init__(self, group, path, x, y, angle, player):
        super().__init__(group, path, x, y, 0, 0, angle)
        self.active = False
        self.rotating = False
        self.player = player
        self.colliding = {'h': False, 'v': False}
        self.charged = False

    def set_active(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = Pilot.BASE_SPEED * sin(rad(self.angle))
        self.vy = Pilot.BASE_SPEED * cos(rad(self.angle))
        self.image = rot_center(self.base_image, angle)
        self.active = True
        self.add(pilot_sprites)

    def charge(self):
        self.charged = True
        self.vx = Pilot.BASE_SPEED * -sin(rad(self.angle))
        self.vy = Pilot.BASE_SPEED * -cos(rad(self.angle))

    def killed(self):
        self.kill()
        self.active = False
        self.rotating = False

    def update(self, dt):
        super().update(dt)
        if self.rotating:
            self.angle += Ship.WSPEED * dt
            self.image = pygame.transform.rotate(self.base_image, self.angle)
        if not self.charged:
            try:
                self.ax = -(self.vx ** 2) / self.vx * 0.5
            except ZeroDivisionError:
                self.ax = 0
            try:
                self.ay = -(self.vx ** 2) / self.vx * 0.5
            except ZeroDivisionError:
                self.ay = 0
        else:
            self.vx = Pilot.BASE_SPEED * -sin(rad(self.angle))
            self.vy = Pilot.BASE_SPEED * -cos(rad(self.angle))
        check_collision = {'v': False, 'h': False}
        if pygame.sprite.spritecollideany(self, horizontal_borders):
            check_collision['h'] = True

        if pygame.sprite.spritecollideany(self, vertical_borders):
            check_collision['v'] = True

        if check_collision['v']:
            if not self.colliding['v']:
                self.colliding['v'] = True
                self.vx_C = self.vx
            if not (self.ax * self.vx_C < 0 and self.vx_C * self.vx < 0):
                self.vx = 0
        else:
            self.colliding['v'] = False
            self.vx_C = 0

        if check_collision['h']:
            if not self.colliding['h']:
                self.colliding['h'] = True
                self.vy_C = self.vy
            if not (self.ay * self.vy_C < 0 and self.vy_C * self.vy < 0):
                self.vy = 0
        else:
            self.colliding['h'] = False
            self.vy_C = 0

        b = pygame.sprite.spritecollideany(self, bullets)
        ship = pygame.sprite.spritecollideany(self, ships_sprites)
        if b or ship:
            self.killed()


class CollisionCircle(pygame.sprite.Sprite):
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


class Ship(Object):
    ship_iwidth, ship_iheight = 30, 30
    MAX_SPEED = 180
    WSPEED = 200
    BASE_ACC = 780
    def __init__(self, group, path, x, y, v, a, angle, player=None):
        super().__init__(group, path, x, y, v, a, angle)
        self.player = player
        self.timer = 0
        self.active = True
        self.vx_C = self.vy_C = 0  # speed before collision
        self.rotating = False
        self.colliding = {'h': False, 'v': False}
        self.collision_cirlce = CollisionCircle(self.x + (Ship.ship_iwidth - 18) / 2, self.y + 10, 9, self)

    def shot(self):
        self.timer = 0
        self.active = False
        self.collision_cirlce.kill()
        self.kill()
        self.player.pilot.set_active(self.x, self.y, self.angle)
        self.rotating = False

    def pew(self):
        Bullet(bullets, 'bullet.png', self.x + Ship.ship_iwidth // 2 - Ship.ship_iwidth // 2 * sin(rad(self.angle)),
               self.y + Ship.ship_iheight // 2 - Ship.ship_iheight // 2 * cos(rad(self.angle)), 500, 0, self.angle, self)

    def revive(self):
        x, y = self.player.pilot.x, self.player.pilot.y
        angle = self.player.pilot.angle
        self.angle = angle
        self.image = rot_center(self.base_image, angle)
        self.vx = self.vy = 1
        self.x = x
        self.y = y
        self.add(ships_sprites)
        self.collision_cirlce = CollisionCircle(self.x + (Ship.ship_iwidth - 18) / 2, self.y + 10, 9, self)
        self.active = True
        self.player.pilot.killed()

    def update(self, dt):
        super().update(dt)
        if self.rotating:
            self.angle += Ship.WSPEED * dt
            self.image = rot_center(self.base_image, self.angle)
        self.ax = -Ship.BASE_ACC * sin(rad(self.angle))
        self.ay = -Ship.BASE_ACC * cos(rad(self.angle))
        check_collision = self.collision_cirlce.update(self.x + Ship.ship_iwidth // 2 + 4 * sin(rad(self.angle)) - 9,
                                                       self.y + Ship.ship_iheight // 2 + 4 * cos(rad(self.angle)) - 9)
        if check_collision['v']:
            if not self.colliding['v']:
                self.colliding['v'] = True
                self.vx_C = self.vx
            if not (self.ax * self.vx_C < 0 and self.vx_C * self.vx < 0):
                self.vx = 0
        else:
            self.colliding['v'] = False
            self.vx_C = 0

        if check_collision['h']:
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
