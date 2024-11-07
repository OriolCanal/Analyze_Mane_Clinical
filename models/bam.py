import os

class Bam():
    def __init__(self, bam_path):
        self.path = bam_path
        self.filename = os.path.basename(self.path)
        self.dir = os.path.dirname(self.path)

