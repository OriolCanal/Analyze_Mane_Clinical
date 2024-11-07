import os
from models.vcf import Vcf_Class
from models.log import Log
import subprocess
from typing import List, Optional


class Run():
    runs_path = "/home/ocanal/Desktop/vep_with_gff"
    def __init__(self, run_path: str):
        self.run_path = run_path
        self.run_id = os.path.basename(self.run_path)
        self.samples = list()
        self.run_path = os.path.join(self.runs_path, self.run_id)
        

    def add_sample(self, Sample: "Sample") -> None:
        """Adds a sample to the run."""

        self.samples.append(Sample)


class Sample():
    all_samples: List['Sample'] = []

    def __init__(self, sample_id, sample_dir):
        self.sample_id = sample_id
        self.Bam = None
        self.Vcf = None
        self.panel = None
        self.path = sample_dir
        self.vcf_dir = os.path.join(sample_dir, "VCF_FOLDER")
        self.bam_dir = os.path.join(sample_dir, "BAM_FOLDER")
    
    def set_bam(self, Bam):
        self.Bam = Bam
    
    def set_vcf(self, Vcf):
        self.Vcf = Vcf
    
    def set_panel(self, panel):
        self.panel = panel

    def run_haplotype_caller(self, bed_path, Ref_fasta):
        if self.Vcf:
            Log.info(f"Haplotype Caller won't be run as VCF already exists for sample {self.sample_id}")
        
        vcf_filename = f"{self.sample_id}_Mane_Clinical.vcf"
        vcf_path = os.path.join(self.vcf_dir, vcf_filename)
        if os.path.exists(vcf_path):
            Log.info(f"Haplotype Caller won't be run as VCF already exists for sample {self.sample_id}")
            self.Vcf = Vcf_Class(vcf_path)
            return(0)
        
        self.Vcf = Vcf_Class(vcf_path)
        
        bed_dir = os.path.dirname(bed_path)
        bed_filename = os.path.basename(bed_path)

        cmd = [
            f"/usr/bin/docker", "run",
            "-v", f"{self.Bam.dir}:/bam_data/",
            "-v", f"{self.vcf_dir}:/vcf_data/",
            "-v", f"{Ref_fasta.dir}:/bundle/",
            "-v", f"{bed_dir}:/panel_data/",
            "-it", "broadinstitute/gatk:4.2.2.0",
            "gatk", "HaplotypeCaller", 
            "-I", f"/bam_data/{self.Bam.filename}",
            "-O", f"/vcf_data/{self.Vcf.filename}",
            "-L", f"/panel_data/{bed_filename}",
            "-R", f"/bundle/{Ref_fasta.filename}",
            "--native-pair-hmm-threads", "4"
        ]
        cmd_str = " ".join(cmd)

        Log.info(
            f"Running Haplotype caller over sample {self.sample_id}:\n{cmd_str}"
        )
        try:
            subprocess.run(cmd, check=True)
            Log.info(f"HaplotypeCaller completed successfully for sample {self.sample_id}.")
        except subprocess.CalledProcessError as e:
            Log.error(f"HaplotypeCaller failed for sample {self.sample_id}: {e}")
        
        return(0)


    

