from models.yaml import Yaml_file, Runs_yaml
from models.runs import Run, Sample
from models.bam import Bam
from models.log import Log
from models.ref_fasta import Ref_Fasta
from models.params import load_config
from models.vep import Vep, Vep_vcf, Vep_variant
import os
import pandas as pd



Log.info(f"loading configuration files.")
ann_conf, ref_conf, docker_conf = load_config()
project_dir = os.path.dirname(os.path.abspath(__file__))

# all variants dir:
all_variants_dir = os.path.join(project_dir, "all_variants")
if not os.path.exists(all_variants_dir):
    os.mkdir(all_variants_dir)

rare_variants_dir = os.path.join(project_dir, "rare_variants")
if not os.path.exists(rare_variants_dir):
    os.mkdir(rare_variants_dir)

params_file = os.path.join(project_dir, "yaml_files", "params.yaml")

# print(params_file)
Params = Yaml_file(params_file)

clinical_transcripts = Params.get_param("mane_clinical")
clinical_transcripts_ids = clinical_transcripts.values()

runs_analyzed_yaml = Params.get_param("runs_analyzed_yaml")
bed_path = Params.get_param("bed_path")

Run_yaml = Runs_yaml(runs_analyzed_yaml)
runs_analyzed = Run_yaml.get_param("runs_analyzed")

Ref_fasta = Ref_Fasta(Params.get_param("ref_fasta_path"))

Vep_class = Vep(ref_conf, ann_conf, docker_conf, "hg19")

# list where the variants along with its clinical annotations will be saved
clinical_variants_anns = list()

runs_dir = Params.get_param("runs_dir")
for dir in os.listdir(runs_dir):

    dir_path = os.path.join(runs_dir, dir)
    if not os.path.isdir(dir_path):
        # print(f"{dir_path} is not a dir")
        continue
    for run_dir in os.listdir(dir_path):
        if run_dir != "AGILENT_GLOBAL":
            continue

        agilen_path = os.path.join(dir_path, run_dir)
        # print(agilen_path)
        # if run does not contain samples analyzed with global panel continue
        if not os.path.isdir(agilen_path):
            continue
        Agilen_run = Run(dir_path)
        if Agilen_run.run_id in runs_analyzed:
            continue

        Log.info(
            f"Analyzing run {Agilen_run.run_id}"
        )
        

        # in AGILENT_GLOBAL samples
        for sample_dir in os.listdir(agilen_path):
            sample_path = os.path.join(agilen_path, sample_dir)
            if not sample_dir.startswith("RB") and not os.path.isdir(sample_path):
                continue

            sample_path = os.path.join(agilen_path, sample_dir)
            if not os.path.isdir(sample_path):
                continue
            # print(sample_dir, sample_path)
            Agilen_sample = Sample(sample_dir, sample_path)
            Agilen_run.add_sample(Agilen_sample)
            bam_dir = os.path.join(sample_path, "BAM_FOLDER")
            if not os.path.exists(bam_dir):
                continue
            for file in os.listdir(bam_dir):
                if not file.endswith("rmdup.bam"):
                    continue
                bam_path = os.path.join(bam_dir, file)
                
                Bam_class = Bam(bam_path)
                Agilen_sample.set_bam(Bam_class)
                Agilen_sample.run_haplotype_caller(bed_path, Ref_fasta)
                Vep_class.run_vep(Agilen_sample.Vcf)
                # print(f"\n\n\n{Agilen_sample.Vcf.path}")
                vep_vcf = Vep_vcf(Agilen_sample.Vcf.annotated_path)
                ann_fields = vep_vcf.get_ann_fields()
                # print(ann_fields)

                for variant in vep_vcf.get_variants():
                    clinical_variant = False
                    chr, pos, ref, alt, vep_anns = variant
                    # print(chr, pos, ref, alt)
                    vep_variant = Vep_variant(chr, pos, ref, alt, vep_anns)
                    vep_variant.parse_ann(ann_fields)
                    for annotation in vep_variant.annotations:
                        if annotation["Feature"] in clinical_transcripts_ids:
                            clinical_variant = True
                            clinical_variants_anns.append([variant, annotation, Agilen_sample.sample_id])

                    if clinical_variant == False:
                        Log.critical(f"Variant {chr}:{pos}{ref}>{alt} have not found a clinical annotation.")



        # Save run's variants to CSV
        if clinical_variants_anns:
            variant_data = []
            for clinical_variant_ann in clinical_variants_anns:
                variant, clinical_ann, sample_id = clinical_variant_ann
                
                # Prepare dictionary with variant and sample information
                variant_info = {
                    "chr": variant[0],
                    "pos": variant[1],
                    "ref": variant[2],
                    "alt": variant[3],
                    "sample_id": sample_id
                }
                variant_info.update(clinical_ann)  # add all annotation fields to the row

                variant_data.append(variant_info)

            # Create DataFrame
            df_variants = pd.DataFrame(variant_data)
            run_csv_file = os.path.join(all_variants_dir, f"mane_clinical_variants_{Agilen_run.run_id}.csv")
            df_variants.to_csv(run_csv_file, index=False)


            # Convert the MAX_AF column to floats, setting errors='coerce' to handle any non-numeric values
            df_variants["MAX_AF"] = pd.to_numeric(df_variants["MAX_AF"], errors='coerce')

            # Now, filter to only include variants with MAX_AF < 0.01
            df_variants_filtered = df_variants[df_variants["MAX_AF"] < 0.01]
            rare_run_csv_file = os.path.join(rare_variants_dir, f"mane_clinical_MAX_AF<0.01_variants_{Agilen_run.run_id}.csv")
            df_variants_filtered.to_csv(rare_run_csv_file, index=False)
            Log.info(f"Excel files for run {Agilen_run.run_id} created: {run_csv_file} and {rare_run_csv_file}")
        
        Log.info(f"Run {Agilen_run.run_id} added to Run yaml")
        Run_yaml.add_run(Agilen_run.run_id)

# Update runs_analyzed.yaml after all runs have been processed
Run_yaml.update_yaml()




#         Runs_yaml.add_run(Agilen_run.run_id)

#         run_path = os.path.join(dir_path, run_dir)


# # Collecting data for DataFrame
# variant_data = []

# # Iterate over the collected clinical variant annotations
# for clinical_variant_ann in clinical_variants_anns:
#     variant, clinical_ann = clinical_variant_ann
    
#     # Extract variant details
#     chr, pos, ref, alt, vep_anns = variant

#     # Combine variant information with clinical annotation information
#     variant_info = {
#         "chr": chr,
#         "pos": pos,
#         "ref": ref,
#         "alt": alt,
#     }
#     variant_info.update(clinical_ann)  # add all annotation fields to the row

#     # Append to the data list
#     variant_data.append(variant_info)

# # Create DataFrame
# df_variants = pd.DataFrame(variant_data)

# excel_file = os.path.join(project_dir, "mane_clincal_variants.csv")
# df_variants.to_csv("")

# Runs_yaml.update_yaml()