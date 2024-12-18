from models.yaml import Yaml_file, Runs_yaml
from models.runs import Run, Sample
from models.bam import Bam
from models.log import Log
from models.ref_fasta import Ref_Fasta
from models.params import load_config
from models.vep import Vep, Vep_vcf, Vep_variant
#from models.samba_133 import upload_to_M
import os
import pandas as pd
from models.send_email import send_mail



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

genes_found = set()
all_clinical_variants = list()
all_gff_variants = list()

clinical_transcripts = Params.get_param("mane_clinical")
clinical_transcripts_ids = clinical_transcripts.values()
# print(clinical_transcripts_ids)

gff_transcripts = Params.get_param("gff_transcripts")
gff_transcripts_ids = gff_transcripts.values()
# print(gff_transcripts_ids)

runs_analyzed_yaml = Params.get_param("runs_analyzed_yaml")
bed_path = Params.get_param("bed_path")
bed_gff_path = Params.get_param("bed_gff")

Run_yaml = Runs_yaml(runs_analyzed_yaml)
runs_analyzed = Run_yaml.get_param("runs_analyzed")

Ref_fasta = Ref_Fasta(Params.get_param("ref_fasta_path"))

Vep_class = Vep(ref_conf, ann_conf, docker_conf, "hg19")

# list where the variants along with its clinical annotations will be saved
all_rare_variants = pd.DataFrame()


