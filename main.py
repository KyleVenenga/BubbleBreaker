# BubbleBreaker
# A bubble game, when more bubbles are joined together, the higher the value recieved when bursting them.
# Kyle Venenga
# August 2019

import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Rectangle
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import ScreenManager, Screen
import random
from kivy.config import Config
from kivy.graphics import Color
import copy
from kivy.properties import StringProperty
from kivy.core.audio import SoundLoader
from kivy.graphics.vertex_instructions import (Rectangle, Ellipse)
from kivy.core.image import Image as CoreImage
import numpy
import gc

from kivy.graphics.instructions import Instruction
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '800')

Builder.load_file('board.kv')

# vars
# Holds a few global arrays for altering within functions
# - Made because when setting array.empty() breaks Android version. Also, doesn't work to set
#   array = [] in a function, as it's trying to declare a new array with the same name.
class vars():
    connected = []
    previous = []

##################################################################################################
# GLOBAL VARIABLES
##################################################################################################

# Holds the vars class objects for connected bubbles, and previous bubbles.
glob = vars()

# Scores [Total Score, Selected Total, Easy High, Med High, Hard High]
scores = [0, 0, 0, 0, 0]

# Board Dimensions [X, Y]
boardDim = [13, 24]

# If the game is muted or not
mute = [False]

# Holds information for the group point bubble
groupPos = [0, 0]

# Information for the grouped score [Widget, Score Number Texture]
GroupBubs = [None, None]

# Holds the difficulty of the game, 4-6 (each for how many bubbles are displayed in the game)
difficulty = [4]

# Text that is shown during the game over message
gameOverTxt = ['']


##################################################################################################
# FUNCTIONS
##################################################################################################

# updateHighScores
# Updates the high scores for the game from the text file
def updateHighScores():
    with open('highScore.txt', 'r') as hs:
        data = hs.readlines()

    scores[2] = int(data[0])
    scores[3] = int(data[1])
    scores[4] = int(data[2])


# Update the scores right away to pull from the file
updateHighScores()


# checkHighScore
# Checks to see if the score from the currently finished game is a new high score or not
# If it is, we will change the high score and the game over text accordingly
def checkHighScore():
    hs = open('highScore.txt', "r")
    # Get the line of the file for particular difficulty high score
    line = difficulty[0] - 4
    with open('highScore.txt', 'r') as hs:
        data = hs.readlines()
    if int(data[line]) < scores[0]:
        changeHighScore(data)
        gameOverTxt[0] = 'New High Score: ' + str(scores[0])
        updateHighScores()
    else:
        gameOverTxt[0] = 'Score: ' + str(scores[0])
    hs.close()


# clearPrevCon
# Clears all of the arrays holding the last moves data
def clearPrevCon():
    for con in glob.connected:
        con.clicked = False
    glob.connected = []
    glob.previous = []


# changeHighScore
# Takes in an array for the three high scores, updates the file with the new scores
def changeHighScore(data):
    line = difficulty[0] - 4
    data[line] = str(scores[0]) + '\n'
    with open('highScore.txt', 'w') as hs:
        hs.writelines(data)


# findTopLeft
# Finds the top left bubble in the currently selected bubbles, this will be the location that the
#   connected bubble score bubble will appear.
# Return the bubble in the upper left
def findTopLeft():
    if len(glob.connected) == 0:
        return
    temp = glob.connected[0]
    for con in glob.connected:
        if con.XCord < temp.XCord:
            temp = con
        elif con.YCord < temp.YCord and con.XCord == temp.XCord:
            temp = con
    return temp


# displayGroupTotal
# Displays the total points bubble by grabbing the top left location, then displaying the bubble
def displayGroupTotal():
    topLeft = findTopLeft()
    topLeft.displayGroupScore()


# calculateTotal
# Adds up the total score after each round
def calculateTotal():
    scores[0] += scores[1]
    scores[1] = 0
    screens[0].updateScore()


# calculateValue
# Calculates the value of all of the connected bubbles. This will be used to display in the bubble for the
#   Player, as well as adding the score up if these bubbles are broken.
def calculateValue():
    scores[1] = len(glob.connected) * len(glob.connected)
    screens[0].updateScore()


