import random

import pygame
import json
import cv2 as cv
import levelGen
import groups as gp
import utility as ut

from pygame.locals import *
from variables import *
from entities import Lift, Player
from levelClass import Level
from simpleImage import SimpleImage
from time import time

clock = pygame.time.Clock()

screen = pygame.display.set_mode(resolution, SCALED | FULLSCREEN)
pygame.display.set_caption(title)

levels = ut.readData("levels/levels.json")
testLevel = Level(levels["levels"][0])

def main(level):
    tileset = levelGen.generateTileSet(f"levels/{level.tilesheet}")
    levelGen.entityDict[45] = [Lift, (45, tileset)]

    spawnpoint, finishLine = levelGen.generateLevel(f"levels/{level.levelData}", tileset)

    bg = SimpleImage(f"levels/{level.bg}")
    bg.rescale(screen.get_height()/(bg.image.get_height()/2))
    bg.image.set_alpha(100)

    origo = pygame.math.Vector2(0, 0)
    p1 = Player("red")
    p1.rect.midbottom = spawnpoint
    p1.screen = screen

    gp.allEntities.add(p1)
    gp.playerGroup.add(p1)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    quit()
                break

        if finishLine.completed:
            for sprite in gp.allSprites.sprites():
                sprite.kill()
            return

        gp.tileGroup.update(origo, screen)
        gp.entityGroup.update(origo, screen)
        p1.cntrlCamera(origo)
        p1.update()

        bg.rect.center += origo * 0.25
        if bg.rect.y > 0 or bg.rect.bottomleft[1] < screen.get_height():
            bg.rect.y = 0

        screen.fill(BLACK)
        screen.blit(bg.image, bg.rect)
        gp.tile2grp.draw(screen)
        gp.visibleEntities.draw(screen)
        screen.blit(p1.image, p1.rect)
        gp.visibleTilesGrp.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main(testLevel)