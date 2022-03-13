import sys
sys.path.append("/groups/pupko/alburquerque/NgsReadClearEngine")
from Bio import Entrez
import argparse
import os
from urllib.error import HTTPError

from KrakenConsts import OUTPUT_MERGED_FASTA_FILE_NAME

EMAIL = 'edodotan@mail.tau.ac.il'
NUMBER_OF_TRIES_PER_GENOME = 3


def get_file_name(acession_number: str):
    return f'{acession_number}.fasta'


def download_genome(output_path: str, acession_number: str):
    try:
        handle = Entrez.efetch(db="nucleotide", id=acession_number, rettype="fasta", retmode="text")
        output_file_name = get_file_name(acession_number)
        out_handle = open(os.path.join(output_path, output_file_name), "w")
        out_handle.write(handle.read())
    except HTTPError as e:
        print(e)
        return False
    return True


def valid_fasta_file(output_path: str, acession_number: str):
    output_file_name = get_file_name(acession_number)
    output_file_path = os.path.join(output_path, output_file_name)
    if os.path.isfile(output_file_path):
        if os.path.getsize(output_file_path) > 10:
            return True
    return False


if __name__ == "__main__":
    Entrez.email = EMAIL
    
    CLI=argparse.ArgumentParser()
    CLI.add_argument(
      "--list_accession_number",  # name on the CLI - drop the `--` for positional/required parameters
      nargs="*",  # 0 or more values expected => creates a list
      type=str,
      #default=[1, 2, 3],  # default if nothing is provided
    )
    CLI.add_argument(
      "--download_path",  # name on the CLI - drop the `--` for positional/required parameters
      nargs="+",  # 0 or more values expected => creates a list
      type=str,
    )
    args = CLI.parse_args()
    
    print("list_accession_number: ", args.list_accession_number)
    print("download_path: ", args.download_path)
    
    download_path = args.download_path[0]
    succ_genome_download_num = 0
    for acession_number in args.list_accession_number:
        failed_nums = 0
        for _ in range(NUMBER_OF_TRIES_PER_GENOME):
            if download_genome(download_path, acession_number):
                if valid_fasta_file(download_path, acession_number):
                    break
            failed_nums += 1
        if failed_nums == NUMBER_OF_TRIES_PER_GENOME:
            print(f'failed to download acession_number = {acession_number}')
        else:
            succ_genome_download_num += 1
    
    if succ_genome_download_num == len(args.list_accession_number):
        print(f'downloaded successefully all the genomes')
        output_merged_fasta_path = os.path.join(download_path, OUTPUT_MERGED_FASTA_FILE_NAME)
        with open(output_merged_fasta_path, 'w') as out_file:
            for acession_number in args.list_accession_number:
                genome_fasta_path = os.path.join(download_path, get_file_name(acession_number))
                with open(genome_fasta_path, 'r') as in_file:
                    for line in in_file:
                        out_file.write(line)
    else:
        print(f'failed downloading all of the files')