# clearConnected
# Clears the connected bubbles from their background being white, and sets the array of connected back to empty
def clearConnected():
    if len(glob.connected) > 0:
        for bub in glob.connected:
            bub.clicked = False
            bub.canvas.before.clear()
    glob.connected = []


# getPrev
# Gets the previous game board from the last move. This will be used to display the last played game
#   board when the user hits the undo button.
def getPrev():
    for row in screens[0].Bubbles:
        for bub in row:
            glob.previous.append([bub.XCord, bub.YCord, bub.bubColor, bub])


# popSelected
# Pops all of the bubbles that are currently connected by the user, then all of the bubbles above will move
#   down to their new spot, and the game board will be updated. Build the previous game board for the undo
#   button. Redisplay the game board.
def popSelected():
    glob.previous = []
    getPrev()
    screens[0].remove_widget(GroupBubs[0])
    conCoords = []

    # Build an array of connected coordinates
    for bub in glob.connected:
        if len(conCoords) == 0:
            conCoords.append([bub.XCord, bub.YCord])
        else:
            add = True
            for coord in conCoords:
                if bub.XCord == coord[0] and bub.YCord > coord[1]:
                    coord[1] = bub.YCord
                    add = False
                    break
                elif bub.XCord == coord[0]:
                    add = False
                    break
            if add is True:
                conCoords.append([bub.XCord, bub.YCord])

    # Cycle Through the coordinates and move all bubbles down.
    for con in conCoords:
        if con[1] != 0:
            for i in range(con[1], -1, -1):
                for s in range(i-1, -1, -1):
                    empSelf = True
                    if screens[0].Bubbles[con[0]][s].clicked is False:
                        emp = Empty()
                        emp.XCord = con[0]
                        emp.YCord = i
                        cur = []
                        cur = screens[0].allBubbles[con[0]][i]
                        col = screens[0].getColIndex(screens[0].Bubbles[con[0]][s].bubColor)
                        if col is None:
                            col = 6
                        screens[0].Bubbles[con[0]][s] = emp
                        screens[0].Bubbles[con[0]][i].canvas.before.clear()
                        screens[0].Bubbles[con[0]][i].clicked = False
                        screens[0].Bubbles[con[0]][i] = cur[col]
                        empSelf = False
                        break
                if empSelf is True:
                    emp = Empty()
                    emp.XCord = con[0]
                    emp.YCord = i
                    screens[0].Bubbles[con[0]][i].canvas.before.clear()
                    screens[0].Bubbles[con[0]][i].clicked = False
                    screens[0].Bubbles[con[0]][i] = emp
        else:
            emp = Empty()
            emp.XCord = con[0]
            emp.YCord = 0
            screens[0].Bubbles[con[0]][0].canvas.before.clear()
            screens[0].Bubbles[con[0]][0].clicked = False
            screens[0].Bubbles[con[0]][0] = emp

    if mute[0] is False:
        sound = SoundLoader.load('Sounds/burst.mp3')
        if sound:
            sound.play()
    screens[0].ids.grid.clear_widgets()
    screens[0].gameLoop()
    calculateTotal()


##################################################################################################
# CLASSES
##################################################################################################

# MyLabel
# Widget (Image) for implementing resizeable text
class MyLabel(Image):
    text = StringProperty('')

    def on_text(self, *_):
        # Just get large texture:
        l = Label(text=self.text)
        l.font_size = '1000dp'  # something that'll give texture bigger than phone's screen size
        l.texture_update()
        # Set it to image, it'll be scaled to image size automatically:
        self.texture = l.texture


