from utils import *
from objetcs import *
from Field import *
SHIP, PILOT, KILLED = 2, 1, 0
pygame.init()
width, height = 800, 800
size = width, height
screen = pygame.display.set_mode(size)

player_number = 3
start_coords = [(offset + 5, offset + 5), (-offset + width - 2 * Ship.ship_iwidth, -offset + height - 2 * Ship.ship_iheight),
                (width - offset - 30 - Ship.ship_iwidth, offset + 10), (offset, offset + height - Ship.ship_iheight)]

field = Field(map_name='map2.txt')
field.prep_map()


def Game():
    global running
    while running:
        for player in field.players:
            if type(player.active_object()) == Pilot:
                player.ship.timer += 1
                if player.ship.timer >= fps * revive_time:
                    player.ship.revive()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == 275 and field.players[0].active_object():
                    field.players[0].active_object().rotating = True
                if event.key == 273 and field.players[0].active_object():
                    if type(field.players[0].active_object()) == Ship:
                        field.players[0].ship.pew()
                    elif type(field.players[0].active_object()) == Pilot:
                        field.players[0].pilot.charge()
                if event.key == 119 and field.players[1].active_object():
                    if type(field.players[1].active_object()) == Ship:
                        field.players[1].ship.pew()
                    elif type(field.players[1].active_object()) == Pilot:
                        field.players[1].pilot.charge()
                if event.key == 100 and field.players[1].active_object():
                    field.players[1].active_object().rotating = True
                if event.key == 264:
                    if type(field.players[2].active_object()) == Ship:
                        field.players[2].ship.pew()
                    elif type(field.players[2].active_object()) == Pilot:
                        field.players[2].pilot.charge()
                if event.key == 262 and field.players[2].active_object():
                    field.players[2].active_object().rotating = True
            if event.type == pygame.KEYUP:
                if event.key == 275 and field.players[0].active_object():
                    field.players[0].active_object().rotating = False
                if event.key == 273:
                    if type(field.players[0].active_object()) == Pilot:
                        field.players[0].pilot.charged = False
                if event.key == 100 and field.players[1].active_object():
                    field.players[1].active_object().rotating = False
                if event.key == 119:
                    if type(field.players[1].active_object()) == Pilot:
                        field.players[1].pilot.charged = False
                if event.key == 262 and field.players[2].active_object():
                    field.players[2].active_object().rotating = False

        if len(pilot_sprites.sprites() + ships_sprites.sprites()) == 1:
            if ships_sprites.sprites():
                return ships_sprites.sprites()[0]
            else:
                return pilot_sprites.sprites()[0]
        elif len(pilot_sprites.sprites() + ships_sprites.sprites()) < 1:
            return None
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


def draw():
    global running
    font = pygame.font.Font(None, 50)
    while True:
        for event in pygame.event.get():
            try:
                if event.type == pygame.QUIT:
                    running = False
                    return None
                if event.key == 32:
                    return None
            except:
                pass

        timer = font.render('tap space to continue', 1, (100, 255, 100))
        timer_x = width // 2 - timer.get_width() // 2
        timer_y = height // 4 - timer.get_height() // 2
        screen.blit(timer, (timer_x, timer_y))

        score_text = font.render(f'{score}', 1, (100, 255, 100))
        score_x = width // 2 - score_text.get_width() // 2
        score_y = height // 2 - score_text.get_height() // 2
        score_w = score_text.get_width()
        score_h = score_text.get_height()
        screen.blit(score_text, (score_x, score_y))
        pygame.draw.rect(screen, (0, 255, 0), (score_x - 10, score_y - 10,
                                               score_w + 20, score_h + 20), 1)
        pygame.display.flip()
        clock.tick(fps)


running = True
fps = 60
revive_time = 5
clock = pygame.time.Clock()
score = {1: 0, 2: 0, 3: 0, 4: 0}
while running:
    field.prep_map()
    field.players.clear()
    ships_sprites.empty()
    pilot_sprites.empty()
    col_sprites.empty()
    bullets.empty()
    for i in range(player_number):
        ship = Ship(ships_sprites, f'ship_player{i + 1}.png', *start_coords[i], 0, Ship.BASE_ACC,
                    180 * ((i + 1) % 2) + 45 * (1 if i < 2 else -1), player=None)
        pilot = Pilot(pilot_sprites, f'pilot_player{i + 1}.png', 0, 0, 0, player=None)
        pilot.kill()
        field.add_player(Player(ship, pilot, i + 1))
    winner = Game()
    if winner:
        score[field.players.index(winner.player) + 1] += 1
        draw()
