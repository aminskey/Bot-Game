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
from text import Text
from math import sin
from time import sleep

pygame.init()

clock = pygame.time.Clock()

screen = pygame.display.set_mode(resolution, SCALED | FULLSCREEN)
pygame.display.set_caption(f"{title} - {subtitle}")

levels = ut.readData("levels/levels.json")
testLevel = Level(levels["levels"][0])

titleFont = pygame.font.Font("fonts/Flexi_IBM_VGA_True.ttf", 75)
subFont = pygame.font.Font("fonts/Flexi_IBM_VGA_True.ttf", 45)
normalFont = pygame.font.Font("fonts/Flexi_IBM_VGA_True.ttf", 35)

def enterOpp(surf=screen, font="fonts/Flexi_IBM_VGA_True.ttf", msg=None, fadeOut=True, color=BLACK):
    win = pygame.Surface(surf.get_size())
    win.fill(color)

    alphaVal = 0

    script = pygame.font.Font(font, 50)

    if msg != None:
        mesg = Text(msg, script, WHITE, pos=(surf.get_width()//2, surf.get_height()//2))

    while alphaVal < 220:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        if fadeOut:
            pygame.mixer.music.set_volume(pygame.mixer.music.get_volume()-0.01)
            if pygame.mixer.music.get_volume() < 0.03:
                break


        win.set_alpha(alphaVal)

        surf.blit(win, (0, 0))

        if msg != None:
            surf.blit(mesg.image, mesg.rect)

        pygame.display.update()
        clock.tick(30)

        alphaVal += 1

    pygame.mixer.music.set_volume(1)

def startScreen():
    textGrp = pygame.sprite.Group()

    header = Text(title, titleFont, WHITE)
    sub = Text(subtitle, subFont, WHITE)

    header.rect.midtop = screen.get_rect().midtop
    sub.rect.midtop = header.rect.midbottom
    textGrp.add(header, sub)

    snd = pygame.mixer.Sound("SFX/cursor.wav")

    bg = SimpleImage("misc/art/startscreen.png")
    bg.rescale(3 * screen.get_height()/bg.image.get_height())
    v = 0

    bg.rect.midtop = screen.get_rect().midtop

    vec = pygame.math.Vector2(0, 0)
    acc = pygame.math.Vector2(0, 0)
    options = []
    index = 0

    cursor = Text(" ", normalFont, WHITE)
    cursor.image.fill(WHITE)

    textGrp.add(cursor)

    shade = pygame.Surface(screen.get_size())
    shade.fill(BLACK)

    for i, op in enumerate(["Start", "Options", "Quit"]):
        tmp = Text(op, normalFont, WHITE)
        if i == 0:
            tmp.rect.topleft = screen.get_rect().midleft + pygame.math.Vector2(cursor.rect.width + 10, screen.get_height()//5)
        else:
            tmp.rect.topleft = options[i-1].rect.bottomleft
        options.append(tmp)
        textGrp.add(tmp)

    k = 0
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit(0)
            if event.type == KEYDOWN:
                snd.play()
                if event.key == K_DOWN:
                    index = index + 1 if index < len(options) - 1 else 0
                elif event.key == K_UP:
                    index = index - 1 if index > 0 else len(options) - 1
                elif event.key == K_RETURN:
                    if options[index].msg == "Start":
                        enterOpp(screen, msg="Loading .....")
                        pygame.mixer.music.unload()
                        main(testLevel)

                        pygame.mixer.music.load("BGM/startscreen.ogg")
                        pygame.mixer.music.play(-1)
                    elif options[index].msg == "Quit":
                        enterOpp(color=BLACK)
                        pygame.quit()
                        exit(0)
                break
            if event.type == KEYUP:
                snd.stop()
                break

        cursor.rect.midright = options[index].rect.midleft + pygame.math.Vector2(-5, 0)
        cursor.blink()

        if not ut.isInBounds(bg.rect.y, 5, -screen.get_height() * index):
            vec.y = -(screen.get_height() * index) - bg.rect.y + acc.y
            if vec.length() > 0:
                vec = vec.normalize() * 20
        else:
            vec.y = 0

        bg.rect.center += vec
        v = 50 * sin(0.025 * k) + 50
        bg.image.set_alpha(100 + v)


        screen.fill(BLACK)
        screen.blit(bg.image, bg.rect)
        textGrp.draw(screen)

        if k < 255:
            shade.set_alpha(255 - k)
            screen.blit(shade, (0, 0))

        pygame.display.update()
        clock.tick(30)
        k += 1


def main(level):
    tileset = levelGen.generateTileSet(level.tilesheet)
    levelGen.entityDict[45] = [Lift, (45, tileset)]

    spawnpoint, finishLine = levelGen.generateLevel(level.levelData, tileset)

    pygame.mixer.music.load(level.bgm)
    pygame.mixer.music.play(-1)
    enterOpp(color=WHITE, fadeOut=False)

    bg = SimpleImage(level.bg)
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
                    enterOpp(color=WHITE)
                    pygame.quit()
                    quit()
                break

        if finishLine.completed:
            for sprite in gp.allSprites.sprites():
                sprite.kill()
            enterOpp(color=WHITE)
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

def introScreen():
    l1 = SimpleImage("misc/art/gameIcon.png", (screen.get_width()/4, screen.get_height()/4))
    l1.rect.midright = screen.get_rect().center

    t1 = Text("Island", titleFont, GREEN)
    t2 = Text("Studios", titleFont, BLUE)

    t1.rect.bottomleft = l1.rect.midright
    t2.rect.topleft = t1.rect.bottomleft

    l2 = SimpleImage("misc/art/gameLogo-old.png", scale=0.5)
    l2.rect.center = screen.get_rect().center

    v = 1
    alpha = 0
    index = 0

    displays = ([l1, t1, t2], [l2])
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit(0)

        alpha += v
        if alpha > 254 and v > 0:
            v = -1
        elif alpha < 1 and v < 0:
            v = 1
            if index < len(displays) - 1:
                index += 1
            else:
                return

        screen.fill(BLACK)
        for i in displays[index]:
            i.image.set_alpha(alpha)

            screen.blit(i.image, i.rect)

        pygame.display.update()
        clock.tick(60)



if __name__ == "__main__":
    pygame.mixer.music.load("BGM/startscreen.ogg")
    pygame.mixer.music.play(-1)

    introScreen()
    sleep(1)
    startScreen()