runs_dir = Params.get_param("runs_dir")
for dir in os.listdir(runs_dir):

    dir_path = os.path.join(runs_dir, dir)
    if not os.path.isdir(dir_path):
        # print(f"{dir_path} is not a dir")
        continue
    for run_dir in os.listdir(dir_path):
        if run_dir != "AGILENT_GLOBAL":
            continue

        run_excels = list()
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
        gff_variants_anns = list()
        clinical_variants_anns = list()
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
                # haplotype caller using mane bed
                Agilen_sample.run_haplotype_caller(bed_path, Ref_fasta, mane=True)
                                
                # Haplotype caller using gff bed                
                Agilen_sample.run_haplotype_caller(bed_gff_path, Ref_fasta, mane=False)

                Vep_class.run_vep(Agilen_sample.Vcf)
                Vep_class.run_vep(Agilen_sample.gff_vcf, structural_variants=False, custom_gff=True)
                # print(f"\n\n\n{Agilen_sample.Vcf.path}")
                gff_vep_vcf = Vep_vcf(Agilen_sample.gff_vcf.gff_annotated_path)
                vep_vcf = Vep_vcf(Agilen_sample.Vcf.annotated_path)

                gff_ann_fields = gff_vep_vcf.get_ann_fields()
                ann_fields = vep_vcf.get_ann_fields()
                # print(ann_fields)

                # mane
                for variant in vep_vcf.get_variants():
                    clinical_variant = False
                    chr, pos, ref, alt, vep_anns = variant
                    # print(chr, pos, ref, alt)
                    vep_variant = Vep_variant(chr, pos, ref, alt, vep_anns)
                    vep_variant.parse_ann(ann_fields)
                    for annotation in vep_variant.annotations:
                        
                        # if Vep_class.gff_name:
                        #     # just parse annotations done over the custom gff
                        #     if annotation["SOURCE"] != Vep_class.gff_name:
                        #         continue
                        # print(annotation)
                        transcript_id = annotation["Feature"]
                        
                        if "." in transcript_id:
                            transcript_id = transcript_id.split(".")[0]
                            # print(transcript_id)

                        if transcript_id in clinical_transcripts_ids:
                            clinical_variant = True
                            genes_found.add(annotation["Feature"])
                            clinical_variants_anns.append([variant, annotation, Agilen_sample.sample_id, Agilen_run.run_id])

                    if clinical_variant == False:
                        Log.critical(f"Variant {chr}:{pos}{ref}>{alt} have not found a clinical annotation.")
                
                # gff
                for variant in gff_vep_vcf.get_variants():
                    gff_variant = False
                    chr, pos, ref, alt, vep_anns = variant
                    # print(chr, pos, ref, alt)
                    vep_variant = Vep_variant(chr, pos, ref, alt, vep_anns)
                    vep_variant.parse_ann(gff_ann_fields)
                    for annotation in vep_variant.annotations:
                        
                        if Vep_class.gff_name:
                            # just parse annotations done over the custom gff
                            if annotation["SOURCE"] != Vep_class.gff_name:
                                continue
                        transcript_id = annotation["Feature"]
                        
                        if "." in transcript_id:
                            transcript_id = transcript_id.split(".")[0]

                        if transcript_id in gff_transcripts_ids:
                            gff_variant = True
                            genes_found.add(annotation["Feature"])
                            gff_variants_anns.append([variant, annotation, Agilen_sample.sample_id, Agilen_run.run_id])

                    if gff_variant == False:
                        Log.critical(f"Variant {chr}:{pos}{ref}>{alt} have not found a gff annotation.")

         # Save run's variants to CSV gff
        if gff_variants_anns:
            variant_data = []
            for gff_variant_ann in gff_variants_anns:
                variant, gff_ann, sample_id, run_id = gff_variant_ann
                
                # Prepare dictionary with variant and sample information
                variant_info = {
                    "chr": variant[0],
                    "pos": variant[1],
                    "ref": variant[2],
                    "alt": variant[3],
                    "sample_id": sample_id,
                    "run_id": run_id
                }
                variant_info.update(gff_ann)  # add all annotation fields to the row
                all_gff_variants.append(variant_info)
                variant_data.append(variant_info)

            # Create DataFrame
            df_variants = pd.DataFrame(variant_data)
            columns_to_format = ["gnomAD_exomes_faf95_afr", "gnomAD_exomes_faf95_amr", "gnomAD_exomes_faf95_eas", "gnomAD_exomes_faf95_nfe", "gnomAD_exomes_faf95_sas"]
            all_columns = df_variants.columns
            for column in all_columns:
                print(column)
            for col in columns_to_format:
                if col in df_variants.columns:
                    df_variants[col] = pd.to_numeric(df_variants[col], errors='coerce')  # Convert to floats


            # Create the new column with the minimum value across the specified columns
            df_variants["Grpmax_Filtering_AF_95%_confidence"] = df_variants[columns_to_format].max(axis=1)

            gff_run_csv_file = os.path.join(all_variants_dir, f"gff_variants_{Agilen_run.run_id}.xlsx")


            # Convert the MAX_AF column to floats, setting errors='coerce' to handle any non-numeric values
            #df_variants["MAX_AF"] = pd.to_numeric(df_variants["MAX_AF"], errors='coerce')
            
            # filter columns just to take the ones that anna and monica asked for
            columns_to_mantain = ["sample_id", "run_id", "Consequence", "SYMBOL", "HGVSc", "HGVSp", "Existing_variation", "RefSeq", "HGVSg", "REVEL_score", "SpliceAI_pred_DS_AG", "SpliceAI_pred_DS_AL", "SpliceAI_pred_DS_DG", "SpliceAI_pred_DS_DL", "ClinVar_CLNSIGCONF", "Grpmax_Filtering_AF_95%_confidence"]
            
            missing_columns = [col for col in columns_to_mantain if col not in df_variants.columns]
            if missing_columns:
                raise ValueError(f"Columns not found in the excel: {missing_columns}")

            # Now, filter to only include variants with MAX_AF < 0.001
            df_variants = df_variants[columns_to_mantain]
            df_variants_filtered = df_variants[df_variants["Grpmax_Filtering_AF_95%_confidence"] < 0.001]
            #df_variants[col] = df_variants[col].apply(lambda x: f"{x:.12f}" if pd.notnull(x) else "")
            df_variants.to_excel(gff_run_csv_file, index=False, engine='openpyxl')
            run_excels.append(gff_run_csv_file)
            gff_rare_run_csv_file = os.path.join(rare_variants_dir, f"gff_Grpmax_Filtering_AF_95%<0.001_variants_{Agilen_run.run_id}.xlsx")
            df_variants_filtered.to_excel(gff_rare_run_csv_file, index=False, engine='openpyxl')
            Log.info(f"Excel files for run {Agilen_run.run_id} created: {gff_run_csv_file} and {gff_rare_run_csv_file}")
            all_rare_variants = pd.concat([all_rare_variants, df_variants_filtered], ignore_index=True)
            run_excels.append(gff_rare_run_csv_file)

            #upload_to_M(rare_run_csv_file)


        # Save run's variants to CSV clinical
        if clinical_variants_anns:
            variant_data = []
            for clinical_variant_ann in clinical_variants_anns:
                variant, clinical_ann, sample_id, run_id = clinical_variant_ann
                
                # Prepare dictionary with variant and sample information
                variant_info = {
                    "chr": variant[0],
                    "pos": variant[1],
                    "ref": variant[2],
                    "alt": variant[3],
                    "sample_id": sample_id,
                    "run_id": run_id
                }
                variant_info.update(clinical_ann)  # add all annotation fields to the row
                all_clinical_variants.append(variant_info)
                variant_data.append(variant_info)

            # Create DataFrame
            df_variants = pd.DataFrame(variant_data)
            columns_to_format = ["gnomAD_exomes_faf95_afr", "gnomAD_exomes_faf95_amr", "gnomAD_exomes_faf95_eas", "gnomAD_exomes_faf95_nfe", "gnomAD_exomes_faf95_sas"]
            all_columns = df_variants.columns
            for column in all_columns:
                print(column)
            for col in columns_to_format:
                if col in df_variants.columns:
                    df_variants[col] = pd.to_numeric(df_variants[col], errors='coerce')  # Convert to floats


            # Create the new column with the minimum value across the specified columns
            df_variants["Grpmax_Filtering_AF_95%_confidence"] = df_variants[columns_to_format].max(axis=1)

            run_csv_file = os.path.join(all_variants_dir, f"mane_clinical_variants_{Agilen_run.run_id}.xlsx")


            # Convert the MAX_AF column to floats, setting errors='coerce' to handle any non-numeric values
            #df_variants["MAX_AF"] = pd.to_numeric(df_variants["MAX_AF"], errors='coerce')
            
            # filter columns just to take the ones that anna and monica asked for
            columns_to_mantain = ["sample_id", "run_id", "Consequence", "SYMBOL", "HGVSc", "HGVSp", "Existing_variation", "RefSeq", "HGVSg", "REVEL_score", "SpliceAI_pred_DS_AG", "SpliceAI_pred_DS_AL", "SpliceAI_pred_DS_DG", "SpliceAI_pred_DS_DL", "ClinVar_CLNSIGCONF", "Grpmax_Filtering_AF_95%_confidence"]
            
            missing_columns = [col for col in columns_to_mantain if col not in df_variants.columns]
            if missing_columns:
                raise ValueError(f"Columns not found in the excel: {missing_columns}")

            # Now, filter to only include variants with MAX_AF < 0.001
            df_variants = df_variants[columns_to_mantain]
            df_variants_filtered = df_variants[df_variants["Grpmax_Filtering_AF_95%_confidence"] < 0.001]
            #df_variants[col] = df_variants[col].apply(lambda x: f"{x:.12f}" if pd.notnull(x) else "")
            df_variants.to_excel(run_csv_file, index=False, engine='openpyxl')
            run_excels.append(run_csv_file)
            rare_run_csv_file = os.path.join(rare_variants_dir, f"mane_clinical_Grpmax_Filtering_AF_95%<0.001_variants_{Agilen_run.run_id}.xlsx")
            df_variants_filtered.to_excel(rare_run_csv_file, index=False, engine='openpyxl')
            run_excels.append(rare_run_csv_file)
            Log.info(f"Excel files for run {Agilen_run.run_id} created: {run_csv_file} and {rare_run_csv_file}")
            all_rare_variants = pd.concat([all_rare_variants, df_variants_filtered], ignore_index=True)
            #upload_to_M(rare_run_csv_file)

        send_mail(Agilen_run.run_id, run_excels)        
        Log.info(f"Run {Agilen_run.run_id} added to Run yaml")
        Run_yaml.add_run(Agilen_run.run_id)

