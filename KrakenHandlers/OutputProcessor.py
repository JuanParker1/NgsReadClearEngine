import argparse
import pandas as pd
from operator import itemgetter
from itertools import groupby
from pathlib import Path
from SharedConsts import K_MER_COUNTER_MATRIX_FILE_NAME, RESULTS_FOR_OUTPUT_FILE_NAME, DF_LOADER_CHUCK_SIZE, \
    RESULTS_COLUMNS_TO_KEEP

# todo: clean this file up
# todo : split classified and un classified before analyzing


def process_output(**kwargs):
    # parse arguments
    outputFilePath = Path(kwargs['outputFilePath'])
    processed_for_UI_results_path = outputFilePath.parent / K_MER_COUNTER_MATRIX_FILE_NAME
    processed_for_PostProcess_results_path = outputFilePath.parent / RESULTS_FOR_OUTPUT_FILE_NAME
    first = True
    for chunk in pd.read_csv(outputFilePath, sep='\t', header=None, chunksize=DF_LOADER_CHUCK_SIZE):
        chunk.rename(columns={0: 'is_classified', 1: "read_name", 2: "classified_species", 3: "read_length",
                              4: "all_classified_K_mers"}, inplace=True)
        chunk['split'] = chunk['all_classified_K_mers'].apply(
            lambda x: [y.split(':') for y in x.split()])  # split list and makes pairs (specie, k-mers)
        chunk['split'] = chunk['split'].apply(lambda x: sorted(x, key=itemgetter(0)))  # sort by specie (inside each row)
        chunk['split'] = chunk['split'].apply(lambda x: [(key, sum([int(y[1]) for y in group])) for key, group in
                                                                 groupby(x, key=itemgetter(
                                                                     0))])  # groupby specie and count by k-mers
        chunk['total_k_mer_count'] = chunk['split'].apply(lambda x: sum([i[1] for i in x]))  # calculate sum of k mers
        chunk['max_specie'] = chunk['split'].apply(lambda x: max(x, key=itemgetter(1))[0])  # calculate max speice
        chunk['max_k_mer_count'] = chunk['split'].apply(lambda x: max(x, key=itemgetter(1))[1])  # calculate k-mers
        chunk['max_k_mer_p'] = chunk['max_k_mer_count'] / chunk['total_k_mer_count']

        chunk["bins_max_k_mer_p"] = pd.cut(chunk["max_k_mer_p"], [x/100 for x in range(101)],
                                           precision=0,
                                           labels=[x/100 for x in range(1, 101)],
                                           right=True)  # split k_mers to bins
        df_preprocess_temp = pd.crosstab(chunk.max_specie, chunk.bins_max_k_mer_p).T

        if first:
            chunk[RESULTS_COLUMNS_TO_KEEP].to_csv(str(processed_for_PostProcess_results_path), mode='a', header=True, index=False)
            df_preprocess = df_preprocess_temp
            first = False
        else:
            chunk[RESULTS_COLUMNS_TO_KEEP].to_csv(str(processed_for_PostProcess_results_path), mode='a', header=False, index=False)
            df_preprocess = df_preprocess.append(df_preprocess_temp)
    df_preprocess.fillna(0, inplace=True)
    df_preprocess = df_preprocess.astype(int)
    df_preprocess = df_preprocess.groupby(df_preprocess.index).sum()
    df_preprocess.to_csv(processed_for_UI_results_path)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Running RL project Main')
    parser.add_argument('--outputFilePath', default=None, help='path to output file to process')
    args = parser.parse_args()
    process_output(**vars(args))