# difficultyPop
# Widget/Popup class for popup to change the difficulty of the game
class difficultyPop(Popup):
    def __init__(self, **kwargs):
        super(difficultyPop, self).__init__(**kwargs)

    # updateDiffiuclty
    # Called when the button is pressed within the popup. Takes in an int for the difficulty value
    #   Changes the image for the button to indicate its current difficulty.
    def updateDifficulty(self, dif):
        self.dismiss()
        if dif == 4:
            screens[0].ids.dif.canvas.after.clear()
            with screens[0].ids.dif.canvas.after:
                Rectangle(pos=(screens[0].ids.dif.x + (screens[0].ids.dif.width * .25),
                               screens[0].ids.dif.y + (screens[0].ids.dif.height * .27)),
                          size=(screens[0].ids.dif.width * .5, screens[0].ids.dif.height * .5),
                          source="Images/four.png"
                          )
        if dif == 5:
            screens[0].ids.dif.canvas.after.clear()
            with screens[0].ids.dif.canvas.after:
                Rectangle(pos=(screens[0].ids.dif.x + (screens[0].ids.dif.width * .25),
                               screens[0].ids.dif.y + (screens[0].ids.dif.height * .27)),
                          size=(screens[0].ids.dif.width * .5, screens[0].ids.dif.height * .5),
                          source="Images/five.png"
                          )
        if dif == 6:
            screens[0].ids.dif.canvas.after.clear()
            with screens[0].ids.dif.canvas.after:
                Rectangle(pos=(screens[0].ids.dif.x + (screens[0].ids.dif.width * .25),
                               screens[0].ids.dif.y + (screens[0].ids.dif.height * .27)),
                          size=(screens[0].ids.dif.width * .5, screens[0].ids.dif.height * .5),
                          source="Images/six.png"
                          )

        difficulty[0] = dif
        screens[0].newGame()


# gameOver
# Popup widget for the game over popup. Displays the score, if it was the new high score, and a button - new game
class gameOver(Popup):
    def __init__(self, **kwargs):
        super(gameOver, self).__init__(**kwargs)

    # newGame
    # Called when the button is hit for new game. Starts a new game.
    def newGame(self):
        self.dismiss()
        screens[0].newGame()


# GroupScoreBubble
# Widget that appears when bubbles are selected, a small circle with the number of the group score of the bubs
# Appears in the upper left of the top left most bubble, or above the left most bubble if on the far left of the
# screen, so the score bubble is not cut off.
class GroupScoreBubble(FloatLayout):
    def __init__(self, **kwargs):
        super(GroupScoreBubble, self).__init__(**kwargs)

        self.x = groupPos[0]
        self.y = groupPos[1]

        with self.canvas.before:
            Ellipse(pos=(self.x, self.y), size=(self.width * .35, self.width * .35))
        with self.canvas:
            Ellipse(pos=(self.x, self.y),
                    size=(self.width * .35, self.width * .35),
                    texture=GroupBubs[1].texture)

    # updateScore
    # Updates the bubble for the score value
    def updateScore(self):
        #self.canvas.clear()
        with self.canvas:
            Ellipse(pos=(self.x, self.y), size=(self.width * .35, self.width * .35), texture=GroupBubs[1])


# Empty
# A widget class, much like a bubble (holds same data), however the widget is an empty, blank box.
#   Used as a filler for the grid where there are no bubbles.
class Empty(BoxLayout):
    def __init__(self, **kwargs):
        super(Empty, self).__init__(**kwargs)
        self.XCord = None       # Bubble Object Variable
        self.YCord = None       # Bubble Object Variable
        self.clicked = None     # Bubble Object Variable
        self.bubColor = None    # Bubble Object Variable
        self.emptRow = None     # If the row is an empty row
        self.emp = True         # Indicate this is an empty object


