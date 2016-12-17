import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move
import random
import numpy as np


class Bot(object):
    def __init__(self, name='Bot'):
        self.my_id, self.game = hlt.get_init()
        hlt.send_init(name)

    def assign_moves(self, rows, cols):
        moves = np.array([STILL] * rows.size)
        return [Move(j, i, m) for (i, j, m) in zip(rows, cols, moves)]

    def run(self):
        while True:
            self.game.get_frame()
            rows, cols = np.where(self.game.owners == self.my_id)
            moves = self.assign_moves(rows, cols)
            hlt.send_frame(moves)


class RandomBot(Bot):
    def __init__(self):
        super(RandomBot, self).__init__("RandomBot")

    def assign_moves(self, rows, cols):
        moves = np.random.choice((NORTH, EAST, SOUTH, WEST, STILL), rows.size)
        return [Move(j, i, m) for (i, j, m) in zip(rows, cols, moves)]


class BlobBot(Bot):
    def __init__(self):
        super(BlobBot, self).__init__("BlobBot")

    def assign_move(self, i, j):

        my_strength = self.game.strength[i, j]
        for direction, address in enumerate(self.game.neighbours_address(i, j)):
            n_owner = self.game.owner[address[0], address[1]]
            n_strength = self.game.strength[address[0], address[1]]
            if n_owner != self.my_id and n_strength < my_strength:
                return Move(j, i, direction)

        if all(self.game.owners[address[0], address[1]] == self.my_id
               for address in self.game.neighbours_address(i, j)):
            return Move(j, i, random.choice((NORTH, WEST, SOUTH, EAST)))

        return Move(j, i, STILL)

    def assign_moves(self, rows, cols):
        return [self.assign_move(i, j) for (i, j) in zip(rows, cols)]


class PowerBlobBot(Bot):
    def __init__(self):
        super(PowerBlobBot, self).__init__("PowerBlobBot")

    def assign_move(self, i, j):
        my_strength = self.game.strength[i, j]
        for direction, address in enumerate(self.game.neighbours_address(i, j)):
            n_owner = self.game.owners[address[0], address[1]]
            n_strength = self.game.strength[address[0], address[1]]
            if n_owner != self.my_id and n_strength < my_strength:
                return Move(j, i, direction)

        if all(self.game.owners[address[0], address[1]] == self.my_id
               for address in self.game.neighbours_address(i, j)):
            if my_strength < 128:
                return Move(j, i, STILL)
            else:
                return Move(j, i, random.choice((NORTH, WEST, SOUTH, EAST)))

        return Move(j, i, STILL)

    def assign_moves(self, rows, cols):
        return [self.assign_move(i, j) for (i, j) in zip(rows, cols)]


class HeuristicBot(Bot):
    def __init__(self):
        super(HeuristicBot, self).__init__("HeuristicBot")

    def assign_moves(self, rows, cols):
        moves = []

        for i, j in zip(rows, cols):
            if self.game.strength[i, j] > 16:
                others = np.array(np.where(self.game.owners != self.my_id))

                others_strength = self.game.strength[[others[0], others[1]]]
                others_production = self.game.production[[others[0], others[1]]]

                others_direction = hlt.get_direction_to_target_mask(i, j, others, self.game.owners.shape)
                others_distance = np.sum(np.abs(others_direction), axis=0)

                heuristic = others_production / (others_distance * np.maximum(others_strength, 1))
                closest_idx = np.argmax(heuristic)

                cardinals = hlt.direction_to_cardinal(others_direction[:, closest_idx])
                options, probs = zip(*cardinals.items())
                probs = 1 / np.array(probs)  # invert so we close the shortest distance first
                probs /= np.sum(probs)
                d = np.random.choice(options, p=probs)

                moves.append(Move(j, i, d))
            else:
                moves.append(Move(j, i, STILL))

        return moves
