class Variant():
    def __init__(self, sample, chr, pos, ref, alt):
        self.sample = sample
        self.chr = chr
        self.pos = pos
        self.ref = ref
        self.alt = alt
        annotations = list()