# Save all variants to a single CSV file
#all_variants_file = os.path.join(all_variants_dir, "all_clinical_variants.xlsx")
#df_all_variants = pd.DataFrame(all_clinical_variants)
#df_all_variants.to_excel(all_variants_file, index=False, engine='openpyxl')
#all_rare_variants_file = os.path.join(rare_variants_dir, "all_rare_variants.csv")
#all_rare_variants_excel = os.path.join(rare_variants_dir, "all_rare_variants.xlsx")
#all_rare_variants = all_rare_variants.drop(columns=["gnomAD_rf_tp_probability", "gnomAD_AC_afr", "gnomAD_AN_afr", "gnomAD_AF_afr", "gnomAD_AC_amr", "gnomAD_AN_amr", "gnomAD_AF_amr", "gnomAD_AC_eas", "gnomAD_AN_eas", "gnomAD_AF_eas", "gnomAD_AC_nfe", "gnomAD_AN_nfe", "gnomAD_AF_nfe", "gnomAD_AC_fin", "gnomAD_AN_fin", "gnomAD_AF_fin", "gnomAD_AC_asj", "gnomAD_AN_asj", "gnomAD_AF_asj", "gnomAD_AC_oth", "gnomAD_AN_oth", "gnomAD_AF_oth", "gnomAD_exomes_rf_tp_probability", "gnomAD_exomes_AC_afr", "gnomAD_exomes_AN_afr", "gnomAD_exomes_AF_afr", "gnomAD_exomes_AC_amr", "gnomAD_exomes_AN_amr", "gnomAD_exomes_AF_amr", "gnomAD_exomes_AC_eas", "gnomAD_exomes_AN_eas", "gnomAD_exomes_AF_eas", "gnomAD_exomes_AC_nfe", "gnomAD_exomes_AN_nfe", "gnomAD_exomes_AF_nfe", "gnomAD_exomes_AC_fin", "gnomAD_exomes_AN_fin", "gnomAD_exomes_AF_fin", "gnomAD_exomes_AC_asj", "gnomAD_exomes_AN_asj", "gnomAD_exomes_AF_asj", "gnomAD_exomes_AC_oth", "gnomAD_exomes_AN_oth", "gnomAD_exomes_AF_oth"])
#all_rare_variants.to_csv(all_rare_variants_file, index=False)
#all_rare_variants.to_excel(all_rare_variants_excel, index=False, engine='openpyxl')

#Log.info(f"All variants file created: {all_variants_file}")


# Update runs_analyzed.yaml after all runs have been processed
Run_yaml.update_yaml()


print(genes_found)

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
