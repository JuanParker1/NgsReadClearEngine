from Bio import SeqIO


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

    def validate_input_file(self, file2check):
        if self.__is_fasta(file2check):
            return True
        elif self.__is_fastq(file2check):
            return True
        return False