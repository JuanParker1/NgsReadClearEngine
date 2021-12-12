import argparse
from itertools import groupby
from operator import itemgetter
from pathlib import Path
import os
import pandas as pd
from SharedConsts import K_MER_COUNTER_MATRIX_FILE_NAME, RESULTS_FOR_OUTPUT_CLASSIFIED_RAW_FILE_NAME, \
    DF_LOADER_CHUCK_SIZE, RESULTS_COLUMNS_TO_KEEP, RESULTS_FOR_OUTPUT_UNCLASSIFIED_RAW_FILE_NAME, \
    UNCLASSIFIED_COLUMN_NAME, RESULTS_SUMMARY_FILE_NAME, SUMMARY_RESULTS_COLUMN_NAMES, TEMP_CLASSIFIED_IDS, \
    TEMP_UNCLASSIFIED_IDS


def parse_kmer_data(kraken_raw_output_df):
    """
    parses the k mer column in the kraken output into a list of pairs (species of k-mer, number of matched k-mers)
    :param kraken_raw_output_df:  data frame of the kraken output
    :return: the same df with the "split" column parsed
    """
    # split list and makes pairs (specie, k-mers)
    kraken_raw_output_df['split'] = kraken_raw_output_df['all_classified_K_mers'].apply(
        lambda x: [y.split(':') for y in x.split()])
    # sort by specie (inside each row)
    kraken_raw_output_df['split'] = kraken_raw_output_df['split'].apply(lambda x: sorted(x, key=itemgetter(0)))
    # group by specie and count by k-mers
    kraken_raw_output_df['split'] = kraken_raw_output_df['split'].apply(lambda x: [(key, sum(
        [int(y[1]) for y in group])) for key, group in groupby(x, key=itemgetter(0))])

    return kraken_raw_output_df


def get_NCBI_renaming_dict(summary_res_df):
    """
    extracts the ncbi taxonomy data from the karaken summary file
    :param summary_res_path: path to the relevant kraken
    :return:
    """
    temp_naming_df = summary_res_df[['ncbi_taxonomyID', 'name']]
    temp_naming_df['ncbi_taxonomyID'] = temp_naming_df['ncbi_taxonomyID'].astype(str)
    temp_naming_df['name'] = temp_naming_df['name'] + ' (taxid ' + temp_naming_df['ncbi_taxonomyID'] + ')'
    renaming_dict = temp_naming_df.set_index('ncbi_taxonomyID').to_dict()['name']
    return renaming_dict


def calc_kmer_statistics(kmer_df):
    """
    this function calculates the k-mer metrics needed for the output matrix
    :param kmer_df: the mid processing k-mer data frame
    :return: kmer_df with a few more k-mer statistics columns
    """
    # calculate sum of k mers
    kmer_df['total_k_mer_count'] = kmer_df['split'].apply(lambda x: sum([i[1] for i in x]))
    # calculate max species
    kmer_df['max_specie'] = kmer_df['split'].apply(lambda x: max(x, key=itemgetter(1))[0])
    # calculate k-mers
    kmer_df['max_k_mer_count'] = kmer_df['split'].apply(lambda x: max(x, key=itemgetter(1))[1])
    # calculate percentile
    kmer_df['max_k_mer_p'] = kmer_df['max_k_mer_count'] / kmer_df['total_k_mer_count']
    # sort into bins according to the percentile of k-mers
    kmer_df["bins_max_k_mer_p"] = pd.cut(kmer_df["max_k_mer_p"], [x / 100 for x in range(101)], precision=0,
                                         labels=[x / 100 for x in range(1, 101)], right=True)

    return kmer_df


