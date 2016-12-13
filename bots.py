import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move
import random
from itertools import chain


class Bot(object):
    def __init__(self, name):
        self.my_id, self.game_map = hlt.get_init()
        hlt.send_init(name)

    def assign_move(self, square):
        return Move(square, STILL)

    def run(self):

        while True:
            self.game_map.get_frame()

            moves = [self.assign_move(square) for square in self.game_map if square.owner == self.my_id]
            hlt.send_frame(moves)


class RandomBot(Bot):
    def __init__(self):
        super(RandomBot, self).__init__("RandomBot")

    def assign_move(self, square):
        return Move(square, random.choice((NORTH, EAST, SOUTH, WEST, STILL)))


class BlobBot(Bot):
    def __init__(self):
        super(BlobBot, self).__init__("BlobBot")

    def assign_move(self, square):
        for direction, neighbor in enumerate(self.game_map.neighbors(square)):
            if neighbor.owner != self.my_id and neighbor.strength < square.strength:
                return Move(square, direction)

        if all(neighbor.owner == self.my_id for neighbor in self.game_map.neighbors(square)):
            return Move(square, random.choice((NORTH, WEST, SOUTH, EAST)))

        return Move(square, STILL)


class PowerBlobBot(Bot):
    def __init__(self):
        super(PowerBlobBot, self).__init__("PowerBlobBot")

    def assign_move(self, square):
        for direction, neighbor in enumerate(self.game_map.neighbors(square)):
            if neighbor.owner != self.my_id and neighbor.strength < square.strength:
                return Move(square, direction)

        if all(neighbor.owner == self.my_id for neighbor in self.game_map.neighbors(square)):
            if square.strength < 128:
                return Move(square, STILL)
            else:
                return Move(square, random.choice((NORTH, WEST, SOUTH, EAST)))

        return Move(square, STILL)
