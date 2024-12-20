from json import load

def readData(file):
    with open(file, "rb") as f:
        r = load(f)
        f.close()
    return r


def isInBounds(x, off, min, max):
    return ((x+off) >= min) and ((x+off) <= max)

def isInBox(c, off, p1, p2):
    return isInBounds(c[0], off, p1[0], p2[0]) and isInBounds(c[1], off, p1[1], p2[1])