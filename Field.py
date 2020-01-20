from utils import *
from objetcs import *

offset = 100


class Field:
    def __init__(self, map_name=None):
        self.map = load_map(map_name)
        self.players = []

    def prep_map(self):

        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                if self.map[y][x] == '-':
                    Border('horizontal', offset + x * Ship.ship_iwidth, offset + y * Ship.ship_iheight)

                elif self.map[y][x] == '|':
                    Border('vertical', offset + x * Ship.ship_iwidth, offset + y * Ship.ship_iheight)

                elif self.map[y][x] == '⎾':
                    Border('horizontal', offset + x * Ship.ship_iwidth, offset + y * Ship.ship_iheight)
                    Border('vertical', offset + x * Ship.ship_iwidth, offset + y * Ship.ship_iheight)

                elif self.map[y][x] == '⎿':
                    Border('horizontal', offset + x * Ship.ship_iwidth, offset + y * Ship.ship_iheight)
                    Border('vertical', offset + x * Ship.ship_iwidth, offset + (y - 1) * Ship.ship_iheight)

                elif self.map[y][x] == '⏌':
                    Border('horizontal', offset + x * Ship.ship_iwidth, offset + y * Ship.ship_iheight)
                    Border('vertical', offset + (x + 1) * Ship.ship_iwidth, offset + (y - 1) * Ship.ship_iheight)

                elif self.map[y][x] == '⏋':
                    Border('horizontal', offset + x * Ship.ship_iwidth, offset + y * Ship.ship_iheight)
                    Border('vertical', offset + (x + 1) * Ship.ship_iwidth, offset + y * Ship.ship_iheight)

    def add_player(self, player: Player):
        self.players.append(player)
