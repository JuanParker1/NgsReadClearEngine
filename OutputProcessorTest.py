import argparse
import pandas as pd
from operator import itemgetter
from itertools import groupby
from pathlib import Path
from SharedConsts import K_MER_COUNTER_MATRIX_FILE_NAME


def process_output(**kwargs):
    # parse arguments
    outputFilePath = Path(kwargs['kwargs']['outputFilePath'])
    KmerPrecision = int(kwargs['kwargs']['KmerPrecisionLimit'])
    processed_results_path = outputFilePath.parent / K_MER_COUNTER_MATRIX_FILE_NAME

    df_origin = pd.read_csv(outputFilePath,
                            sep='\t', header=None)
    #df_origin['split'].str.split()
    df_origin['split'] = df_origin[4].apply(
        lambda x: [y.split(':') for y in x.split()])  # split list and makes pairs (specie, k-mers)
    df_origin['split'] = df_origin['split'].apply(lambda x: sorted(x, key=itemgetter(0)))  # sort by specie (inside each row)
    df_origin['split'] = df_origin['split'].apply(lambda x: [(key, sum([int(y[1]) for y in group])) for key, group in
                                                             groupby(x, key=itemgetter(
                                                                 0))])  # groupby specie and count by k-mers
    df_origin['max_specie'] = df_origin['split'].apply(lambda x: max(x, key=itemgetter(1))[0])  # calculate max speice
    df_origin['max_k_mer'] = df_origin['split'].apply(lambda x: max(x, key=itemgetter(1))[1])  # calculate k-mers
    df_origin['max_k_mer_p'] = df_origin['max_k_mer'] / df_origin[3]

    df_origin["bins_max_k_mer_p"] = pd.cut(df_origin["max_k_mer_p"], [x for x in range(KmerPrecision + 1)],
                                           precision=0,
                                           labels=[x for x in range(KmerPrecision)])  # split k_mers to bins

    df_preprocess = pd.crosstab(df_origin.max_specie, df_origin.bins_max_k_mer_p)
    df_preprocess.to_csv(str(processed_results_path))


if __name__ == '__main__':

    process_output(kwargs={"outputFilePath":"/groups/pupko/alburquerque/kraken_out_1.txt","KmerPrecisionLimit":100})
    parser = argparse.ArgumentParser(description='Running RL project Main')
    parser.add_argument('--outputFilePath', default=None, help='path to output file to process')
    parser.add_argument('--KmerPrecisionLimit', default=100, help='K-mer Cutoff')  # todo write better help
    args = parser.parse_args()
    process_output(**vars(args))

