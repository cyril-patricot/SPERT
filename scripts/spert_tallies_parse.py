#!/usr/bin/env python


def main():
    """
    Receives tallies.out file, and produces sorted tally files
    ordered by lexicographic notation and scoring
    """
    # define dictionary for pincell lexicographic notation
    lat_5x5 = ['l21']
    lat_4x4 = ['l330', 'l331', 'l402']
    qtr_core_4x4 = ['l6']
    rows_5x5 = ['E','D','C','B','A']
    rows_4x4 = ['D','C','B','A']
    dc = dict()
    for i in range(len(rows_5x5)):
        for j in range(5):
            for lat in lat_5x5:
                dc[lat+'('+str(i)+','+str(j)+')'] = rows_5x5[i]+str(j+1)
    for i in range(len(rows_4x4)):
        for j in range(4):
            for lat in lat_4x4:
                dc[lat+'('+str(i)+','+str(j)+')'] = rows_4x4[i]+str(j+1)
    for i in range(len(rows_4x4)):
        for j in range(4):
            for lat in qtr_core_4x4:
                dc[lat+'('+str(i)+','+str(j)+')'] = rows_4x4[i]+str(j+1)+'_'

    # extract data
    score_all = []
    with open('tallies.out', 'r') as fin:
        flag_first_score = True
        for line in fin:
            if 'TALLY' in line and '_2' not in line:
                score = line.split()
                score_all.append(score[3])
                if not flag_first_score:
                    fout.close()
                fout = open(score_all[-1]+'.out', 'w')
                flag_first_score = False
            if 'Distributed Cell' in line:
                for item in dc.keys():
                    pc1 = ''
                    pc2 = ''
                    if item in line:
                        pc1 = ''
                        if '_' in dc[item]:
                            pc1 = dc[item]
                        else:
                            pc2 = dc[item]
                fout.write('\n'+pc1+pc2+': ')
            if '+/-' in line:
                val = line.split()
                if val[0] == 'Flux':
                    mean = '%.6e'%float(val[1])
                    std = '%.6e'%float(val[3])
                else:
                    mean = '%.6e'%float(val[2])
                    std = '%.6e'%float(val[4])
                fout.write(mean + ', ' + std + ', ')
    fout.close()

    # remove empty line at header, add empty line at end
    for score in score_all:
        with open(score+'.out', 'r') as fin:
            data = fin.read().splitlines(True)
        with open(score+'.out', 'w') as fout:
            fout.writelines(data[1:])
            fout.write('\n')

    # sort entries
    for score in score_all:
        with open(score+'.out', 'r') as fin:
            data = fin.read().splitlines(True)
        with open(score+'.out', 'w') as fout:
            fout.writelines(sorted(data))

if __name__ == "__main__":
    main()
