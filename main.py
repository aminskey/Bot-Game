import random

import pygame
import json
import cv2 as cv

from pygame.locals import *


FPS = 45
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

maxVel = 10
gravOn = True

vzero = pygame.math.Vector2(0, 0)

title = "Untitled Bot Game"
resolution = (900, 600)
spawnpoint = (0, 0)

clock = pygame.time.Clock()

screen = pygame.display.set_mode(resolution, SCALED | FULLSCREEN)
pygame.display.set_caption(title)

tileGroup = pygame.sprite.Group()
tile2grp = pygame.sprite.Group()
entityGroup = pygame.sprite.Group()
enemyGroup = pygame.sprite.Group()
playerGroup = pygame.sprite.Group()
allEntities = pygame.sprite.Group()
visibleEntities = pygame.sprite.Group()
visibleTilesGrp = pygame.sprite.Group()

def readData(file):
    with open(file, "rb") as f:
        r = json.load(f)
        f.close()
    return r

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
    def update(self, vec=pygame.math.Vector2(0, 0), win=screen):
        self.rect.center += vec
        if self.id >= 1:
            if isInBox(self.rect.center, self.rect.width//2, (-win.get_width()//4, -win.get_height()//4), (win.get_width() * 5//4, win.get_height() * 5//4)):
                if not self.bgTile:
                    visibleTilesGrp.add(self)
                else:
                    tile2grp.add(self)
            else:
                if not self.bgTile:
                    visibleTilesGrp.remove(self)
                else:
                    tile2grp.remove(self)

class Entity(pygame.sprite.Sprite):
    def __init__(self, _type, name, animSpeed, scale=1, loop=True):
        super().__init__()
        tmp = cv.imread(f"{_type}/art/{name}.png")
        jdata = readData(f"{_type}/json/{name}.json")

        self.frames = []
        self.type = _type
        self.animSpeed = animSpeed
        self.scale = scale
        self.counter = 0
        self.name = name
        self.loop = loop
        self.args = []
        self.vel = pygame.math.Vector2(0, 0)

        for i in jdata["frames"].items():
            item = i[1]
            w, h = item["frame"]["w"], item["frame"]["h"]
            x, y = item["frame"]["x"], item["frame"]["y"]
            buff = tmp[y:(h+y), x:(w+x)]
            img = pygame.transform.scale_by(pygame.image.frombuffer(buff.tobytes(), (w, h), "BGR"), scale)
            img.set_colorkey((255, 0, 208))
            self.frames.append(img)

        self.image = self.frames[0]
        self.rect = self.image.get_rect()

    def copy(self):
        return Entity(self.type, self.name, self.animSpeed, self.scale, self.loop)

    def update(self, vec, win=screen):
        self.rect.center += vec

        if self in visibleEntities.sprites():
            self.counter += self.animSpeed

            if self.counter > len(self.frames) - 1:
                if self.loop:
                    self.counter = 0
                else:
                    self.kill()
                    return
            self.image = self.frames[int(self.counter)]

        if isInBox(self.rect.center, self.rect.width//2, (-win.get_width()//4, -win.get_height()//4), (win.get_width() * 5//4, win.get_height() * 5//4)):
            visibleEntities.add(self)
        else:
            visibleEntities.remove(self)

class Tube(Entity):
    def __init__(self, _type, animSpeed, scale):
        super().__init__("powerUps", _type, animSpeed, scale)
    def copy(self):
        return Tube(self.name, self.animSpeed, self.scale)
    def action(self, p1):
        return 1
    def update(self, vec, win=screen):
        super().update(vec, win)

        if pygame.sprite.spritecollideany(self, playerGroup):
            collide = pygame.sprite.spritecollideany(self, playerGroup)
            print(collide.rect.center, self.rect.center)
            if isinstance(collide, Player):
                print("YAY", collide)
                self.action(collide)
                tmp = tubeBroken.copy()
                tmp.rect.midbottom = self.rect.midbottom
                tmp.add(entityGroup, allEntities, visibleEntities)

                self.kill()


class Entity2(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.rect = self.image.get_rect()
        self.vel = pygame.math.Vector2(0, 0)

        self.collide = None

    def update(self, vec, win=screen):
        self.rect.center += vec

        if isInBox(self.rect.center, self.rect.width//2, (-win.get_width()//4, -win.get_height()//4), (win.get_width() * 5//4, win.get_height() * 5//4)):
            visibleEntities.add(self)
        else:
            visibleEntities.remove(self)

class Lift(Entity2):
    def __init__(self, index, tileset):
        super().__init__()
        self.index = index
        self.tileset = tileset

        self.image = tileset[index-1].image
        self.rect = self.image.get_rect()
    def update(self, vec, win=screen):
        super().update(vec, win)
        if pygame.sprite.spritecollideany(self, playerGroup):
            self.collide = pygame.sprite.spritecollideany(self, playerGroup)
            self.collide.vel.y = -5
    def copy(self):
        return Lift(self.index, self.tileset)



class CollidePoint(pygame.sprite.Sprite):
    def __init__(self, size):
        super().__init__()
        self.image = pygame.Surface(size)
        self.rect = self.image.get_rect()

class Player(Entity):
    def __init__(self, name, scale=1):
        super().__init__("bots", name, 0.25, scale)
        self.lives = 3
        self.hp = 50

        self.acc = pygame.math.Vector2(0, 1)
        self.vel = pygame.math.Vector2(0, 0)

        self.frontpoint = CollidePoint((5, self.image.get_height() // 2 - 10))
        self.backpoint = CollidePoint((5, self.image.get_height() // 2 - 10))
        self.underpoint = CollidePoint((self.image.get_width()//2, 5))
        self.top = CollidePoint((self.image.get_width()//2, 5))

        self.jumping = False
        self.jumpPower = 7
        self.__freeMove = True
        self.speed = 5
        self.gravityOn = True
        self.__fallctrl = False

    @property
    def freeMove(self):
        return self.__freeMove

    @property
    def fallCtrl(self):
        return self.__fallctrl

    def copy(self):
        return Player(self.name, self.scale)

    def gravity(self):
        if not pygame.sprite.spritecollideany(self.underpoint, visibleTilesGrp):
            if self.vel.y < maxVel:
                self.vel.y += self.acc.y
        elif not self.jumping:
            self.vel.y = 0
        else:
            self.jumping = False


    def jump(self):
        self.vel.y = -self.jumpPower

    def move(self):
        k = pygame.key.get_pressed()

        if k[K_LEFT]:
            if not pygame.sprite.spritecollideany(self.backpoint, visibleTilesGrp):
                self.vel.x = -self.speed
        if k[K_RIGHT]:
            if not pygame.sprite.spritecollideany(self.frontpoint, visibleTilesGrp):
                self.vel.x = self.speed
        if k[K_SPACE]:
            if not self.jumping:
                self.jumping = True
                self.jump()

    def fric(self, fval=0.8):
        self.vel.x *= fval

    def resetVel(self):
        self.vel = pygame.math.Vector2(0, 0)

    def update_cp(self):
        self.frontpoint.rect.topleft = self.rect.midright
        self.backpoint.rect.topright = self.rect.midleft
        self.underpoint.rect.midtop = self.rect.midbottom
        self.top.rect.midbottom = self.rect.midtop

    def cntrlCamera(self, vec):

        global gravOn

        start = tileGroup.sprites()[0]
        end = tileGroup.sprites()[-1]

        if not self.__freeMove:
            vec.x = -self.vel.x
            if start.rect.x > 0 or end.rect.x < screen.get_width():
                self.__freeMove = True
                vec.x = vec.y = 0
        else:
            self.rect.centerx += self.vel.x
            if isInBounds(self.rect.centerx, self.rect.width, screen.get_width()//2-20, screen.get_width()//2 + 20):
                self.__freeMove = False
                vec.x = -self.vel.x


        if not self.__fallctrl:
            if not isInBounds(self.rect.centery, 0, screen.get_height()//6, screen.get_height()):
                vec.y = -self.vel.y
                for entityGroup in visibleEntities.sprites():
                    entityGroup.vel.y = vec.y
                self.__fallctrl = True
        else:
            if not isInBounds(self.rect.centery, 0, screen.get_height()//2 - 10, screen.get_height()//2 + 10):
                self.gravityOn = False
                gravOn = False
                self.jumping = True
                if self.rect.centery < screen.get_height()//2:
                    vec.y = self.speed
                    self.rect.centery += self.speed
                else:
                    vec.y = -self.speed
                    self.rect.centery -= self.speed
            else:
                vec.y = 0
                self.gravityOn = True
                gravOn = True
                self.jumping = False
                self.__fallctrl = False

        if not self.__fallctrl:
            self.rect.centery += self.vel.y

    def update(self):
        if pygame.sprite.spritecollideany(self.top, visibleTilesGrp):
            self.jumping = True
            self.vel.y = 1

        if abs(self.vel.x) < 1:
            self.counter += self.animSpeed
        else:
            self.counter = -1

        if self.counter > len(self.frames) - 2:
            self.counter = 0
        tmp = self.frames[int(self.counter)]

        if self.vel.x < 0:
            self.image = pygame.transform.flip(tmp, True, False)
        else:
            self.image = tmp

        if pygame.sprite.spritecollideany(self.underpoint, enemyGroup):
            coll = pygame.sprite.spritecollideany(self.underpoint, enemyGroup)
            if hasattr(coll, "hp"):
                coll.hp -= 20
            self.vel.y = -self.jumpPower*2
        if pygame.sprite.spritecollideany(self, enemyGroup):
            coll = pygame.sprite.spritecollideany(self, enemyGroup)
            if hasattr(coll, "damage"):
                self.hp -= coll.damage
        else:
            self.move()

        if self.gravityOn:
            self.gravity()

        self.fric()
        self.update_cp()
class Enemy(Entity):
    def __init__(self, _type, animSpeed, scale):
        super().__init__("hostile", _type, animSpeed, scale)
        self.hp = 12
        self.acc = pygame.math.Vector2(0, 1)

        self.front = CollidePoint((4, self.image.get_height()//3))
        self.back = CollidePoint((4, self.image.get_height()//3))
        self.bottom = CollidePoint((self.image.get_width()//3, 4))
        self.isJumping = False
        self.doJump = False
        self.damage = 5
        self.knockback = 5

        self.add(enemyGroup)

    def update_cp(self):
        self.front.rect.midleft = self.rect.midright
        self.back.rect.midright = self.rect.midleft
        self.bottom.rect.midtop = self.rect.midbottom

    def jump(self):
        if not self.isJumping:
            self.vel.y = -7
            self.isJumping = True

    def gravity(self):
        if not pygame.sprite.spritecollideany(self.bottom, visibleTilesGrp):
            if self.vel.y < maxVel:
                self.vel.y += self.acc.y
        else:
            if not self.isJumping and abs(self.vel.y) > 1:
                self.vel.y *= -0.27
            else:
                self.isJumping = False

    def update(self, vec, win=screen):
        super().update(vec, win)
        self.update_cp()
        if self in visibleEntities.sprites():
            if self.doJump:
                self.jump()

            if self.vel.x < 0:
                tmp = self.frames[int(self.counter)]
                self.image = pygame.transform.flip(tmp, True, False)

            self.rect.center += self.vel

            if gravOn:
                self.gravity()
            else:
                self.vel.y = 0

class Bomb(Enemy):
    def __init__(self, animSpeed, scale):
        super().__init__("bomb", animSpeed, scale)

        self.walkAnim = self.frames[:13].copy()
        self.blowUp = self.frames[13:].copy()

        self.frames = self.walkAnim
        self.startPoint = 0
        self.range = 256
        self.vel.x = 1

    def roam(self):
        if self.range > 0:
            if abs(self.startPoint - self.rect.centerx) > self.range:
                self.vel.x *= -1

    def update(self, vec, freeze=False, win=screen):
        super().update(vec, win)
        if not freeze:
            self.startPoint += vec.x
            if self.frames != self.blowUp:
                if self.hp > 0 or pygame.sprite.spritecollideany(self, playerGroup):
                    self.roam()
                else:
                    self.frames = self.blowUp
                    self.vel.x = 0
                    self.animSpeed = 0.45
            elif self.counter > len(self.frames) - 2:
                # Create Explosion
                tmp = Entity("misc", "explosion", 1.4, self.scale * 1.2, False)
                tmp.rect.center = self.rect.center
                tmp.add(entityGroup, allEntities, visibleEntities)
                self.kill()
                return


        if pygame.sprite.spritecollideany(self.front, visibleTilesGrp):
            self.rect.centerx -= self.front.image.get_width()
            self.vel.x *= -1
        if pygame.sprite.spritecollideany(self.back, visibleTilesGrp):
            self.rect.centerx += self.back.image.get_width()
            self.vel.x *= -1


def copyTile(tile):
    return Tile(tile.id, tile.img, tile.off, tile.tilesize, tile.alpha)

def isInBounds(x, off, min, max):
    return ((x+off) >= min) and ((x+off) <= max)

def isInBox(c, off, p1, p2):
    return isInBounds(c[0], off, p1[0], p2[0]) and isInBounds(c[1], off, p1[1], p2[1])

def generateTileSet(file):
    tset = []
    jdata = readData(file)
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


tileset = generateTileSet("levels/tilesheet.json")
tubeBroken = Entity("powerUps", "tubeBroken", 0.5, loop=False)

entityDict = {
    2: [Bomb, (1, 1)],
    3: [Enemy, ("ball", 0.25, 0.25)],
    4: [Tube, ("coin", 5/FPS, 0.75)],
    5: [Tube, ("healthUp", 0.125, 0.75)],
    41: [Entity, ("misc", "portal", 0.75, 1.5)],
    45: [Lift, (45, tileset)]
}


def generateLevel(file, tileset):

    global spawnpoint

    buff = readData(f"{file}")
    for layer in buff["layers"]:
        for chunk in layer["chunks"]:
            startx = x = chunk["x"]
            y = chunk["y"]
            width = chunk["width"]

            for item in chunk["data"]:
                if item == 40:
                    spawnpoint = (x * 32, y * 32 + 32)
                elif item in entityDict:
                    entity = entityDict[item][0](*entityDict[item][1])
                    print(item)
                    entity.rect.midbottom = (x*32, y*32 + 32)
                    if hasattr(entity, "startPoint"):
                        entity.startPoint = (x*32)
                    entityGroup.add(entity)
                    allEntities.add(entity)
                else:
                    if item > 1:
                        tmp = copyTile(tileset[item-1])
                        tmp.rect.topleft = (x*32, y*32)
                        tmp.image.set_alpha(layer["opacity"]*255)

                        if layer["name"] != "Main Layer":
                            tmp.bgTile = True

                        tileGroup.add(tmp)

                x += 1
                if x >= (width + startx):
                    x = startx
                    y += 1



def main():
    generateLevel("levels/testLevel.json", tileset)

    origo = pygame.math.Vector2(0, 0)
    p1 = Player("red")
    p1.rect.midbottom = spawnpoint
    allEntities.add(p1)
    playerGroup.add(p1)

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




        tileGroup.update(origo)
        entityGroup.update(origo)
        p1.cntrlCamera(origo)
        p1.update()

        screen.fill(BLACK)
        tile2grp.draw(screen)
        visibleEntities.draw(screen)
        screen.blit(p1.image, p1.rect)
        visibleTilesGrp.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()