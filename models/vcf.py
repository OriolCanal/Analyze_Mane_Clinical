import os
class Vcf_Class():

    def __init__(self, vcf_path):
        self.path = vcf_path
        self.filename = os.path.basename(self.path)
        self.dir = os.path.dirname(self.path)
        self.annotated_filename= f"annotated_{self.filename}"
        self.annotated_path = os.path.join(self.dir, self.annotated_filename)
        self.gff_annotated_path = None
        self.gff_annotatede_filename = None
        self.variants = list()
    
    def set_annotated_vcf(self, annotated_vcf_path):
        if not os.path.exists(annotated_vcf_path):
            raise ValueError(
                f"File {annotated_vcf_path} does not exist!"
            )
        self.annotated_path = annotated_vcf_path
        self.annotated_filename = os.path.basename(annotated_vcf_path)
    
    def set_gff_annotated_vcf(self, annotated_vcf_path):
        if not os.path.exists(annotated_vcf_path):
            raise ValueError(
                f"File {annotated_vcf_path} does not exist!"
            )
        self.gff_annotated_path = annotated_vcf_path
        self.gff_annotated_filename = os.path.basename(annotated_vcf_path)