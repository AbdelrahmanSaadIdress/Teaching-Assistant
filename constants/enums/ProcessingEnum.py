from enum import Enum

class ProcessingEnum(Enum):

    TXT = ".txt"
    PDF = ".pdf"
    IMG = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
    VID = [".mp4", ".mov", ".avi", ".mkv"]
    AUD = [".mp3", ".wav", ".ogg", ".m4a"]