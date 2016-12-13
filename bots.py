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


def weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w

    assert False, "shouldnt get here"


class HeuristicBot(Bot):
    def __init__(self):
        super(HeuristicBot, self).__init__("HeuristicBot")

    def assign_move(self, square):
        heuristic = self.get_heuristic(square)
        choice = weighted_choice(heuristic.items())
        return Move(square, choice)

    def get_heuristic(self, square):
        if square.strength <= 0:
            return {STILL: 1}
        else:
            for direction, neighbor in enumerate(self.game_map.neighbors(square)):
                if neighbor.owner != self.my_id and neighbor.strength < square.strength:
                    return {direction: 1}

            if all(neighbor.owner == self.my_id for neighbor in self.game_map.neighbors(square)):
                all_targets = [(s, self.game_map.get_distance(square, s))
                               for s in chain(*self.game_map.contents)
                               if s.owner != self.my_id]

                closest, _ = max(all_targets, key=lambda o: o[0].production / o[1])

                dx = self.game_map.get_direction(square.x, closest.x, self.game_map.width)
                choice_x = (WEST, abs(dx)) if dx < 0 else (EAST, dx)

                dy = self.game_map.get_direction(square.y, closest.y, self.game_map.height)
                choice_y = (NORTH, abs(dy)) if dy < 0 else (SOUTH, dy)

                return dict([choice_x, choice_y])

            return {STILL: 1}
