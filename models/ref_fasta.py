import os

class Ref_Fasta():
    def __init__(self, fasta_path):
        self.path = fasta_path
        self.dir = os.path.dirname(self.path)
        self.filename = os.path.basename(self.path)