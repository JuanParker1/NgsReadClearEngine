from KrakenHandlers.SearchEngine import SearchEngine
from OutputProcessor import process_output
from KrakenHandlers.SearchResultAnalyzer import run_post_process
if __name__ == "__main__":
    a ={'outputFilePath':"/groups/pupko/alburquerque/kraken_out_1.txt"}
    process_output(**a)
    run_post_process(path_to_classified_results = "/groups/pupko/alburquerque/ResultsForPostProcessClassifiedRaw.csv",
                     path_to_final_result_file = "/groups/pupko/alburquerque/ResultsForPostProcessClassifiedRawFiltered.csv",
                     path_to_unclassified_results = "/groups/pupko/alburquerque/ResultsForPostProcessUnClassifiedRaw.csv",
                     classification_threshold = 0.3)
    # se = SearchEngine.kraken_search("/groups/pupko/alburquerque/kraken_out_1.txt", {})
