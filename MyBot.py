import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random


class Hive(object):
    def __init__(self):

        self.my_id, self.game_map = hlt.get_init()
        hlt.send_init("PythonBot")

    def assign_move(self, square):
        for direction, neighbor in enumerate(self.game_map.neighbors(square)):
            if neighbor.owner != self.my_id and neighbor.strength < square.strength:
                return Move(square, direction)

        if all(neighbor.owner == self.my_id for neighbor in self.game_map.neighbors(square)):
            return Move(square, random.choice((NORTH, WEST, SOUTH, EAST)))

        return Move(square, STILL)


def run():

    hive = Hive()

    while True:
        hive.game_map.get_frame()

        moves = [hive.assign_move(square) for square in hive.game_map if square.owner == hive.my_id]
        hlt.send_frame(moves)


run()
