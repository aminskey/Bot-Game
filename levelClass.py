
class Level:
    def __init__(self, data):
        self.name = data["name"]
        self.levelData = data["levelData"]
        self.tilesheet = data["tilesheet"]