# Select what values in a CSV file to visualize.

# Default behavior:
# * Set G to the main DPP candidate's votes.
# * Set B to the main KMT candidate's votes.
# * Set R to the sum of the rest candidates' votes.
# * Normalize [R, G, B] so that V := max(R, G, B) == 1.0
# * Set V (brightness in HSV space) to participation rate (投票率).
#   * participation rate := #(voter) / #(eligible voter)
# * Create or overwrite `rgb/data.csv`.

# Options:
# --out=<RGB name>  Set output file path to `rgb/<RGB name>.csv`.
# --red=<name>      Set R to a specific candidate.
# --green=<name>    Set G to a specific candidate.
# --blue=<name>     Set B to a specific candidate.
# --ignorePR        Set participation rate to 1.0.
#                   This makes the colors as bright as possible,
#                   but eliminates information of participation rate.

# To customize further, Google Sheets or similar software is recommended.
# Please refer to the example `rgb/南港.csv` file for the required format.

# Requirements:
#   <python> -m pip install pandas numpy
# Usage:
#   <python> select_data.py ../data/<data name>.csv [<option> ...]
# Example usage:
#   <python> select_data.py ../data/臺北市_南港區_立委第4選區_投開票所.csv --out=南港
# Example output:
#   rgb/南港.csv

# %% parse options

import sys, pandas

argv = sys.argv
assert len(argv) >= 2, argv

# necessary parameters
in_file_path = argv[1]
df = pandas.read_csv(in_file_path)
print(f'read CSV file: {in_file_path}')
in_file_name = in_file_path.replace('\\', '/').split('/')[-1]
try:
    county, town = in_file_name.split('_')[:2]
except ValueError:
    print(f'failed to parse input CSV file name: {in_file_name}')
    print('  expected format: <county>_<town><anything>(村里|投開票所)<anything>.csv')
    print('  example:         臺北市_南港區_立委第4選區_投開票所.csv')
    exit()
div_type = '投開票所' if '投開票所' in in_file_name else '村里'
print('inferred these from input file name:')
print(f'  county:   {county}')
print(f'  town:     {town}')
print(f'  division: {div_type}')

# optional parameters
out_file_path = 'rgb/data.csv'
R_label = 'default'
G_label = 'default'
B_label = 'default'
ignorePR = False
for option in argv[2:]:
    if option.startswith('--out='):
        out_file_path = f'rgb/{option[6:]}.csv'
    elif option.startswith('--red='):
        R_label = option[6:]
    elif option.startswith('--green='):
        G_label = option[8:]
    elif option.startswith('--blue='):
        B_label = option[7:]
    elif option == '--ignorePR':
        ignorePR = True
    else:
        print(f'unknown option: {option}')
        exit()

# %% find the candidates corresponding to R, G, B 

candidates = df['名字'].to_list()[:-1]
parties = df['政黨'].to_list()[:-1]
table = df.iloc[:, 3:].to_numpy().T
vote_counts = table.sum(axis=0)[:-1]

if G_label == 'default':
    DPP_list = []
    for idx, (party, vote_count) in enumerate(zip(parties, vote_counts)):
        if party == '民主進步黨':
            DPP_list.append((idx, vote_count))
    assert len(DPP_list) > 0, '民主進步黨 candidate not found. Please specify --green=<name>'
    DPP_list.sort(key=lambda t: t[1])
    G_idx = DPP_list[-1][0]
    G_label = candidates[G_idx]
else:
    G_idx = candidates.index(G_label)
G_data = table[:, G_idx]

if B_label == 'default':
    KMT_list = []
    for idx, (party, vote_count) in enumerate(zip(parties, vote_counts)):
        if party == '中國國民黨':
            KMT_list.append((idx, vote_count))
    assert len(KMT_list) > 0, '中國國民黨 candidate not found. Please specify --blue=<name>'
    KMT_list.sort(key=lambda t: t[1])
    B_idx = KMT_list[-1][0]
    B_label = candidates[B_idx]
else:
    B_idx = candidates.index(B_label)
B_data = table[:, B_idx]

if R_label == 'default':
    indices = list(range(table.shape[1] - 1))
    indices.remove(G_idx)
    indices.remove(B_idx)
    R_data = table[:, indices].sum(axis=1)
    R_label = '其他'
else:
    R_idx = candidates.index(R_label)
    R_data = table[:, R_idx]

print(f'R: {R_label}')
print(f'G: {G_label}')
print(f'B: {B_label}')
assert len(set((R_label, G_label, B_label))) == 3, 'R, G, B labels have to be different.'

# %% normalize [R, G, B] and rescale to participation rate

import numpy as np

# normalize
RGB_data = np.stack([R_data, G_data, B_data], axis=1)
RGB_data = RGB_data / RGB_data.max(axis=1, keepdims=True)
np.nan_to_num(RGB_data, copy=False, nan=0.0, posinf=0.0)

# rescale to participation rate
if ignorePR:
    print('V in HSV color space (brightness) set to 1.0 (0.0 for zero-vote divisions)')
else:
    PR = table[:, :-1].sum(axis=1) / table[:, -1]
    np.nan_to_num(PR, copy=False, nan=0.0, posinf=0.0)
    RGB_data *= PR[:, None]
    print('V in HSV color space (brightness) set to participation rate')

R_data, G_data, B_data = RGB_data.T

# %% output

metadata = f'{county} {town} {div_type}'
df_out = pandas.DataFrame(
    data={metadata: df.columns[3:], R_label: R_data, G_label: G_data, B_label: B_data},
    columns=[metadata, R_label, G_label, B_label])
df_out.to_csv(out_file_path, index=False)
print(f'generated file: {out_file_path}')

# %%
