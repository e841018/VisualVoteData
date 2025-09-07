# Distill legislator vote data of a town and save as csv files.

# Requirements:
#   <python> -m pip install pandas numpy
# Usage:
#   <python> distill_legislators.py <county name> <town name>
# Example usage:
#   <python> distill_legislators.py 臺北市 南港區
# Example output:
#   data/臺北市_南港區_立委第4選區_村里.csv
#   data/臺北市_南港區_立委第4選區_投開票所.csv

# Hierarchy of administrative and electroral divisions in the votedata database:
#   PCODE   province            省, 直轄市
#   CCODE   county              縣, 市
#   TCODE   town                鄉, 鎮, 縣轄市, 區
#   VCODE   village             村, 里
#   PPID    polling place       投開票所
#   -       neighborhood        鄰

# Electoral district is a special tier. An electoral district is contained in a
# single county, but could include villages from multiple towns. In other words,
# it's neither above nor below town in the hierarchy. Electoral district is
# currently only used in the Legislative Yuan elections.
#   ECODE   electoral district  選區

# Some polling places are composed of neighbors from differnt villages,
# such as this one:
#   PCODE = 10      (臺灣省)
#   CCODE = 8       (南投縣)
#   ECODE = 1       (第1選區)
#   TCODE = 10      (魚池鄉)
#   VCODE = '0A01'  (新城村、共和村)
#   PPID  = 224     (新城村17鄰、共和村4-11鄰)
# These polling places would have a special village assigned for them,
# whose VCODEs contain 'A'. This assignment has some consequences:
#   * Excluding electoral districts, the hierarchy is well-defined.
#     Each division is contained in a single parent division.
#   * The counts of some villages will not be accurate.
#     E.g., the counts of 新城村 will not include the counts from PPID 224.

# %% set target

import sys
target_county = '臺北市'
target_town = '南港區'
argv = sys.argv
if len(argv) >= 3:
    target_county = argv[1]
    target_town = argv[2]

# %% find area codes

import pandas
df_base = pandas.read_csv('votedata/voteData/2024總統立委/區域立委/elbese.csv', names=[
        'PCODE', # province code
        'CCODE', # county code
        'ECODE', # electoral district code 
        'TCODE', # town code
        'VCODE', # village code
        'NAME', # name
    ],
    dtype={
        'PCODE': 'uint16',
        'CCODE': 'uint16',
        'ECODE': 'uint16',
        'TCODE': 'uint16',
        'VCODE': 'string',
        'NAME': 'string',
    })
def select_PCT(df, PCODE, CCODE, TCODE, keep_town = False):
    df = df[df.PCODE == PCODE]
    df = df[df.CCODE == CCODE]
    df = df[df.TCODE == TCODE]
    if not keep_town:
        df = df[df.VCODE != '0000']
    return df

# county: PCODE and CCODE
df = df_base[(df_base.TCODE == 0)]
df = df[df.NAME == target_county]
assert len(df) == 1, df
PCODE = df.PCODE.iat[0]
CCODE = df.CCODE.iat[0]

# town: TCODE
df = df_base[(df_base.PCODE == PCODE) & (df_base.CCODE == CCODE)]
df = df[df.VCODE == '0000']
df = df[df.NAME == target_town]
ECODEs = list(df.ECODE)
assert len(set(df.TCODE)) == 1, df.TCODE
TCODE = df.TCODE.iat[0]

# village: VCODE
df_village = select_PCT(df_base, PCODE, CCODE, TCODE).sort_values(by='VCODE')
print(f'{target_county} {target_town}: {len(df_village)} villages')
print(df_village)

# %% collect candidate info

# party
df_paty = pandas.read_csv('votedata/voteData/2024總統立委/區域立委/elpaty.csv', names=[
        'PARID', # party ID
        'PNAME', # party name
    ],
    dtype={
        'PARID': 'uint16',
        'PNAME': 'string',
    })
party = {}
for idx, PARID, PNAME in df_paty.itertuples():
    party[PARID] = PNAME

# candidate
df_cand = pandas.read_csv('votedata/voteData/2024總統立委/區域立委/elcand.csv', names=[
        'PCODE', # province code
        'CCODE', # county code
        'ECODE', # electoral district code 
        'TCODE', # town code
        'VCODE', # village code
        'CANID', # candidate ID
        'CNAME', # candidate name
        'PARID', # party ID
        'GENDR', # gender
        'BDATE', # birth date
        'CAAGE', # candidate age
        'BPLAC', # birth place
        'EDBAC', # educational background
        'ISINC', # is incumbent
        'ELECT', # electee
        'ISASS', # is assistant
    ],
    dtype={
        'PCODE': 'uint16',
        'CCODE': 'uint16',
        'ECODE': 'uint16',
        'TCODE': 'uint16',
        'VCODE': 'string',
        'CANID': 'uint16',
        'CNAME': 'string',
        'PARID': 'uint16',
        'GENDR': 'uint16',
        'BDATE': 'string',
        'CAAGE': 'uint16',
        'BPLAC': 'string',
        'EDBAC': 'string',
        'ISINC': 'string',
        'ELECT': 'string',
        'ISASS': 'string',
    })
