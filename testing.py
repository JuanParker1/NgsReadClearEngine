from KrakenHandlers.SearchResultAnalyzer import run_post_process
from OutputProcessor import process_output
from KrakenHandlers.SearchEngine import SearchEngine

if __name__ == "__main__":
    # a = {"outputFilePath": "/groups/pupko/alburquerque/example.fasta"}
    a = {"outputFilePath": "/groups/pupko/alburquerque/results.txt"}

    # SearchEngine.kraken_search("/groups/pupko/alburquerque/example.fasta",{})
    # b = process_output(**a)
    run_post_process(path_to_classified_results="/groups/pupko/alburquerque/ResultsForPostProcessClassifiedRaw.csv",
                     path_to_final_result_file="/groups/pupko/alburquerque/ResultsForPostProcessClassifiedRawFiltered.fasta",
                     path_to_unclassified_results="/groups/pupko/alburquerque/ResultsForPostProcessUnClassifiedRaw.csv",
                     classification_threshold=0.3, species_to_filter_on=["Salmonella (taxid 590)", "Enterobacteriaceae (taxid 543)", 2220, 12],
                     path_to_original_unclassified_data="/groups/pupko/alburquerque/unclassified.fasta",
                     path_to_original_classified_data="/groups/pupko/alburquerque/classified.fasta")
    print('a')
