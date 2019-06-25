import os, sys
import re
import numpy as np
from math import sqrt
from numpy.linalg import svd, eigh
from paraparser.indexparser import parse_index, rev_parse_index
from fileparser.parse49 import parse_49
from filegenerator.genfchk import quicksave

VERSION = 'V3.1'
VERSIONTEXT = 'Original published version honorably delivered by Acid&Francium (with a blast).\nUpdated on 25 June 2019 by Changsu.\n'

tol = 1e-6

def myeigh(mat, rev=False):
    evals, evecs = eigh(mat)
    evecs = evecs.T
    if rev:
        order = evals.argsort()[::-1]
    else:
        order = evals.argsort()
    evals = evals[order]
    evecs = evecs[order]
    return evals, evecs

#def

def genPIO(data, fragmentation=None):
    # input
    #data = parse_49(fn49)

    title = data['title']
    naoao = data['NAOAO']
    dmnao = data['DNAO']
    try:
        fmnao = data['FNAO']
    except KeyError:
        pass
    naolabels = data['NAOlabel']
    dim = naoao.shape[0]
    assert dmnao.shape == (dim, dim)

    # detect fragment orbitals
    if not fragmentation:
        prompt = '$ Please input the atom ID of two fragments: (e.g. 1-5,8,13 6-7,9-12)\n$ '
        command = eval(input(prompt))
        # command = '1 2'
    else:
        command = fragmentation
    fragments = command.strip().lower().split()
    assert len(fragments) == 2
    atoms1 = parse_index(fragments[0])
    atoms2 = parse_index(fragments[1])
    oids1 = np.array([orb for orb in range(dim) if naolabels[orb].center in atoms1])
    oids2 = np.array([orb for orb in range(dim) if naolabels[orb].center in atoms2])
    assert len(set(oids1)) == len(oids1)
    assert len(set(oids2)) == len(oids2)
    assert not set(oids1).intersection(set(oids2))
    if set(oids1).union(set(oids2)) != set(range(dim)):
        print('Warning: Incomplete fragmentation detected!')
    if set([naolabels[orb].center for orb in oids1]) != set(atoms1):
        print('Warning: Ghost atoms detected in fragment A!')
    if set([naolabels[orb].center for orb in oids2]) != set(atoms2):
        print('Warning: Ghost atoms detected in fragment B!')

    # compute PIOs
    vals1, vecs1 = eigh(dmnao[oids1,:][:,oids1])
    vals2, vecs2 = eigh(dmnao[oids2,:][:,oids2])
    vecs1, vecs2 = vecs1.T, vecs2.T
    off_block = vecs1.dot(dmnao[oids1,:][:,oids2]).dot(vecs2.T)
    off_block[abs(off_block) < tol] = 0
    U, D, V = svd(off_block, full_matrices = True)
    U = vecs1.T.dot(U)
    V = V.dot(vecs2)
    print((U.shape, V.shape))
    D2 = D**2
    print((np.array2string(D2, formatter =
        {'float_kind': lambda x: ('%.3f' % x if x >= 0.001 else '0')})))
    print(('Total interaction:', D2.sum()))

    pionao = np.eye(dim)
    pionao[np.array(oids1)[:,None],oids1] = U.T
    pionao[np.array(oids2)[:,None],oids2] = V
    if len(oids1) == len(oids2):
        pass
    else:
        if len(oids1) > len(oids2):
            nullspace = np.array(oids1)[len(oids2):]
        else:
            nullspace = np.array(oids2)[len(oids1):]
        print(nullspace)
        dm = pionao.dot(dmnao).dot(pionao.T)
        evals, evecs = myeigh(dm[nullspace[:,None],nullspace], rev=True)
        pionao[nullspace] = evecs.dot(pionao[nullspace])
        try:
            fm = pionao.dot(fmnao).dot(pionao.T)
            null2 = nullspace[abs(evals-2)<tol]
            null0 = nullspace[abs(evals-0)<tol]
            print(null2)
            evals, evecs = myeigh(fm[null2[:,None],null2])
            print(evals)
            pionao[null2] = evecs.dot(pionao[null2])
            print(null0)
            evals, evecs = myeigh(fm[null0[:,None],null0])
            print(evals)
            pionao[null0] = evecs.dot(pionao[null0])
        except NameError:
            pass

    # output
    d = dict()
    d['flag_spin'] = data['flag_spin']
    d['srcfile'] = data['fn49'] #fn49
    d['title'] = os.path.splitext(os.path.split(data['fn49'])[1])[0] if title == 'Title Card Required' else title
    d['dim'] = dim
    d['fragments'] = (sorted(set([naolabels[orb].center for orb in oids1])),
        sorted(set([naolabels[orb].center for orb in oids2])))
    d['oids'] = (oids1, oids2)
    d['PBI'] = D2
    d['Contribution'] = D2 / (D2.sum())
    d['PIOAO'] = pionao.dot(naoao)
    d['DPIO'] = pionao.dot(dmnao).dot(pionao.T)
    try:
        d['FPIO'] = pionao.dot(fmnao).dot(pionao.T)
    except NameError:
        pass

    dm = d['DPIO']
    pimonao = np.copy(pionao)
    for oid1, oid2 in zip(oids1, oids2):
        D = dm[np.array([oid1, oid2])[:,None],[oid1,oid2]]
        evals, evecs = myeigh(D,rev=True)
        # if abs(vals[0] - vals[1]) <= tol:
            # vecs = eigh(F)[1]
        pimonao[[oid1,oid2]] = evecs.dot(pionao[[oid1,oid2]])
    d['PIMOAO'] = pimonao.dot(naoao)
    d['DPIMO'] = pimonao.dot(dmnao).dot(pimonao.T)
    try:
        d['FPIMO'] = pimonao.dot(fmnao).dot(pimonao.T)
    except NameError:
        pass

    return d

