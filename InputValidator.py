from Bio import SeqIO, Entrez
import gzip
import shutil
from urllib.error import HTTPError


class InputValidator:
    def __is_fasta(self, filename):
        with open(filename, "r") as handle:
            fasta = SeqIO.parse(handle, "fasta")
            try:
                return any(fasta)
            except Exception as e:
                return False

    def __is_fastq(self, filename):
        with open(filename, "r") as handle:
            fastq = SeqIO.parse(handle, "fastq")

            try:
                return any(fastq)
            except Exception as e:
                return False

    def unzip_file(self, filename):
        with gzip.open(filename, 'rb') as f_in:
            unzipped_filename = '.'.join(filename.split('.')[:-1])
            with open(unzipped_filename, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return unzipped_filename

    def validate_input_file(self, file2check):
        if file2check.endswith('.gz'): #unzip file
            file2check = self.unzip_file(file2check)
        
        if self.__is_fasta(file2check):
            return True
        elif self.__is_fastq(file2check):
            return True
        return False
        
    def valid_species(self, species: str):
        try:
            handle = Entrez.efetch(db="nucleotide", id=species, rettype="fasta", retmode="text")
        except HTTPError as e:
            print(e)
            return False
        return True
