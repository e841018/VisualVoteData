# Export RGB data to image, interactive webpage, and KML (Google Earth) formats.

# Requirements:
#   <python> -m pip install pandas numpy matplotlib
# Usage:
#   <python> export.py <path prefix> <RGB name 0> [<RGB name 1> ...]
# Example usage:
#   <python> export.py ../output/港湖 南港 內湖
# Example output:
#   ../output/港湖.png

# %% read files

import sys, pandas, pickle
argv = sys.argv
assert len(argv) >= 3, argv
out_path_prefix = argv[1]
RGB_names = argv[2:]

df_list = []
shapes_list = []
shape_paths = []
town_names = []
for RGB_name in RGB_names:
    path = f'rgb/{RGB_name}.csv'
    df = pandas.read_csv(path)
    df_list.append(df)
    county, town, div_type = df.columns[0].split(' ')
    print('-' * 80)
    print(f'read CSV file: {path}')
    print(f'  county:   {county}')
    print(f'  town:     {town}')
    print(f'  division: {div_type}')
    path = f'../shapes/{county}_{town}.pkl'
    with open(path, 'rb') as f:
        shapes = pickle.load(f)
    shapes_list.append(shapes)
    shape_paths.append(path)
    town_names.append(town)
    print(f'read shape file: {path}')
    print(f'  {len(shapes[0])} towns')
    print(f'  {len(shapes[1])} villages')
    print(f'  {len(shapes[2])} neighborhoods')
print('-' * 80)

# %% export to image

import numpy as np
aspect = 1 / np.cos(25 / 180 * np.pi) # latitude is about 25 degrees North at Taipei

import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
fontManager.addfont('asset/Noto_Sans_TC/static/NotoSansTC-Regular.ttf')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'Noto Sans TC'
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.cm import ScalarMappable

def parse_neighborhood_name(pp_name):
    v_name_list = []
    n_name_list = []
    for village in pp_name.split(' '):
        village = village.split('_')
        v_name = village[0]
        v_name_list.append(v_name)
        for n_number in village[1:]:
            n_name = f'{v_name}{n_number}鄰'
            n_name_list.append(n_name)
    return v_name_list, n_name_list

# create figure
fig = plt.figure(figsize=(10, 10), dpi=100)
ax = fig.add_axes(plt.Axes(fig, (0, 0, 1, 1)))
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_facecolor('0.8')
ax.set_aspect(aspect, 'datalim')
ax.margins(x=0.01, y=0.01)

for df, shapes, path in zip(df_list, shapes_list, shape_paths):
    can_names = df.columns[1:].to_list()
    div_names = df.iloc[:, 0].to_list()
    div_colors = df.iloc[:, 1:].to_numpy()
    towns, villages, neighborhoods = shapes

    # neighborhoods
    village_set = set()
    for pp_name, color in zip(div_names, div_colors):
        v_name_list, n_name_list = parse_neighborhood_name(pp_name)
        for v_name in v_name_list:
            village_set.add(v_name)
        for n_name in n_name_list:
            if n_name not in neighborhoods:
                print(f'warning: {n_name} not found in {path}')
                continue
            parts, centroid = neighborhoods[n_name]
            points = []
            codes = []
            for part in parts:
                assert len(part) >= 1, part
                points += part
                codes.append(Path.MOVETO)
                codes.extend([Path.LINETO] * (len(part) - 1))
            ax.add_patch(PathPatch(Path(points, codes), linewidth=0, facecolor=color))

    # villages
    for v_name, (parts, centroid) in villages.items():
        if v_name not in village_set:
            continue
        for part in parts:
            ax.plot(*zip(*part), color='w', linewidth=1)
        ax.annotate(v_name, centroid, ha='center', va='center', fontsize=10)

    # towns
    for t_name, (parts, centroid) in towns.items():
        for part in parts:
            ax.plot(*zip(*part), color='w', linewidth=2)

# title
ax_title = fig.add_axes(plt.Axes(fig, (0, 0, 1, 1)))
ax_title.set_axis_off()
ax_title.set_xlim(0, 1)
ax_title.set_ylim(0, 1)
ax_title.annotate('、'.join(town_names) + '\n2024區域立委', (0.98, 0.98), ha='right', va='top', fontsize=40)

# color reference
ax_cref = fig.add_axes(plt.Axes(fig, (0.7, 0.4, 0.2, 0.19)))
ax_cref.set_axis_off()
ax_cref.imshow(plt.imread('asset/cref.png'))
ax_cref.annotate(can_names[0], (256, 140), color='k', ha='center', va='center', fontsize=15)
ax_cref.annotate(can_names[1], (110, 415), color='k', ha='center', va='center', fontsize=15)
ax_cref.annotate(can_names[2], (400, 415), color='k', ha='center', va='center', fontsize=15)

# color bar
if 'ignorePR' not in RGB_names[0]:
    ax_cbar = fig.add_axes(plt.Axes(fig, (0.7, 0.38, 0.2, 0.02)))
    fig.colorbar(ScalarMappable(cmap='gray'), cax=ax_cbar, orientation='horizontal')
    ax_cbar.set_xticks([0, 0.5, 1])
    ax_cbar.set_xticklabels(['0%', '投票率', '100%'], fontsize=15)

plt.savefig(f'{out_path_prefix}.png')

# %%
