import pandas as pd
from operator import itemgetter
from itertools import groupby

PRECISION_K_MERS = 100

df_origin = pd.read_csv("/bioseq/data/results/genome_fltr/7f13cd6e-3ffe-4e1c-93c7-96ea539fdbde/results.txt", sep='\t', header=None)
df_origin['split'] = df_origin[4].apply(lambda x: [y.split(':') for y in x.split()]) # split list and makes pairs (specie, k-mers)
df_origin['split'] = df_origin['split'].apply(lambda x: sorted(x, key=itemgetter(0))) # sort by specie
df_origin['split'] = df_origin['split'].apply(lambda x: [(key, sum([int(y[1]) for y in group])) for key, group in groupby(x, key=itemgetter(0))]) # groupby specie and count by k-mers 
df_origin['max_specie'] = df_origin['split'].apply(lambda x: max(x, key=itemgetter(1))[0]) # calculate max speice
df_origin['max_k_mer'] = df_origin['split'].apply(lambda x: max(x, key=itemgetter(1))[1]) # calculate k-mers
df_origin['max_k_mer_p'] = df_origin['max_k_mer'] / df_origin[3]

df_origin["bins_max_k_mer_p"] = pd.cut(df_origin["max_k_mer_p"],[x for x in range(PRECISION_K_MERS + 1)], precision=0, labels=[x for x in range(PRECISION_K_MERS)]) # split k_mers to bins

df_preprocess = pd.crosstab(df_origin.max_specie,df_origin.bins_max_k_mer_p)
df_preprocess.to_csv('/bioseq/data/results/genome_fltr/7f13cd6e-3ffe-4e1c-93c7-96ea539fdbde/preprocess.csv')