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

clock = pygame.time.Clock()

screen = pygame.display.set_mode(resolution, SCALED | FULLSCREEN)
pygame.display.set_caption(title)

levels = ut.readData("levels/levels.json")
testLevel = Level(levels["levels"][0])

def main(level):
    tileset = levelGen.generateTileSet(f"levels/{level.tilesheet}")
    levelGen.entityDict[45] = [Lift, (45, tileset)]

    spawnpoint = levelGen.generateLevel(f"levels/{level.levelData}", tileset)

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

        gp.tileGroup.update(origo, screen)
        gp.entityGroup.update(origo, screen)
        p1.cntrlCamera(origo)
        p1.update()

        screen.fill(BLACK)
        gp.tile2grp.draw(screen)
        gp.visibleEntities.draw(screen)
        screen.blit(p1.image, p1.rect)
        gp.visibleTilesGrp.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main(testLevel)