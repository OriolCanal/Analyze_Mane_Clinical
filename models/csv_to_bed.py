import pandas as pd

df = pd.read_csv("/home/ocanal/Desktop/Mane_clinical/mane_clinical_AGILENT_GLOBAL.bed")

df_bed = df[["Chromosome", "start", "end"]].copy()

df_bed.to_csv("/home/ocanal/Desktop/Mane_clinical/mane_clinical_AGILENT_GLOBAL_gatk.bed", sep="\t", header=False, index=False)