def spin_dict_split(data_dict):
    dict_alpha, dict_beta = {}, {}
    for key, value in data_dict.items():
        if hasattr(value, 'ndim'):
            if value.ndim == 3:
                assert value.shape[0] == 2
                dict_alpha[key] = value[0]
                dict_beta[key] = value[1]
            else:
                dict_alpha[key] = dict_beta[key] = value
        else:
            dict_alpha[key] = dict_beta[key] = value
    return dict_alpha, dict_beta

def saveRawData(data, suffix=''):
    import pickle
    with open(os.path.join(os.path.split(data['srcfile'])[0],
        data['title']+'_pio{}.raw'.format(suffix)), 'wb') as f:
        pickle.dump(data, f)

def saveTxt(data, suffix=''):
    atoms1, atoms2 = data['fragments']
    oids1, oids2 = data['oids']
    ixn = data['PBI']
    dm = data['DPIO']
    fm = data.get('FPIO', np.zeros_like(dm))

    pops1 = np.diag(dm)[oids1]
    pops2 = np.diag(dm)[oids2]
    energies1 = np.diag(fm)[oids1]
    energies2 = np.diag(fm)[oids2]
    total = sum(ixn)
    contrib = ixn / total * 100
    cum = np.cumsum(contrib)
    if not fm is None:
        ie = [fm[i][j] for i, j in zip(oids1, oids2)]
    else:
        ie = [0 for i, j in zip(oids1, oids2)]

    popb = []
    popa = []
    eb = []
    ea = []
    rie = []
    for d11, d22, f11, f22, d12d12, f12 in \
        zip(pops1, pops2, energies1, energies2, ixn, ie):
        d12 = sqrt(d12d12)
        D = np.array([[d11, d12], [d12, d22]])
        F = np.array([[f11, f12], [f12, f22]])
        vals, vecs = eigh(D)
        if abs(vals[0] - vals[1]) <= tol:
            vecs = eigh(F)[1]
        newD = vecs.dot(D).dot(vecs.T)
        newF = vecs.dot(F).dot(vecs.T)
        popb.append(newD[1, 1])
        popa.append(newD[0, 0])
        eb.append(newF[1, 1])
        ea.append(newF[0, 0])
        rie.append(newF[0, 1])

    text = list(zip(np.array(oids1) + 1, pops1, energies1,
        np.array(oids2) + 1, pops2, energies2,
        ixn, contrib, cum, ie,
        eb, ea, popb, popa, rie))
    # for line in text:
        # print line

    mod = '%4d%10f%12f%4d%10f%12f%10f%10f%8.2f%12f%12f%12f%10f%10f%12f'
    modt = re.sub('(\.\d+)?[fd]', 's', mod)

    with open(os.path.join(os.path.split(data['srcfile'])[0],
        data['title']+'_pio{}.txt'.format(suffix)), 'w') as f:
        f.write('PIO %s\n' % VERSION)
        f.write('%s\n' % VERSIONTEXT)
        f.write('Fragment A: %s (Orbitals: %s)\n' % (rev_parse_index(atoms1), rev_parse_index(oids1+1)))
        f.write('Fragment B: %s (Orbitals: %s)\n' % (rev_parse_index(atoms2), rev_parse_index(oids2+1)))
        f.write('Fragment A'.center(26))
        f.write('Fragment B'.center(26))
        f.write('\n')
        f.write(modt % ('Orb', 'Pop   ', 'E    ', 'Orb', 'Pop   ', 'E    ',
            'Ixn   ', 'Contrib%', 'Cum%', 'IE   ',
            'EB   ', 'EA   ', 'PopB  ', 'PopA  ', 'RIE   '))
        f.write('\n')

        while text:
            f.write(mod % text.pop(0))
            f.write('\n')

        print('PIO result saved to file.\n')

def saveFChk(data, mfn, suffix=''):
    pioao = data['PIOAO']
    quicksave(mfn, pioao, data.get('FPIO', np.zeros(pioao.shape[0])),
        suffix='_pio{}'.format(suffix), overwrite=True)
    pimoao = data['PIMOAO']
    quicksave(mfn, pimoao, data.get('FPIMO', np.zeros(pimoao.shape[0])),
        suffix='_pimo{}'.format(suffix), overwrite=True)

def saveAll(data, mfn, suffix=''):
    saveRawData(data, suffix)
    saveTxt(data, suffix)
    saveFChk(data, mfn, suffix)

def main():
    fragmentation = ' '.join(sys.argv[2:4]) or None
    ffchk = sys.argv[1]
    f49 = os.path.splitext(ffchk)[0].upper() + '.49'
    data_dict = parse_49(f49)
    if not data_dict['flag_spin']:
        data = genPIO(data_dict, fragmentation)
        saveAll(data, ffchk)
    else:
        data_a, data_b = spin_dict_split(data_dict)
        data_a = genPIO(data_a, fragmentation)
        data_b = genPIO(data_b, fragmentation)
        saveAll(data_a, ffchk, suffix='_alpha')
        saveAll(data_b, ffchk, suffix='_beta')




if __name__ == '__main__':
    main()


