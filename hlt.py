import sys
from collections import namedtuple
from itertools import chain, zip_longest
import numpy as np


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


NORTH, EAST, SOUTH, WEST, STILL = range(5)


def opposite_cardinal(direction):
    """Returns the opposing cardinal direction."""
    return (direction + 2) % 4 if direction != STILL else STILL


Square = namedtuple('Square', 'x y owner strength production')


Move = namedtuple('Move', 'x y direction')


class GameMap:
    def __init__(self, size_string, production_string, map_string=None):
        self.width, self.height = tuple(map(int, size_string.split()))
        self.production = tuple(tuple(map(int, substring))
                                for substring in grouper(production_string.split(), self.width))
        self.contents = None
        self.get_frame(map_string)
        self.starting_player_count = len(set(square.owner for square in self)) - 1

    def get_frame(self, map_string=None):
        """Updates the map information from the latest frame provided by the Halite game environment."""
        if map_string is None:
            map_string = get_string()
        split_string = map_string.split()
        owners = list()
        while len(owners) < self.width * self.height:
            counter = int(split_string.pop(0))
            owner = int(split_string.pop(0))
            owners.extend([owner] * counter)
        assert len(owners) == self.width * self.height
        assert len(split_string) == self.width * self.height
        self.contents = [[Square(x, y, owner, strength, production)
                          for x, (owner, strength, production)
                          in enumerate(zip(owner_row, strength_row, production_row))]
                         for y, (owner_row, strength_row, production_row)
                         in enumerate(zip(grouper(owners, self.width),
                                          grouper(map(int, split_string), self.width),
                                          self.production))]

    def __iter__(self):
        """Allows direct iteration over all squares in the GameMap instance."""
        return chain.from_iterable(self.contents)

    def neighbors(self, square, n=1, include_self=False):
        """Iterable over the n-distance neighbors of a given square.  For single-step neighbors,
        the enumeration index provides the direction associated with the neighbor."""
        assert isinstance(include_self, bool)
        assert isinstance(n, int) and n > 0
        if n == 1:
            # NORTH, EAST, SOUTH, WEST, STILL ... matches indices provided by enumerate(game_map.neighbors(square))
            combos = ((0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))
        else:
            combos = ((dx, dy) for dy in range(-n, n+1) for dx in range(-n, n+1) if abs(dx) + abs(dy) <= n)
        return (self.contents[(square.y + dy) % self.height][(square.x + dx) % self.width]
                for dx, dy in combos if include_self or dx or dy)

    def get_target(self, square, direction):
        """"Returns a single, one-step neighbor in a given direction."""
        dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))[direction]
        return self.contents[(square.y + dy) % self.height][(square.x + dx) % self.width]

    def get_direction(self, coord1, coord2, room):
        """Returns shortest direction between two coordinates (X or Y). Need this because of wrapparound"""
        d_straight = coord2 - coord1
        d_wrapped = (coord2 - room) - coord1
        if abs(d_straight) < abs(d_wrapped):
            return d_straight
        else:
            return d_wrapped

    def get_distance(self, sq1, sq2):
        """"Returns Manhattan distance between two squares."""
        dx = min(abs(sq1.x - sq2.x), sq1.x + self.width - sq2.x, sq2.x + self.width - sq1.x)
        dy = min(abs(sq1.y - sq2.y), sq1.y + self.height - sq2.y, sq2.y + self.height - sq1.y)
        return dx + dy


class NumpyGameMap:
    """Just like GameMap but loads the info in a numpy array"""

    def __init__(self, size_string, production_string, map_string=None):

        self.width, self.height = tuple(map(int, size_string.split()))

        self.owners = None
        self.strength = None
        self.production = np.array([int(s) for s in production_string.split()]).reshape(self.height, self.width)

        self.get_frame(map_string)

    def get_frame(self, map_string=None):
        """Updates the map information from the latest frame provided by the Halite game environment."""
        map_string = map_string or get_string()
        split_string = map_string.split()

        owners = []
        counters = []
        while sum(counters) < self.width * self.height:
            counters.append(int(split_string.pop(0)))
            owners.append(int(split_string.pop(0)))
        self.owners = np.repeat(owners, counters).reshape(self.height, self. width)

        assert len(split_string) == self.width * self.height
        self.strength = np.array([int(s) for s in split_string]).reshape(self.height, self.width)

    def neighbours_address(self, i, j):
        """Iterable over the n-distance neighbors of a given square.  For single-step neighbors,
        the enumeration index provides the direction associated with the neighbor."""
        # NORTH, EAST, SOUTH, WEST, STILL ... matches indices provided by enumerate(game_map.neighbors(square))
        combos = ((-1, 0), (0, 1), (1, 0), (0, -1), (0, 0))
        return (((i + dx) % self.height, (j + dy) % self.width) for dx, dy in combos)


def get_direction_to_target_mask(i, j, others, shape):
    """calculate, for every pair of coordinates in 'others', the shortest 2D directional vector
    (watch out for wraparound)"""
    distance_straight = others - np.array([[i], [j]])
    distance_wrapped = (others - np.array([[shape[0]], [shape[1]]])) - np.array([[i], [j]])

    better_straight = np.abs(distance_straight) < np.abs(distance_wrapped)

    shortest = np.empty(shape=distance_straight.shape, dtype=np.int)
    shortest[better_straight] = distance_straight[better_straight]
    shortest[~better_straight] = distance_wrapped[~better_straight]

    return shortest


def direction_to_cardinal(direction):
    """convert a tuple of integers indicating a 2D vector into a dictionary where the key is a cardinal actions and the
    value the number of times it needs to be repeated"""

    cardinals = {}

    if direction[0] < 0:
        cardinals[NORTH] = abs(direction[0])
    elif direction[0] > 0:
        cardinals[SOUTH] = abs(direction[0])

    if direction[1] < 0:
        cardinals[WEST] = abs(direction[1])
    elif direction[1] > 0:
        cardinals[EAST] = abs(direction[1])

    if not cardinals:
        return {STILL: 1}
    else:
        return cardinals


#################################################################
# Functions for communicating with the Halite game environment  #
#################################################################


def send_string(s):
    sys.stdout.write(s)
    sys.stdout.write('\n')
    sys.stdout.flush()


def get_string():
    return sys.stdin.readline().rstrip('\n')


def get_init():
    player_id = int(get_string())
    m = NumpyGameMap(get_string(), get_string())
    return player_id, m


def send_init(name):
    send_string(name)


def translate_cardinal(direction):
    """"Translate direction constants used by this Python-based bot framework
    to that used by the official Halite game environment."""
    return (direction + 1) % 5


def send_frame(moves):
    send_string(' '.join(str(move.x) + ' ' + str(move.y) + ' ' +
                         str(translate_cardinal(move.direction)) for move in moves))