candidates_ECODE = {}
for ECODE in ECODEs:
    candidates = []
    df = df_cand[(df_cand.PCODE == PCODE) & (df_cand.CCODE == CCODE) & (df_cand.ECODE == ECODE)]
    for row in df.itertuples():
        candidates.append((row.CANID, row.CNAME, party[row.PARID]))
    candidates_ECODE[ECODE] = sorted(candidates, key=lambda r: r[0])
    print(f'ECODE = {ECODE}:')
    for candidate in candidates:
        print(candidate)

# %% collect result data

import numpy as np

# load result csv files
df_ctks = pandas.read_csv('votedata/voteData/2024總統立委/區域立委/elctks.csv', names=[
        'PCODE', # province code
        'CCODE', # county code
        'ECODE', # electoral district code 
        'TCODE', # town code
        'VCODE', # village code
        'PPID', # polling place ID
        'CANID', # candidate ID
        'VOTEC', # vote count
        'VOTER', # vote ratio
        'ELECT', # electee
    ],
    dtype={
        'PCODE': 'uint16',
        'CCODE': 'uint16',
        'ECODE': 'uint16',
        'TCODE': 'uint16',
        'VCODE': 'string',
        'PPID': 'uint16',
        'CANID': 'uint16',
        'VOTEC': 'uint32',
        'VOTER': 'float32',
        'ELECT': 'string',
    })
df_prof = pandas.read_csv('votedata/voteData/2024總統立委/區域立委/elprof.csv', names=[
        'PCODE', # province code
        'CCODE', # county code
        'ECODE', # electoral district code 
        'TCODE', # town code
        'VCODE', # village code
        'PPID', # polling place ID
        'VALIC', # valid count
        'INVAC', # invalid count
        'TVOTC', # total vote count
        'ELIGC', # eligible count
        'POPUC', # population count
        'CANDC', # candidate count
        'ELECC', # electee count
        'CANDCM', # candidate count (male)
        'CANDCF', # candidate count (female)
        'ELECCM', # electee count (male)
        'ELECCF', # electee count (female)
        'ELIGR', # ELIGC / POPUC * 100
        'TVOTR', # TVOTC / ELIGC * 100
        'ELECR', # ELECC / CANDC * 100
    ],
    dtype={
        'PCODE': 'uint16',
        'CCODE': 'uint16',
        'ECODE': 'uint16',
        'TCODE': 'uint16',
        'VCODE': 'string',
        'PPID': 'uint16',
        'VALIC': 'uint32',
        'INVAC': 'uint32',
        'TVOTC': 'uint32',
        'ELIGC': 'uint32',
        'POPUC': 'uint32',
        'CANDC': 'uint16',
        'ELECC': 'uint16',
        'CANDCM': 'uint16',
        'CANDCF': 'uint16',
        'ELECCM': 'uint16',
        'ELECCF': 'uint16',
        'ELIGR': 'float32',
        'TVOTR': 'float32',
        'ELECR': 'float32',
    })

# load and process polling place names
class PollingPlaceName:
    def __init__(self, target_county, target_town):
        self.unknown_count = 0
        self.df_pp = pandas.read_csv(f'pp_list/{target_county}_{target_town}_pp_list.csv')
    @staticmethod
    def parse_list(NEIGHBORHOODS):
        if NEIGHBORHOODS == '所有的鄰':
            return '所有的鄰'
        assert len(NEIGHBORHOODS) > 1, NEIGHBORHOODS
        assert NEIGHBORHOODS[-1] == '鄰', NEIGHBORHOODS
        nums = NEIGHBORHOODS[:-1].replace('、', ',').replace(', ', ',')
        assert all(c in '0123456789-,' for c in nums), nums
        nums = nums.split(',')
        vill_list = []
        for num in nums:
            if '-' in num: # e.g., '9-12'
                num = num.split('-')
                assert len(num) == 2, num
                start, stop = num
                for n in range(int(start), int(stop) + 1):
                    vill_list.append(n)
            else: # e.g., '3'
                vill_list.append(int(num))
        return '_'.join([str(v) for v in vill_list])
    def get(self, PPID):
        df = self.df_pp[self.df_pp.PPID == PPID]
        if len(df) == 0:
            pp_name = f'unknown_{self.unknown_count}'
            self.unknown_count += 1
            print(f'unknown polling place (PPID={PPID}): assigned name {pp_name}')
            return pp_name
        else:
            pp_name_list = []
            for idx, PPID, VILLNAME, NEIGHBORHOODS in df.itertuples():
                pp_name_list.append(f'{VILLNAME}_{self.parse_list(NEIGHBORHOODS)}')
            return ' '.join(pp_name_list)
