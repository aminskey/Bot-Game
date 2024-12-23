import pygame

class SimpleImage(pygame.sprite.Sprite):
    def __init__(self, imageURL, size=-1, scale=1):
        super().__init__()
        self.base_image = pygame.transform.scale_by(pygame.image.load(imageURL), scale)

        # size for resizing image
        if isinstance(size, tuple):
            self.base_image = pygame.transform.scale(self.base_image, size)
        self.rect = self.base_image.get_rect()

        self.image = self.base_image.copy()

    def rescale(self, v):
        self.base_image = pygame.transform.scale_by(self.base_image, v)
        self.rect = self.base_image.get_rect()
        self.image = self.base_image.copy()