# Bubble
# Widget that the game is built around. Holds all of the information/functions for the bubbles. The grid for the
#   game is built off of Bubble widgets to start, and as they are deleted, replaced with Empty objects.
class Bubble(BoxLayout):
    def __init__(self, **kwargs):
        super(Bubble, self).__init__(**kwargs)
        self.bubColor = ''      # Char of the color the bubble is
        self.XCord = None       # Bubbles X Coord in the gird
        self.YCord = None       # Bubbles Y Coord in the grid
        self.clicked = False    # Whether the bubble is currently selected
        self.emptRow = None     # Used for Empty Object
        self.emp = False        # If it is empty or not
        self.GroupBub = None    # GroupScoreBubble object when selected

    # BubClicked
    # Called when the bubble is clicked. If the bubble was previously clicked, call the popSelected function
    #   If not, search for all of the connected bubbles of like color
    def BubClicked(self):
        # If it had not been clicked/selected
        if self.clicked is False:
            # If the GroupScoreBubble object exists, another group has been selected clear the widget
            if GroupBubs[0] is not None:
                screens[0].remove_widget(GroupBubs[0])
            # Clear all the previously connected
            clearConnected()
            # Find New Connected Bubbles
            self.findConnected()
            # Calculate their value
            calculateValue()
            # Change the bubbles backgrounds
            for bub in glob.connected:
               bub.selectedBackground()
            if len(glob.connected) > 1:
                displayGroupTotal()
            if mute[0] is False:
                sound = SoundLoader.load('Sounds/select.mp3')
                if sound:
                    sound.play()
        # If this bubble has been clicked/selected in the last click, destroy the bubbles.
        elif self.clicked is True:
            popSelected()

    # displayGroupScore
    # Build a group score object bubble with the groups score for this bubble.
    def displayGroupScore(self):
        if self.XCord > 0:
            groupPos[0] = self.x - 15
            groupPos[1] = self.y + 10
        else:
            groupPos[0] = self.x
            groupPos[1] = self.y + 10
        text = str(scores[1])
        if len(text) % 2 == 0:
            text = text.center(6)
        else:
            text = text.center(7)
        GroupBubs[1].text = text
        GroupBubs[0] = GroupScoreBubble()
        screens[0].add_widget(GroupBubs[0])

    # selectedBackground
    # Adds a background to the grid space for the bubble if its been selected
    def selectedBackground(self):
        with self.canvas.before:
            Rectangle(pos=self.pos, size=self.size)

    # findConnected
    # Finds all of the connected bubbles for this bubble. If Red it will find all reds connected to this bubble
    def findConnected(self):
        # Up
        if self.YCord > 0:
            bub = screens[0].Bubbles[self.XCord][self.YCord - 1]

            if bub.bubColor == self.bubColor and self.checkExists(bub) is False:
                self.addBub(bub)
        # Down
        if self.YCord < 23:
            bub = screens[0].Bubbles[self.XCord][self.YCord + 1]
            if bub.bubColor == self.bubColor and self.checkExists(bub) is False:
                self.addBub(bub)
        # Left
        if self.XCord > 0:
            bub = screens[0].Bubbles[self.XCord - 1][self.YCord]
            if bub.bubColor == self.bubColor and self.checkExists(bub) is False:
                self.addBub(bub)
        # Right
        if self.XCord < 12:
            bub = screens[0].Bubbles[self.XCord + 1][self.YCord]
            if bub.bubColor == self.bubColor and self.checkExists(bub) is False:
                self.addBub(bub)

    #addBub
    # Adds a bubble to the connected array, changes some data values
    def addBub(self, bub):
        if len(glob.connected) < 1:
            glob.connected.append(self)
            self.clicked = True
        glob.connected.append(bub)
        bub.clicked = True
        bub.findConnected()

    # checkExists
    # Checks if the bubble exists in the connected array
    def checkExists(self, bub):
        if len(glob.connected) == 0:
            return False
        for bubs in glob.connected:
            if bub is bubs:
                return True
        return False


