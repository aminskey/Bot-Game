import pygame

from utility import isInBounds

class Text(pygame.sprite.Sprite):
    def __init__(self, msg, script, textColor, pos=(0, 0), shadow : tuple =None, pos2=(2, 3)):
        super().__init__()

        img = script.render(msg, None, textColor)
        self.msg = msg
        # If shadow is not None, then we must expect it to be the shadow color

        if isinstance(shadow, tuple) and len(shadow) == 3:
            self.image = pygame.Surface((img.get_width()*1.02, img.get_height()*1.02)).convert_alpha()
            self.image.fill((23, 16, 1))
            self.image.set_colorkey((23, 16, 1))
            shadowText = Text(msg, script, shadow)
            shadowText.rect.topleft = pos2

            self.image.blit(shadowText.image, shadowText.rect)
            self.image.blit(img, (0, 0))
        else:
            self.image = img.copy()

        self.rect = self.image.get_rect()
        self.color = textColor
        self.rect.center = pos
        self.alphaValue = 255
        self.deltaA = -20
    def blink(self):
        self.alphaValue += self.deltaA
        if not isInBounds(self.alphaValue, 0, 0, 255):
            self.deltaA *= -1
        self.image.set_alpha(self.alphaValue)