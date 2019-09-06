# Bubble Breaker
A bubble game designed to break bubbles, joining bubbles of like color together to increase the score exponentially.
Each bubble added will add to the total connected, total connected squared creates the total score if broken. 
The goal is to gain the highest total points possible.

## [Video Walkthrough](https://drive.google.com/file/d/1snXnTPGIfFp6Y0SYDih93aYeTqgkIYVk/view)

## Languages
* Python - PyCharm
* Kivy

## Technologies
* Kivy - Python GUI framework that allows for cross-platform support
* Random
* Garbage Collection

## Key Features
* Undo button to allow user to undo their last move
* Difficulty switcher, to add up to 6 bubbles on the screen
* New Game button to start fresh if the user desires a better roll
* Mute/Unmute to turn off sound in-game
* High Score monitoring to keep track of each difficulties best scores

## Key Notes
* When the column is empty, the columns will move together, and they will do so towards the center for asthetic purposes
* Bubble pops up on screen in the upper left of all connectred bubbles. 
* Memory for all bubble colors is allocated and objects are built on startup, to ensure smooth, fast, gameplay
* New game generation is instant