def process_output(**kwargs):
    """
    reads kraken results in manageable chunks and pre-processes the results for the UI and final output exports
    :param kwargs: must have a key "outputFilePath"
    :return: the number of unclassified organisms
    """
    # parse arguments and set up
    outputFilePath = Path(kwargs['outputFilePath'])
    if outputFilePath is None:
        raise Exception("no output file path was provided for pre-processor")

    processed_for_UI_results_path = outputFilePath.parent / K_MER_COUNTER_MATRIX_FILE_NAME
    processed_Unclassified_for_PostProcess_results_path = \
        outputFilePath.parent / RESULTS_FOR_OUTPUT_UNCLASSIFIED_RAW_FILE_NAME
    processed_Classified_for_PostProcess_results_path = \
        outputFilePath.parent / RESULTS_FOR_OUTPUT_CLASSIFIED_RAW_FILE_NAME
    results_summary_path = outputFilePath.parent / RESULTS_SUMMARY_FILE_NAME
    temp_unclass_path = outputFilePath.parent / TEMP_UNCLASSIFIED_IDS
    temp_class_path = outputFilePath.parent / TEMP_CLASSIFIED_IDS

    first = True
    how_many_unclassified = 0
    # used later to prepare the files for faster post process
    classified_ids = []
    unclassified_ids = []

    # make sure there are no old things that will make the df appending wrong
    for file in [processed_Classified_for_PostProcess_results_path, processed_Unclassified_for_PostProcess_results_path,
                 processed_for_UI_results_path]:
        if file.is_file():
            os.remove(str(file))

    # prepare renaming dict
    summary_res_df = pd.read_csv(results_summary_path, sep='\t', names=SUMMARY_RESULTS_COLUMN_NAMES)
    summary_res_df['name'] = summary_res_df['name'].str.strip()
    ncbi_renaming_dict = get_NCBI_renaming_dict(summary_res_df)
    # todo: export as json with the three relevant summary statistics

    # main processing loop
    for chunk in pd.read_csv(outputFilePath, sep='\t', header=None, chunksize=DF_LOADER_CHUCK_SIZE):

        # process the results
        chunk.rename(columns={0: 'is_classified', 1: "read_name", 2: "classified_species", 3: "read_length",
                              4: "all_classified_K_mers"}, inplace=True)
        # calculations
        chunk = parse_kmer_data(chunk)
        chunk = calc_kmer_statistics(chunk)
        # typing and naming
        chunk.replace({"max_specie": ncbi_renaming_dict}, inplace=True)
        chunk['max_k_mer_p'] = chunk['max_k_mer_p'].astype(float)
        chunk['all_classified_K_mers'] = chunk['all_classified_K_mers'].astype(str)
        chunk['classified_species'] = chunk['classified_species'].astype(str)

        # separate unclassified and classified results
        # fix kraken discrepancy with us
        kraken_mistakes = chunk[(chunk['is_classified'] == 'C') & (chunk['max_specie'] == UNCLASSIFIED_COLUMN_NAME)]
        chunk.drop(kraken_mistakes.index, inplace=True)
        # actually separate
        unclassified_chunk = chunk[chunk['is_classified'] == 'U'].append(kraken_mistakes)
        classified_chunk = chunk[chunk['is_classified'] == 'C']
        how_many_unclassified += len(unclassified_chunk.index)

        # create UI results matrix where its percentiles as rows, k-mers as columns and counts as values
        df_preprocess_temp = pd.crosstab(classified_chunk.max_specie, classified_chunk.bins_max_k_mer_p).T

        # save results:
        classified_ids += list(classified_chunk["read_name"])
        unclassified_ids += list(unclassified_chunk["read_name"])

        if first:
            unclassified_chunk[RESULTS_COLUMNS_TO_KEEP].to_csv(str(processed_Unclassified_for_PostProcess_results_path),
                                                               mode='a', header=True, index=False)
            classified_chunk[RESULTS_COLUMNS_TO_KEEP].to_csv(str(processed_Classified_for_PostProcess_results_path),
                                                             mode='a', header=True, index=False)
            df_preprocess = df_preprocess_temp
            first = False
        else:
            unclassified_chunk[RESULTS_COLUMNS_TO_KEEP].to_csv(str(processed_Unclassified_for_PostProcess_results_path),
                                                               mode='a', header=False, index=False)
            classified_chunk[RESULTS_COLUMNS_TO_KEEP].to_csv(str(processed_Classified_for_PostProcess_results_path),
                                                             mode='a', header=False, index=False)
            df_preprocess = df_preprocess.append(df_preprocess_temp)

    # save final matrix for UI
    df_preprocess.fillna(0, inplace=True)
    df_preprocess = df_preprocess.astype(int)
    df_preprocess = df_preprocess.groupby(df_preprocess.index).sum()
    # add unclassified to matrix
    df_preprocess[UNCLASSIFIED_COLUMN_NAME] = 0
    line = pd.DataFrame(data=[[0 for i in df_preprocess.columns]], columns=df_preprocess.columns, index=[0.00])
    line[UNCLASSIFIED_COLUMN_NAME] = how_many_unclassified
    df_preprocess = line.append(df_preprocess)

    df_preprocess.to_csv(processed_for_UI_results_path)

    # create search lists for SeqKit
    classified_ids_string = '\n'.join(classified_ids)
    unclassified_ids_string = '\n'.join(unclassified_ids)
    with open(temp_class_path, 'w') as fp:
        fp.write(classified_ids_string)
    with open(temp_unclass_path, 'w') as fp:
        fp.write(unclassified_ids_string)

    # make sure permissions are good
    processed_for_UI_results_path.chmod(777)
    processed_Classified_for_PostProcess_results_path.chmod(777)
    processed_Unclassified_for_PostProcess_results_path.chmod(777)

    return how_many_unclassified


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Running RL project Main')
    parser.add_argument('--outputFilePath', default=None, help='path to output file to process')
    args = parser.parse_args()
    process_output(**vars(args))
