#!/usr/bin/python3
"""
  Snackade! - A game of snacking and cutting off your opponent
              Play head to head or against the computer!

MIT License

Copyright (c) 2021 Brian Corriveau  https://github.com/bcorriveau/snackade

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

Caterpillar Walk - Copyright Nicole Corriveau 2020, permission granted to use in Snackade
                   as background music.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import pygame
from pygame.mixer import Sound, get_init, pre_init
from array import array
from time import sleep
from enum import Enum
from random import randint

pre_init(44100, -16, 1, 2048)
successes, failures = pygame.init()

font1 = pygame.font.SysFont("monospace", 16)
font2 = pygame.font.SysFont("monospace", 32)
clock = pygame.time.Clock()

# Colours for the game
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_RED = (255, 99, 71)
RED = (255, 0, 0)
DARK_RED = (139, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Game piece / Sprite values - each sprint adds its value to a grid location
GVAL_CLEAR = 0
GVAL_BORDER = 1
GVAL_PLAYER = 1
GVAL_OCCUPIED = 1
GVAL_SNACK = 10

BORDER_RADIUS = 6
BORDER_WIDTH = BORDER_RADIUS * 2 + 1

# need border offsets + border width offset!!
BORDER_XOFF = BORDER_WIDTH
BORDER_YOFF = 50

GRID_XOFF = BORDER_XOFF + BORDER_RADIUS + 1
GRID_YOFF = BORDER_YOFF + BORDER_RADIUS + 1

PLAYER_XSIZE = 32
PLAYER_YSIZE = 32

# Grid size
GRID_XSIZE = 23
GRID_YSIZE = 15

# Directions for sprites
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# maps from distance to simple direction, e.g. 10 becomes 1, -10 becomes -1
dir_map = lambda x: 0 if x == 0 else abs(x) // x


# Set up grid to check for collisions
def init_grid(grid):

    if grid == None:
        grid = [[] for x in range(0, GRID_XSIZE+1)]

    for x in range(0, GRID_XSIZE+1):
        grid[x]= [0 for y in range(0, GRID_YSIZE+1)]

    for x in range(0,GRID_XSIZE+1):
        grid[x][0] = GVAL_BORDER
        grid[x][GRID_YSIZE] =  GVAL_BORDER
    for y in range(0,GRID_YSIZE+1):
        grid[0][y] = GVAL_BORDER
        grid[GRID_XSIZE][y] = GVAL_BORDER

    return grid


class Tone(Sound):

    def __init__(self, frequency, volume=.1):
        self.frequency = frequency
        Sound.__init__(self, self.build_samples())
        self.set_volume(volume)

    def build_samples(self):
        period = int(round(get_init()[0] / self.frequency))
        samples = array("h", [0] * period)
        amplitude = 2 ** (abs(get_init()[1]) - 1) - 1
        for time in range(period):
            if time < period / 2:
                samples[time] = amplitude
            else:
                samples[time] = -amplitude
        return samples


def sound_start():
    freq = 100
    for i in range(1,20):
        Tone(freq).play(5)
        sleep(0.1)
        freq += 50

def sound_chomp():
    Tone(400).play(4)
    sleep(0.05)
    Tone(540).play(4)
    sleep(0.05)
    Tone(660).play(4)

def sound_crash():
    Tone(40).play(5)


class NoteLoop:
    # Tone names and frequencies supported
    NOTE_NAMES = { 'B2':123,  'C2':131, 'C2#':139, 'D2':147, 'E2b':156, 'E2':165, 'F2#':185, 'G2':196,
                   'A3b':208, 'A3':220, 'B3':247,  'C3':262, 'C3#':277, 'D3':293,
                   'E3b':311, 'E3':330, 'F3':349,
                   None:0 }

    def __init__(self, tones):
        """
        Initialize tone loop
        :param tone_list: list of tone names and duration tuples to play one at a time in a loop
        """
        self.tones = tones
        self.next = 0

    def play_next(self):
        freq_name,duration = self.tones[self.next]
        # if tone is not None then play it for the duration
        if freq_name in self.NOTE_NAMES:
            freq = self.NOTE_NAMES[freq_name]
            if freq:
                Tone(freq).play(duration)
        else:
            print('note error on {}'.format(freq_name))
        self.next +=1
        if self.next >= len(self.tones):
            self.next = 0


def wait_anykey():
    """
    Waits for any key to be pressed
    :return:    the key that was pressed
    """

    # pump the events and wait a bit to get them flowing
    pygame.event.pump()
    sleep(0.2)
    pygame.event.clear()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                return chr(event.key)
        clock.tick(5)


def write_text(screen, text, x, y, font = font1):
    y_offset = 0
    for line in text:
        msg1 = font.render(line, 10, (255, 255, 255))
        screen.blit(msg1, (x,y + y_offset))
        y_offset += 18
    pygame.display.update()


def clear_text(screen, lines, x, y, chars):
    y_offset = 18 * lines
    blankmsg = pygame.Rect((x, y), ((chars * 10), y_offset))
    pygame.draw.rect(screen, BLACK, blankmsg)
    pygame.display.update()


def end_game(screen, p1crash, p2crash):
    if p1crash and p2crash:
        write_text(screen, ['Both players crashed!!'], 250, 524)
    elif p1crash:
        write_text(screen, ['Blue player wins!'], 250, 524)
    else:
        write_text(screen, ['Green player wins!'], 250, 524)
    sleep(2)
    clear_text(screen, 1, 250, 524, 25)


def play_again(screen):
    write_text(screen, ['Play Again? (y/n)'], 250, 524)
    inkey = wait_anykey()
    clear_text(screen, 1, 250, 524, 20)
    return inkey == 'y'


# Display intro and get the game play selection
#     return TRUE if computer player, FALSE if head to head
def intro_select(screen):
    write_text(screen, ['Snackade!'],280, 6, font2)
    write_text(screen, ['         Eat snacks and cut the other',
                        '         player off without crashing!',
                        ' ',
                        '    Green Control             Blue Control',
                        '        (up)                      (up)',
                        '         W                         I',
                        '(left) A   D (right)      (left) J   L (right)',
                        '         S                         K',
                        '       (down)                    (down)',
                        ' ',
                        ' ',
                        '          Press h to play head to head or',
                        '          Press c to play the computer'], 150, 200)
    while True:
        key = wait_anykey()
        if key == 'h' or key == 'c':
            break

    if key == 'c':
        clear_text(screen, 5, 410, 272, 20)
        write_text(screen, ['    Computer!'], 420, 308)
        sleep(2)
    clear_text(screen, 13, 150, 200, 50)
    return key == 'c'

def display_game_status(screen, p1, p2):
    clear_text(screen, 2, 250, 541, 25)
    write_text(screen, ['Green Points:{:2d}  Wins:{:2d}'.format(p1.points, p1.wins),
                        'Blue  Points:{:2d}  Wins:{:2d}'.format(p2.points, p2.wins)], 250, 541)

# Class to hold all the game presentation data and methods
class GameBox:
    def __init__(self, screen):
        self.screen = screen
        self.border = pygame.Rect((BORDER_XOFF, BORDER_YOFF),
                                  (GRID_XSIZE * PLAYER_XSIZE - BORDER_WIDTH,
                                   GRID_YSIZE * PLAYER_YSIZE - BORDER_WIDTH))

        self.game_area = pygame.Rect((GRID_XOFF, GRID_YOFF),
                                     ((GRID_XSIZE - 1) * PLAYER_XSIZE + BORDER_RADIUS - 1,
                                      (GRID_YSIZE - 1) * PLAYER_YSIZE + BORDER_RADIUS - 1))
        self.grid = init_grid(None)
        self.snack_location = None

    def display_border(self):
        pygame.draw.rect(self.screen, WHITE, self.border, BORDER_WIDTH)

    def clear_game_area(self):
        pygame.draw.rect(self.screen, BLACK, self.game_area)

    def screen_x(self, gx):
        return (gx-1) * PLAYER_XSIZE + GRID_XOFF

    def screen_y(self, gy):
        return (gy-1) * PLAYER_YSIZE + GRID_YOFF

    def grid_reset(self):
        self.grid = init_grid(self.grid)
        self.snack_location = None

    def grid_setval(self, gx, gy, value):
        self.grid[gx][gy] = value

    def grid_upval(self, gx, gy, value):
        self.grid[gx][gy] += value
        if value == GVAL_SNACK:
            self.snack_location = (gx, gy)
        elif value == -GVAL_SNACK:
            self.snack_location = None

    def grid_val(self, gx, gy):
        return self.grid[gx][gy]


class GridSprite:

    def __init__(self, gbox, gx, gy, colour, sprite_value):
        self.gbox = gbox
        self.colour = colour
        self.sprite_value = sprite_value

    def place(self, gx, gy):
        """
        Place sprite on grid by setting its value
        """
        self.gx = gx
        self.gy = gy
        self.gbox.grid_upval(gx, gy, self.sprite_value)

    def remove(self, gx, gy):
        """
        Remove sprite from grid, subtract value from grid location
        """
        self.gbox.grid_upval(gx, gy, -self.sprite_value)

    def location(self):
        return self.gx, self.gy


class Snack(GridSprite):
    def __init__(self, gbox):
        # find an empty spot on the grid for the snack
        while True:
            gx = randint(2,GRID_XSIZE-1)
            gy = randint(2,GRID_YSIZE-1)
            if gbox.grid_val(gx, gy) == GVAL_CLEAR:
                break

        # set value and colour of snack
        self.value = randint(1,3)
        if self.value > 2:
            colour = DARK_RED
        elif self.value > 1:
            colour = RED
        else:
            colour = LIGHT_RED

        super().__init__(gbox, gx, gy, colour, GVAL_SNACK)
        self.place(gx, gy)
        self.image = pygame.Surface((PLAYER_XSIZE, PLAYER_YSIZE))
        self.image.fill(colour)
        self.rect = pygame.Rect(gbox.screen_x(self.gx)+10, gbox.screen_y(self.gy)+10, 18, 18)
        pygame.draw.rect(gbox.screen, colour, self.rect, 6)

    def clear(self):
        """
        Clear snack from screen and remove value from grid
        """
        self.image.fill(BLACK)
        pygame.draw.rect(self.gbox.screen, BLACK, self.rect, 6)
        self.remove(self.gx, self.gy)


class Player(GridSprite):

    class Status(Enum):
        CLEAR = 0
        CHOMP = 1
        COLLISION = 2

    def __init__(self, gbox, gx, gy, colour, move_chars):
        """
        Initialize player
        :param screen:  screen to draw player
        :param gx:      grid x to start player
        :param gy:      grid y to start player
        :param colour:  colour of player
        :param sprite_value: value to place on the grid for player
        :param move_chars:   list with up,down,left,right characters for control
        """
        super().__init__(gbox, gx, gy, colour, GVAL_PLAYER)
        self.wins = 0
        self.points = 0
        self.image = pygame.Surface((PLAYER_XSIZE, PLAYER_YSIZE))
        self.image.fill(self.colour)
        self.set_head(gx, gy)
        self.move_key = {}
        # set up, down, left, right vectors for keys if defined
        if len(move_chars) == 4:
            self.move_key[ord(move_chars[0])] = UP
            self.move_key[ord(move_chars[1])] = DOWN
            self.move_key[ord(move_chars[2])] = LEFT
            self.move_key[ord(move_chars[3])] = RIGHT
        else:
            self.move_key = []

        self.rect = pygame.Rect(gbox.screen_x(self.gx), gbox.screen_y(self.gy),
                                gbox.screen_x(self.gx + 1), gbox.screen_y(self.gy + 1))
        self.status = self.Status.CLEAR

    def set_head(self, gx, gy):
        self.place(gx, gy)
        self.trail = []
        self.grow(2)
        self.trail.append((self.gx, self.gy))
        self._draw_seg(self.gx, self.gy, self.colour)

    def set_direction(self, dx, dy):
        """
        Sets player's direction
        :param dx:  dx part of direction vector
        :param dy:  dy part of direction vector
        :return:
        """
        self.dx, self.dy = dx, dy

    def grow(self, segments, points=0):
        """
        Grow the player
        :param segments:    number of segments to grow
        :param points:      points to add to score, default 0
        :return:            None
        """
        for i in range(0,segments):
            self.trail.append((self.gx,self.gy))
            self.place(self.gx, self.gy)
        self.points += points

    def move(self):
        # return if no move
        if not (self.dx or self.dy):
            return

        self.place(self.gx + self.dx, self.gy + self.dy)
        self.trail.append((self.gx, self.gy))
        self.rect.move_ip(self.dx * PLAYER_XSIZE, self.dy * PLAYER_YSIZE)
        self.tail = self.trail.pop(0)
        self.remove(self.tail[0], self.tail[1])

    def update_status(self):
        # check for collisions and chomping...
        value = self.gbox.grid_val(self.gx, self.gy)
        if (value > GVAL_PLAYER and value < GVAL_SNACK) or \
          value == GVAL_PLAYER + GVAL_PLAYER + GVAL_SNACK:
            self.status = self.Status.COLLISION
        elif value == GVAL_PLAYER + GVAL_SNACK:
            self.status = self.Status.CHOMP
        else:
            self.status = self.Status.CLEAR

    def _draw_seg(self, gx, gy, colour):
        rect = pygame.Rect((self.gbox.screen_x(gx)+5, self.gbox.screen_y(gy)+5),
                                  (PLAYER_XSIZE-5, PLAYER_YSIZE-5))
        pygame.draw.rect(self.gbox.screen, colour, rect, 6)

    def draw(self):
        # draw head and remove tail
        self._draw_seg(self.gx, self.gy, self.colour)
        tx, ty = self.tail
        if self.gbox.grid_val(tx, ty) == GVAL_CLEAR:
            self._draw_seg(tx, ty, BLACK)

    def draw_crash(self):
        gx = self.gx - self.dx
        gy = self.gy - self.dy

        rect = pygame.Rect((self.gbox.screen_x(gx)+5, self.gbox.screen_y(gy)+5),
                                  (PLAYER_XSIZE-5, PLAYER_YSIZE-5))
        pygame.draw.rect(self.gbox.screen, self.colour, rect, 10)


class ComputerPlayer(Player):

    RIGHT_TURN = {UP:RIGHT, RIGHT:DOWN, DOWN:LEFT, LEFT:UP}
    LEFT_TURN  = {UP:LEFT, LEFT:DOWN, DOWN:RIGHT, RIGHT:UP}

    # Dictionary of turns to make when a snack appears. Given the direction of the
    # snack and the current direction of the computer player, give the direction to
    # head to go towards the snack
    #
    #  Direction of snack, current direction -> direction to head
    #
    SNACK_TURN = {
        (0, -1):    { UP:UP,    DOWN:LEFT,  LEFT:UP,    RIGHT:UP},
        (1, -1):    { UP:UP,    DOWN:RIGHT, LEFT:UP,    RIGHT:RIGHT},
        (1,  0):    { UP:RIGHT, DOWN:RIGHT, LEFT:UP,    RIGHT:RIGHT},
        (1,  1):    { UP:RIGHT, DOWN:RIGHT, LEFT:DOWN,  RIGHT:RIGHT},
        (0,  1):    { UP:RIGHT, DOWN:DOWN,  LEFT:DOWN,  RIGHT:DOWN},
        (-1, 1):    { UP:LEFT,  DOWN:DOWN,  LEFT:LEFT,  RIGHT:DOWN},
        (-1, 0):    { UP:LEFT,  DOWN:LEFT,  LEFT:LEFT,  RIGHT:DOWN},
        (-1, -1):   { UP:UP,    DOWN:LEFT,  LEFT:LEFT,  RIGHT:UP}
    }

    # Set the computer player up just like regular player, except no key controls
    def __init__(self, gbox, gx, gy, colour):
        super().__init__(gbox, gx, gy, colour, [])

    def move(self):
        # calculate turn options
        turn_options = [(self.dx, self.dy),
                        self.RIGHT_TURN[(self.dx, self.dy)],
                        self.LEFT_TURN[(self.dx, self.dy)]]

        # if there is a snack then head towards it, otherwise default same direction
        if self.gbox.snack_location:
            snack_x, snack_y = self.gbox.snack_location
            sx, sy = dir_map(snack_x - self.gx), dir_map(snack_y - self.gy)
            dx, dy = self.SNACK_TURN[(sx, sy)][(self.dx, self.dy)]
        else:
            dx,dy = self.dx, self.dy

        # if about to crash then turn if it helps
        gval_infront = self.gbox.grid_val(self.gx + dx, self.gy + dy)
        if gval_infront and gval_infront < GVAL_SNACK:
            for dx, dy in turn_options:
                if self.gbox.grid_val(self.gx + dx, self.gy + dy) == GVAL_CLEAR:
                    break

        self.set_direction(dx, dy)
        super().move()

def play(gbox, p1, p2):

    snack = None
    play_chomp = False
    display_game_status(gbox.screen, p1, p2)

    # Caterpillar Walk - Copyright Nicole Corriveau 2020, permission granted to use in Snackade
    background_loop = NoteLoop([('F3',5), ('C3',5), ('A3b',5), ('C3',5), ('C2',5), ('C3',5), ('A3b',5),
                                ('C3',5), ('F3',5), ('C3',5), ('A3b',5), ('C3',5), ('C2',5), ('D2',5),
                                ('E2b',5), ('E2',5)])

    # update sounds and screen only every 2 ticks
    update_cycle = True
    while True:
        # 10 ticks allowed per second
        clock.tick(10)
        update_cycle = not update_cycle

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

            # check if key press matches a player mover key and update direction if matched
            elif event.type == pygame.KEYDOWN:
                for p in [p1,p2]:
                    if event.key in p.move_key:
                        dx, dy = p.move_key[event.key]
                        p.set_direction(dx,dy)

        # are we on the second cycle?
        if not update_cycle:
            continue

        background_loop.play_next()

        # random snack event to create or remove snack
        if randint(1, 15) == 15:
            if snack:
                if randint(1, 5) == 5:
                    snack.clear()
                    snack = None
            else:
                snack = Snack(gbox)

        # first move to new positions
        p1.move()
        p2.move()

        # update player statuses
        for p in [p1, p2]:
            p.update_status()
            if p.status == Player.Status.COLLISION:
                p.draw_crash()
            elif p.status == Player.Status.CHOMP:
                p.grow(snack.value, snack.value)
                snack.clear()
                snack = None
                play_chomp = True
                display_game_status(gbox.screen, p1, p2)

        # Check for crashes
        p1crash = p1.status == Player.Status.COLLISION
        p2crash = p2.status == Player.Status.COLLISION

        # update positions if not crashed
        for p in [p1, p2]:
            if not p.status == Player.Status.COLLISION:
                p.draw()

        if p1crash or p2crash:
            sound_crash()
            end_game(gbox.screen, p1crash, p2crash)
            if not p1crash:
                p1.wins += 1
            if not p2crash:
                p2.wins +=1
            return

        pygame.display.update()
        # play chomp after updating the screen to keep animation smooth
        if play_chomp:
            sound_chomp()
            play_chomp = False


def main():
    screen = pygame.display.set_mode((750, 580))
    gbox = GameBox(screen)
    gbox.display_border()
    p1 = Player(gbox, 1, 4, GREEN, ['w','s','a','d'])
    p2 = Player(gbox, 22, 4, BLUE, ['i','k','j','l'])
    computer_plays = intro_select(screen)
    if computer_plays:
        gbox.grid_reset()
        p1 = Player(gbox, 1, 4, GREEN, ['w','s','a','d'])
        p2 = ComputerPlayer(gbox, 22, 4, BLUE)
    while True:
        p1.set_direction(1, 0)
        p2.set_direction(-1, 0)
        pygame.display.update()
        sound_start()
        play(gbox, p1, p2)
        display_game_status(screen, p1, p2)
        if play_again(screen):
            gbox.grid_reset()
            gbox.clear_game_area()
            p1.set_head(1, 4)
            p2.set_head(22 ,4)
        else:
            break


if __name__ == '__main__':
    main()
