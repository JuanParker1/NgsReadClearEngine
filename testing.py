from KrakenHandlers.SearchResultAnalyzer import run_post_process
from OutputProcessor import process_output
from KrakenHandlers.SearchEngine import SearchEngine

if __name__ == "__main__":
    # a = {"outputFilePath": "/groups/pupko/alburquerque/example.fasta"}
    a = {"outputFilePath": "/groups/pupko/alburquerque/results.txt",
         "remove_only_high_level_res": True}

    # SearchEngine.kraken_search("/groups/pupko/alburquerque/example.fasta", {})
    b = process_output(**a)
    # run_post_process(root_folder="/groups/pupko/alburquerque/", classification_threshold=0.3,
    #                  species_to_filter_on=["Salmonella (taxid 590)", "Enterobacteriaceae (taxid 543)", 2220, 12])
    print('a')