get_pp_name = PollingPlaceName(target_county, target_town).get

# collect result data of the target town
df_ctks = select_PCT(df_ctks, PCODE, CCODE, TCODE)
df_prof = select_PCT(df_prof, PCODE, CCODE, TCODE)
for ECODE in ECODEs: # some towns belong to multiple electoral districts
    df_ctks_E = df_ctks[df_ctks.ECODE == ECODE]
    df_prof_E = df_prof[df_prof.ECODE == ECODE]
    candidates = candidates_ECODE[ECODE]
    cidx = {}
    for c, (CANID, CNAME, PNAME) in enumerate(candidates):
        cidx[CANID] = c

    # each village
    df_candi = df_ctks_E[df_ctks_E.PPID == 0] # len(villages) * len(candidates) rows
    df_total = df_prof_E[df_prof_E.PPID == 0] # len(villages) rows
    villages = sorted(set(df_candi.VCODE))
    assert villages == sorted(df_village[df_village.ECODE==ECODE].VCODE), villages
    assert villages == sorted(df_total.VCODE), df_total
    assert len(villages) * len(candidates) == len(df_candi), (len(villages), len(candidates), len(df_candi))
    # np table:
    #   rows: *villages
    #   columns: *candidates, total
    table = np.zeros((len(villages), len(candidates) + 1), dtype=np.uint32)
    vidx = {}
    for v, VCODE in enumerate(villages):
        vidx[VCODE] = v
    for row in df_candi.itertuples():
        table[vidx[row.VCODE]][cidx[row.CANID]] = row.VOTEC
    for row in df_total.itertuples():
        table[vidx[row.VCODE]][-1] = row.ELIGC
    # pandas DataFrame:
    #   rows: *candidates, total
    #   columns: CANID, CNAME, PNAME, *villages
    CANIDs, CNAMEs, PNAMEs = [*zip(*candidates, (0, '選舉人數', '-'))]
    data = {'號次': CANIDs, '名字': CNAMEs, '政黨': PNAMEs}
    columns = ['號次', '名字', '政黨']
    for VCODE, row in zip(villages, table):
        village_name = df_village[df_village.VCODE==VCODE].NAME.iat[0]
        data[village_name] = row
        columns.append(village_name)
    assert len(data) == len(columns), (len(data), len(columns))
    df = pandas.DataFrame(data, columns=columns)
    file_name = f'{target_county}_{target_town}_立委第{ECODE}選區_村里.csv'
    df.to_csv(f'../data/{file_name}', index=False)
    print(f'generated file in data/: {file_name}')

    # each polling place
    df_candi = df_ctks_E[df_ctks_E.PPID != 0] # len(pps) * len(candidates) rows
    df_total = df_prof_E[df_prof_E.PPID != 0] # len(pps) rows
    pps = sorted(set(df_candi.PPID))
    assert pps == sorted(df_total.PPID), df_total
    assert len(pps) * len(candidates) == len(df_candi), (len(pps), len(candidates), len(df_candi))
    # np table:
    #   rows: *pps
    #   columns: *candidates, total
    table = np.zeros((len(pps), len(candidates) + 1), dtype=np.uint32)
    pidx = {}
    for p, PPID in enumerate(pps):
        pidx[PPID] = p
    for row in df_candi.itertuples():
        table[pidx[row.PPID]][cidx[row.CANID]] = row.VOTEC
    for row in df_total.itertuples():
        table[pidx[row.PPID]][-1] = row.ELIGC
    # pandas DataFrame:
    #   rows: *candidates, total
    #   columns: CANID, CNAME, PNAME, *pps
    CANIDs, CNAMEs, PNAMEs = [*zip(*candidates, (0, '選舉人數', '-'))]
    data = {'號次': CANIDs, '名字': CNAMEs, '政黨': PNAMEs}
    columns = ['號次', '名字', '政黨']
    for PPID, row in zip(pps, table):
        pp_name = get_pp_name(PPID)
        data[pp_name] = row
        columns.append(pp_name)
    assert len(data) == len(columns), (len(data), len(columns))
    df = pandas.DataFrame(data, columns=columns)
    file_name = f'{target_county}_{target_town}_立委第{ECODE}選區_投開票所.csv'
    df.to_csv(f'../data/{file_name}', index=False)
    print(f'generated file in data/: {file_name}')

# %%