# Board
# The game board screen, the heart of the game.
class Board(Screen):
    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)

        GroupBubs[1] = MyLabel()
        self.allBubbles = self.buildAllBubbles()    # All bubbles in the grid, 13/24 grid with 6 colors each
        self.Bubbles = self.buildBubbles()          # All of the bubbles on the game board 13x24 (random)
        self.displayBubbles()
        self.updateScore()

        # Temp Vars For Undo Button
        self.tempScore = scores[0]

    # updateScore
    # Function that updates the score text on the screen
    def updateScore(self):
        self.ids.totalScore.text = str(scores[0])
        self.ids.highScore.text = str(scores[difficulty[0] - 2])  + '\n'

    # checkColumn
    # Checks to see if there is a column empty, if so move everything over
    def checkColumn(self):
        checker = True
        for i in range(1, boardDim[0], +1):
            for x in range(1, boardDim[0], + 1):
                clear = True
                for y in range(0, boardDim[1], +1):
                    if self.Bubbles[x][y].bubColor is not None:
                        clear = False
                if clear is True and self.Bubbles[x][0].emptRow is not True:
                    self.moveColumns(x)

    # moveColumns
    # Moves the columns of bubbles over left or right when an entire column is empty. Columns collapse towards
    #   the center to remain a nice, visually appealing, game from start to finish
    def moveColumns(self, column):
        # If the column was on the right side of the grid, move the columns to the left
        if column > boardDim[0] / 2:
            for x in range(column, boardDim[0] - 1, +1):
                for y in range(0, boardDim[1], +1):
                    if self.Bubbles[x + 1][y].bubColor is None:
                        cur = self.allBubbles[x][y]
                        self.Bubbles[x + 1][y].emptRow = True
                        self.Bubbles[x][y] = cur[6]
                    else:
                        cur = self.allBubbles[x][y]
                        col = self.getColIndex(self.Bubbles[x + 1][y].bubColor)
                        self.Bubbles[x][y] = cur[col]
            for y in range(0, boardDim[1], +1):
                cur = self.allBubbles[boardDim[0] - 1][y]
                cur[6].emptRow = True
                self.Bubbles[boardDim[0] - 1][y] = cur[6]

        # If the column was on the left side, move all the columns to the right
        else:
            for x in range(column, 0, -1):
                for y in range(0, boardDim[1], +1):
                    if self.Bubbles[x - 1][y].bubColor is None:
                        cur = self.allBubbles[x][y]
                        cur[6].emptRow = True
                        self.Bubbles[x][y] = cur[6]
                    else:
                        cur = self.allBubbles[x][y]
                        col = self.getColIndex(self.Bubbles[x - 1][y].bubColor)
                        self.Bubbles[x][y] = cur[col]
            for y in range(0, boardDim[1], +1):
                cur = self.allBubbles[0][y]
                cur[6].emptRow = True
                self.Bubbles[0][y] = cur[6]

    # checkConnections
    # Checks to see if there are any remaining connections on the baord, if not end the game.
    def checkConnections(self):
        for y in range(0, 24, +1):
            for x in range(0, 13, +1):
                if self.Bubbles[x][y].bubColor is not None:
                    col = self.Bubbles[x][y].bubColor
                    # Up
                    if y > 0:
                        bub = self.Bubbles[x][y - 1]
                        if bub.bubColor == col:
                            return
                    # Down
                    if y < 23:
                        bub = self.Bubbles[x][y + 1]
                        if bub.bubColor == col:
                            return
                    # Left
                    if x > 0:
                        bub = self.Bubbles[x - 1][y]
                        if bub.bubColor == col:
                            return
                    # Right
                    if x < 12:
                        bub = screens[0].Bubbles[x + 1][y]
                        if bub.bubColor == col:
                            return
        checkHighScore()
        over = gameOver(size=(self.width * .75, self.height * .25))
        over.ids.score.text = gameOverTxt[0]
        over.open()

    # gameLoop
    # The core game loop, what happens after everything is done, and the next turn has arrived.
    def gameLoop(self):
        self.tempScore = scores[0]
        self.checkColumn()
        self.ids.grid.clear_widgets()
        self.displayBubbles()
        self.checkConnections()

    # displayBubbles
    # Displays all of the bubbles on the screen in a grid format
    def displayBubbles(self):
        for y in range(0, 24, +1):
            for x in range(0, 13, +1):
                self.ids.grid.add_widget(self.Bubbles[x][y])

    # buildAllBubbles
    # Builds all of the bubbles, one for each color for each grid space. Done at the beginning of the game.
    #   When a color is moved down, or a new game is started, objects are already made. No time creating new
    #   Objects and allocating more memory. Done when the game starts, not during.
    def buildAllBubbles(self):
        Bubbles = [[0 for y in range(24)] for x in range(13)]
        Bubbles.append([])

        for y in range(0, 24, +1):
            for x in range(0, 13, +1):
                curBubs = []
                for i in range(0, 6, +1):
                    cur = Bubble()
                    cur.XCord = x
                    cur.YCord = y
                    cur.bubColor = self.getColor(i)
                    cur.ids.img.source = self.getCol(cur.bubColor)
                    curBubs.append(cur)
                curBubs.append(Empty())
                curBubs[6].XCord = x
                curBubs[6].YCord = y
                Bubbles[x][y] = curBubs

        return Bubbles

    # buildBubbles
    # Builds the grid of bubbles that are to be shown on the screen. This is the current games grid. Utilizes
    # the AllBubbles array.
    def buildBubbles(self):
        Bubbles = [[0 for y in range(24)] for x in range(13)]

        for y in range(0, 24, +1):
            for x in range(0, 13, +1):
                cur = self.allBubbles[x][y]
                rand = random.randrange(0, difficulty[0], 1)
                Bubbles[x][y] = cur[rand]

        return Bubbles

    # getColIndex
    # Gets and returns the index location for a color, inputs a char, returns an int.
    def getColIndex(self, char):
        colors = ['R', 'B', 'G', 'Y', 'P', 'O']
        count = 0
        for col in colors:
            if col == char:
                return count
            count += 1

    # getCol
    # Inputs a char and returns the string for the file location of that colors image for displaying the bubble
    def getCol(self, char):
        if char is 'R':
            return 'Images/red.png'
        if char is 'B':
            return 'Images/blue.png'
        if char is 'G':
            return 'Images/green.png'
        if char is 'Y':
            return 'Images/yellow.png'
        if char is 'O':
            return 'Images/orange.png'
        if char is 'P':
            return 'Images/pink.png'

    # getColor
    # Inputs an index int, and returns what color lies at that index.
    def getColor(self, num):
        colors = ['R', 'B', 'G', 'Y', 'P', 'O']
        return colors[num]

    # newGame
    # Called when a new game is started, sets all of the values back to new game, and generates a new screen
    def newGame(self):
        clearPrevCon()
        for y in range(0, 24, +1):
            for x in range(0, 13, +1):
                for i in range(0, 6, +1):
                    self.allBubbles[x][y][i].canvas.before.clear()
                    if i == 6:
                        self.allBubbles[x][y][i].emptRow = False
        if mute[0] is False:
            sound = SoundLoader.load('Sounds/restart.mp3')
            if sound:
                sound.play()
        scores[0] = 0
        if GroupBubs[0] is not None:
            self.remove_widget(GroupBubs[0])
        self.Bubbles = [[]]
        self.Bubbles = self.buildBubbles()
        self.ids.grid.clear_widgets()
        self.displayBubbles()
        self.updateScore()
        gc.collect()

    # undo
    # When an undo button is hit, this will undo the last move the user made.
    def undo(self):
        if scores[0] == 0:
            return
        if GroupBubs[0] is not None:
            self.remove_widget(GroupBubs[0])
        for con in glob.connected:
            con.canvas.before.clear()
            con.clicked = False
        for prev in glob.previous:
            if prev[3].emptRow is True:
                prev[3].emptRow = False
            self.Bubbles[prev[0]][prev[1]] = prev[3]
        scores[0] = self.tempScore
        self.updateScore()
        self.ids.grid.clear_widgets()
        self.displayBubbles()
        glob.previous = []
        if mute[0] is False:
            sound = SoundLoader.load('Sounds/back.mp3')
            if sound:
                sound.play()

    # changeMute
    # Changes the mute status of the game, and indicates the current state on the button
    def changeMute(self):
        if mute[0] is False:
            mute[0] = True
            self.ids.sound.canvas.after.clear()
            with self.ids.sound.canvas.after:
                Rectangle(pos=(self.ids.sound.x + (self.ids.sound.width * .33),
                               self.ids.sound.y + (self.ids.sound.height * .32)),
                          size=(self.ids.sound.width * .35, self.ids.sound.height * .4),
                          source="Images/mute.png"
                          )
        else:
            mute[0] = False
            self.ids.sound.canvas.after.clear()
            with self.ids.sound.canvas.after:
                Rectangle(pos=(self.ids.sound.x + (self.ids.sound.width * .33),
                               self.ids.sound.y + (self.ids.sound.height * .32)),
                          size=(self.ids.sound.width * .35, self.ids.sound.height * .4),
                          source="Images/sound.png"
                          )

    # changeDifficulty
    # When the button for difficulty is hit, open the dificulty popup.
    def changeDifficulty(self):
        dif = difficultyPop(size=(self.width * .75, self.height * .25))
        dif.open()


# ScreenManagement
# Class for holding the ScreenManager object
class ScreenManagement(ScreenManager):
    error = ""
    running = True


# Build the screen manager, build a new screen, then switch to the screen.
scrn = ScreenManagement()
screens = [Board()]
scrn.switch_to(screens[0])


# GameApp
# Core class that runs the application
class GameApp(App):

    # build
    # Builds application
    def build(self):
        self.title = "Bubble Breaker"
        return scrn

# Run the application
if __name__ == '__main__':
    GameApp().run()

