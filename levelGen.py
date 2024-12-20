import pygame
import groups as gp
import cv2 as cv
import utility as ut

from pygame.locals import *
from variables import *
import entities as ent

class Tile(pygame.sprite.Sprite):
    def __init__(self, id, img, off=(0, 0), tilesize=(32, 32), alpha=(255, 0, 208)):
        super().__init__()

        self.id = id
        self.bgTile = False
        self.img = img
        self.off = off
        self.tilesize = tilesize
        self.alpha = alpha

        tmp = cv.imread(img)
        buff = tmp[off[0]:(tilesize[0]+off[0]), off[1]:(tilesize[1]+off[1])]

        self.image = pygame.image.frombuffer(buff.tobytes(), tilesize, "BGR")
        self.image.set_colorkey(self.alpha)
        self.rect = self.image.get_rect()
    def update(self, vec, win):
        self.rect.center += vec
        if self.id >= 1:
            if ut.isInBox(self.rect.center, self.rect.width//2, (-win.get_width()//4, -win.get_height()//4), (win.get_width() * 5//4, win.get_height() * 5//4)):
                if not self.bgTile:
                    gp.visibleTilesGrp.add(self)
                else:
                    gp.tile2grp.add(self)
            else:
                if not self.bgTile:
                    gp.visibleTilesGrp.remove(self)
                else:
                    gp.tile2grp.remove(self)


    def copy(tile):
        return Tile(tile.id, tile.img, tile.off, tile.tilesize, tile.alpha)


def generateTileSet(file):
    tset = []
    jdata = ut.readData(file)
    res = (jdata["tilewidth"], jdata["tileheight"])
    c = jdata["transparentcolor"].strip("#")
    alpha = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    img = f"levels/{jdata['image']}"

    i = j = 0
    for n in range(jdata["tilecount"]):
        tmp = Tile(n, img, (j, i), res, alpha)
        tset.append(tmp)

        i += jdata["tilewidth"]
        if i >= jdata["imagewidth"]:
            i = 0
            j += jdata["tileheight"]
    return tset


entityDict = {
    2: [ent.Bomb, (1, 1)],
    3: [ent.Enemy, ("ball", 0.25, 0.25)],
    4: [ent.Tube, ("coin", 5/FPS, 0.75)],
    5: [ent.Tube, ("healthUp", 0.125, 0.75)],
    41: [ent.Entity, ("misc", "portal", 0.75, 1.5)]
}


def generateLevel(file, tileset):

    spawnpoint = (0, 0)
    buff = ut.readData(f"{file}")
    for layer in buff["layers"]:
        for chunk in layer["chunks"]:
            startx = x = chunk["x"]
            y = chunk["y"]
            width = chunk["width"]

            for item in chunk["data"]:
                if item == 40:
                    spawnpoint = (x * 32, y * 32 + 32)
                elif item in entityDict:
                    print(item)
                    entity = entityDict[item][0](*entityDict[item][1])
                    entity.rect.bottomleft = (x*32, y*32 + 32)
                    if hasattr(entity, "startPoint"):
                        entity.startPoint = (x*32)
                    gp.entityGroup.add(entity)
                    gp.allEntities.add(entity)
                else:
                    if item > 1:
                        tmp = tileset[item-1].copy()
                        tmp.rect.topleft = (x*32, y*32)
                        tmp.image.set_alpha(layer["opacity"]*255)

                        if layer["name"] != "Main Layer":
                            tmp.bgTile = True

                        gp.tileGroup.add(tmp)

                x += 1
                if x >= (width + startx):
                    x = startx
                    y += 1
    return spawnpoint