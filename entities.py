import pygame
import cv2 as cv
import utility as ut
import groups as gp

from variables import *
from pygame.locals import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, _type, name, animSpeed, scale=1, loop=True):
        super().__init__()
        tmp = cv.imread(f"{_type}/art/{name}.png")
        jdata = ut.readData(f"{_type}/json/{name}.json")

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

    def update(self, vec, win):
        self.rect.center += vec

        if self in gp.visibleEntities.sprites():
            self.counter += self.animSpeed

            if self.counter > len(self.frames) - 1:
                if self.loop:
                    self.counter = 0
                else:
                    self.kill()
                    return
            self.image = self.frames[int(self.counter)]

        if ut.isInBox(self.rect.center, self.rect.width//2, (-win.get_width()//4, -win.get_height()//4), (win.get_width() * 5//4, win.get_height() * 5//4)):
            gp.visibleEntities.add(self)
        else:
            gp.visibleEntities.remove(self)

class Tube(Entity):
    def __init__(self, _type, animSpeed, scale):
        super().__init__("powerUps", _type, animSpeed, scale)
    def copy(self):
        return Tube(self.name, self.animSpeed, self.scale)
    def action(self, p1):
        return 1
    def update(self, vec, win):
        super().update(vec, win)

        if pygame.sprite.spritecollideany(self, gp.playerGroup):
            collide = pygame.sprite.spritecollideany(self, gp.playerGroup)
            print(collide.rect.center, self.rect.center)
            if isinstance(collide, Player):
                print("YAY", collide)
                self.action(collide)
                tmp = tubeBroken.copy()
                tmp.rect.midbottom = self.rect.midbottom
                tmp.add(gp.entityGroup, gp.allEntities, gp.visibleEntities)

                self.kill()


class Entity2(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.rect = self.image.get_rect()
        self.vel = pygame.math.Vector2(0, 0)

        self.collide = None

    def update(self, vec, win):
        self.rect.center += vec

        if ut.isInBox(self.rect.center, self.rect.width//2, (-win.get_width()//4, -win.get_height()//4), (win.get_width() * 5//4, win.get_height() * 5//4)):
            gp.visibleEntities.add(self)
        else:
            gp.visibleEntities.remove(self)

class Lift(Entity2):
    def __init__(self, index, tileset):
        super().__init__()
        self.index = index
        self.tileset = tileset

        self.image = tileset[index-1].image
        self.rect = self.image.get_rect()
    def update(self, vec, win):
        super().update(vec, win)
        if pygame.sprite.spritecollideany(self, gp.playerGroup):
            self.collide = pygame.sprite.spritecollideany(self, gp.playerGroup)
            self.collide.vel.y = -5
    def copy(self):
        return Lift(self.index, self.tileset)

tubeBroken = Entity("powerUps", "tubeBroken", 0.5, loop=False)

class CollidePoint(pygame.sprite.Sprite):
    def __init__(self, size):
        super().__init__()
        self.image = pygame.Surface(size)
        self.rect = self.image.get_rect()

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

        self.add(gp.enemyGroup)

    def update_cp(self):
        self.front.rect.midleft = self.rect.midright
        self.back.rect.midright = self.rect.midleft
        self.bottom.rect.midtop = self.rect.midbottom

    def jump(self):
        if not self.isJumping:
            self.vel.y = -7
            self.isJumping = True

    def gravity(self):
        if not pygame.sprite.spritecollideany(self.bottom, gp.visibleTilesGrp):
            if self.vel.y < maxVel:
                self.vel.y += self.acc.y
        else:
            if not self.isJumping and abs(self.vel.y) > 1:
                self.vel.y *= -0.1
            else:
                self.isJumping = False

    def update(self, vec, win):
        super().update(vec, win)
        self.update_cp()
        if self in gp.visibleEntities.sprites():
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

    #def getNextTile(self):

    def update(self, vec, win, freeze=False):
        super().update(vec, win)
        if not freeze:
            self.startPoint += vec.x
            if self.frames != self.blowUp:
                if self.hp > 0 or pygame.sprite.spritecollideany(self, gp.playerGroup):
                    self.roam()
                else:
                    self.frames = self.blowUp
                    self.vel.x = 0
                    self.animSpeed = 0.45
            elif self.counter > len(self.frames) - 2:
                # Create Explosion
                tmp = Entity("misc", "explosion", 1.4, self.scale * 1.2, False)
                tmp.rect.center = self.rect.center
                tmp.add(gp.entityGroup, gp.allEntities, gp.visibleEntities)
                self.kill()
                return

        if pygame.sprite.spritecollideany(self.front, gp.visibleTilesGrp):
            self.rect.centerx -= self.front.image.get_width()
            self.vel.x *= -1
        if pygame.sprite.spritecollideany(self.back, gp.visibleTilesGrp):
            self.rect.centerx += self.back.image.get_width()
            self.vel.x *= -1

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
        self.jumpPower = 10
        self.__freeMove = True
        self.speed = 5
        self.gravityOn = True
        self.__fallctrl = False
        self.screen = None

    @property
    def freeMove(self):
        return self.__freeMove

    @property
    def fallCtrl(self):
        return self.__fallctrl

    def copy(self):
        return Player(self.name, self.scale)

    def gravity(self):
        if not pygame.sprite.spritecollideany(self.underpoint, gp.visibleTilesGrp):
            if self.vel.y < maxVel:
                self.vel.y += self.acc.y
        elif not self.jumping:
            self.rect.y -= self.vel.y
            self.vel.y = 0
        else:
            self.jumping = False


    def jump(self):
        self.vel.y = -self.jumpPower

    def move(self):
        k = pygame.key.get_pressed()

        if k[K_LEFT]:
            if not pygame.sprite.spritecollideany(self.backpoint, gp.visibleTilesGrp):
                self.vel.x = -self.speed
        if k[K_RIGHT]:
            if not pygame.sprite.spritecollideany(self.frontpoint, gp.visibleTilesGrp):
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

        start = gp.tileGroup.sprites()[0]
        end = gp.tileGroup.sprites()[-1]

        if not self.__freeMove:
            vec.x = -self.vel.x
            if start.rect.x > 0 or end.rect.x < self.screen.get_width():
                self.__freeMove = True
                vec.x = vec.y = 0
            elif not ut.isInBounds(self.rect.centerx, 10, self.screen.get_width() // 4, self.screen.get_width() * 3 // 4):
                diff = self.rect.centerx - self.screen.get_width()//2
                vec.x = -diff/4
        else:
            self.rect.centerx += self.vel.x
            if ut.isInBounds(self.rect.centerx, self.rect.width, self.screen.get_width()//2-20, self.screen.get_width()//2 + 20):
                self.__freeMove = False
                vec.x = -self.vel.x



        if not self.__fallctrl:
            if not ut.isInBounds(self.rect.centery, 0, self.screen.get_height()//6, self.screen.get_height()):
                vec.y = -self.vel.y
                for entityGroup in gp.visibleEntities.sprites():
                    entityGroup.vel.y = vec.y
                self.__fallctrl = True
        else:
            if not ut.isInBounds(self.rect.centery, 0, self.screen.get_height()//2 - 10, self.screen.get_height()//2 + 10):
                self.gravityOn = False
                gravOn = False
                self.jumping = True
                if self.rect.centery < self.screen.get_height()//2:
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
        if pygame.sprite.spritecollideany(self.top, gp.visibleTilesGrp):
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

        if pygame.sprite.spritecollideany(self.underpoint, gp.enemyGroup):
            coll = pygame.sprite.spritecollideany(self.underpoint, gp.enemyGroup)
            if hasattr(coll, "hp"):
                coll.hp -= 20
            self.vel.y = -self.jumpPower*2
        elif pygame.sprite.spritecollideany(self, gp.enemyGroup):
            coll = pygame.sprite.spritecollideany(self, gp.enemyGroup)
            if hasattr(coll, "damage"):
                self.hp -= coll.damage
                vel = self.vel if (max(self.vel.length(), coll.vel.length()) == self.vel.length()) else coll.vel
                self.vel = -vel
                coll.vel = vel

                self.rect.x += self.vel.x*2
                coll.rect.x += coll.vel.x*2
        else:
            self.move()

        if self.gravityOn:
            self.gravity()

        self.fric()
        self.update_cp()
