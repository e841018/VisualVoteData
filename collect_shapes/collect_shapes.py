# Collect longitude and latitude data from SHP files and save as Python pickles.

# Requirements:
#   <python> -m pip install pyshp numpy
# Usage:
#   <python> collect_shapes.py <county name> <town name>
# Example usage:
#   <python> collect_shapes.py 臺北市 南港區
# Example output:
#   shapes/臺北市_南港區.pkl

# Note that the generated pickles have no dependencies on phshp or numpy.

# %% set target

import sys
target_county = '臺北市'
target_town = '南港區'
argv = sys.argv
if len(argv) >= 3:
    target_county = argv[1]
    target_town = argv[2]

# %% read shapefiles

import shapefile
def read_shapefile(prefix_list):
    all_shapes = []
    all_records = []
    for prefix in prefix_list:
        sf = shapefile.Reader(prefix) # read shp, shx, dbf

        shapes = sf.shapes()
        print(f'{prefix}: {len(shapes)} shapes')
        all_shapes += shapes

        records = sf.records()
        print(f'{prefix}: {len(records)} records')
        all_records += records

        assert len(shapes) == len(records), (len(shapes), len(records))
        print('fields: [name, type, length, decimal length]')
        for field in sf.fields[1:]:
            print(f'        {field}')
        
    return all_shapes, all_records

t_shapes, t_records = read_shapefile(['鄉(鎮、市、區)界線1140318/TOWN_MOI_1140318', '鄉(鎮、市、區)界線1140318/Town_Majia_Sanhe'])
v_shapes, v_records = read_shapefile(['村里界歷史圖資1111118/VILLAGE_MOI_1111118', '村里界歷史圖資1111118/Village_Sanhe'])
n_shapes, n_records = read_shapefile(['臺北市鄰界圖_20250101_ShpTrans/G97_A_CALIN_P'])

# %% select towns, villages, neighborhoods

t_selection = []
for r, record in enumerate(t_records):
    if record.COUNTYNAME == target_county and record.TOWNNAME == target_town:
        t_selection.append(r)
print(f'selected {len(t_selection)} towns')

v_selection = []
for r, record in enumerate(v_records):
    if record.COUNTYNAME == target_county and record.TOWNNAME == target_town:
        v_selection.append(r)
        if record.NOTE != '':
            print(f'NOTE: {record.COUNTYNAME} {record.TOWNNAME} {record.VILLNAME}: {record.NOTE}')
print(f'selected {len(v_selection)} villages')

n_selection = []
for r, record in enumerate(n_records):
    if '臺北市' == target_county and record.SECT_NAME == target_town:
        n_selection.append(r)
print(f'selected {len(n_selection)} neighborhoods')

# %% calculate centroids and collect parts

import numpy as np
def calc_centroid(xy_list):
    assert len(xy_list) > 2, len(xy_list)
    assert xy_list[0] == xy_list[-1], (xy_list[0], xy_list[-1])
    x, y = np.array(xy_list).T
    areas = (x[:-1] * y[1:] - x[1:] * y[:-1]) / 2
    areas_sum = areas.sum()
    centroids_x = (x[:-1] + x[1:]) / 3
    centroids_y = (y[:-1] + y[1:]) / 3
    centroid_x = (centroids_x * areas).sum() / areas_sum
    centroid_y = (centroids_y * areas).sum() / areas_sum
    return float(centroid_x), float(centroid_y), abs(float(areas_sum))

def collect_parts(shape):
    assert shape.shapeType == 5, shape.shapeType
    idxs = list(shape.parts) + [None]
    parts = []
    centroids = []
    for p in range(len(shape.parts)):
        part = shape.points[idxs[p]:idxs[p+1]]
        parts.append(part)
        centroids.append(calc_centroid(part))
    centroids.sort(key=lambda t: t[2]) # sort with area
    centroid = centroids[-1][:2] # use the centroid of the largest
    return parts, centroid

towns = {}
empty_name_count = 0
for s in t_selection:
    shape = t_shapes[s]
    record = t_records[s]

    # manual fixes for `鄉(鎮、市、區)界線1140318/Town_Majia_Sanhe`
    if s == 368: # keep only part 1 since part 0 of t_shapes[368] is roughly same as t_shapes[132]
        towns['瑪家鄉'][0].extend(collect_parts(shape)[0][1:]) # append parts
        print(f'{record.COUNTYNAME} {record.TOWNNAME}: {2} parts')
        continue

    if len(shape.parts) > 1:
        print(f'{record.COUNTYNAME} {record.TOWNNAME}: {len(shape.parts)} parts')
    name = record.TOWNNAME
    if name == '':
        name = f'empty_{empty_name_count}'
        empty_name_count += 1
        print(f'renamed empty name into {name}')
    assert name not in towns, f'found duplicate name: {name}'
    towns[name] = collect_parts(shape)

villages = {}
empty_name_count = 0
for s in v_selection:
    shape = v_shapes[s]
    record = v_records[s]
    if len(shape.parts) > 1:
        print(f'{record.COUNTYNAME} {record.TOWNNAME} {record.VILLNAME}: {len(shape.parts)} parts')
    name = record.VILLNAME
    if name == '':
        name = f'empty_{empty_name_count}'
        empty_name_count += 1
        print(f'renamed empty name into {name}')
    assert name not in villages, f'found duplicate name: {name}'
    villages[name] = collect_parts(shape)

neighborhoods = {}
empty_name_count = 0
for s in n_selection:
    shape = n_shapes[s]
    record = n_records[s]

    # manual fixes for `臺北市鄰界圖_20250101_ShpTrans/G97_A_CALIN_P`
    if s == 4471: # rows 4450, 4471 are both 臺北市/內湖區/紫陽里/12鄰
        neighborhoods['紫陽里12鄰'][0].extend(collect_parts(shape)[0]) # append parts
        print(f'臺北市 {record.SECT_NAME} {record.LIE_NAME} {record.SDFNAME}: {2} parts')
        continue
    elif s == 4943: # 臺北市/內湖區/金瑞里/2鄰 -> 臺北市/內湖區/金瑞里/22鄰
        record.SDFNAME = '金瑞里22鄰'
    elif s == 8719: # rows 8684, 8719 are both 臺北市/南港區/新光里/12鄰
        neighborhoods['新光里12鄰'][0].extend(collect_parts(shape)[0]) # append parts
        print(f'臺北市 {record.SECT_NAME} {record.LIE_NAME} {record.SDFNAME}: {2} parts')
        continue

    if len(shape.parts) > 1:
        print(f'臺北市 {record.SECT_NAME} {record.LIE_NAME} {record.SDFNAME}: {len(shape.parts)} parts')
    name = record.SDFNAME
    if name == '':
        name = f'empty_{empty_name_count}'
        empty_name_count += 1
        print(f'renamed empty name into {name}')
    assert name not in neighborhoods, f'found duplicate name: {name}'
    neighborhoods[name] = collect_parts(shape)

# %% dump pkl

import pickle
file_name = f'{target_county}_{target_town}.pkl'
with open(f'../shapes/{file_name}', 'wb') as f:
    pickle.dump((towns, villages, neighborhoods), f)
print(f'generated file in shapes/: {file_name}')

# %%
