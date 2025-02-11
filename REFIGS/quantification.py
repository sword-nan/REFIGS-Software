from multiprocessing import Queue

import pandas as pd
import numpy as np

from .myms import spectrum_normalization, LoadMS2, deconvolute,get_scanNum_per_cycle
from CsoDIAq import spectra_matcher_functions as smf


def refigs_quantification(
    text_queue: Queue,
    ids_file: str,
    SSM_file: str,
    mzxml_file: str,
    raw_library: dict[str, dict],
    tol: int = 20
):
    tol = tol * 1e-6

    library = spectrum_normalization(raw_library)
    text_queue.put(
        smf.print_milestone(
            f"{'#' * 15}  loading SSM file...  {'#' * 15}")
    )
    Identify = pd.read_csv(SSM_file, sep=',')
    Identify['Precursor'] = Identify[['peptide', 'zLIB']].apply(
        lambda x: x['peptide']+'_'+str(x['zLIB']), axis=1)
    smf.print_milestone(
        f"{'#' * 15}'  loading mzML file...  '{'#' * 15}")
    MS2 = LoadMS2(mzxml_file)
    MS2_dict = {}
    for ms2 in MS2:
        MS2_dict[ms2[-1]] = ms2

    text_queue.put(
        smf.print_milestone(f"{'#' * 15}  claculating coeffs...  {'#' * 15}")
    )
    output = []
    scans = set(Identify['scan'].values)
    for i, scan in enumerate(scans):
        if i % 1000 == 0:
            text_queue.put(
                smf.print_milestone(
                    f'{i}/{len(scans)}\t FIGS is calculating coeffs')
            )
        tmp_df = Identify[Identify['scan'] == scan]
        keys = tmp_df['Precursor'].values
        tmp_library = {}
        for key in keys:
            tmp_library[(key.split('_')[0], int(key.split('_')[1]))
                        ] = library[(key.split('_')[0], int(key.split('_')[1]))]
        tmp_ms2 = MS2_dict[scan]
        output.extend(deconvolute(tmp_ms2, tmp_library, tol, False))

    Coeffs = pd.DataFrame(output,columns=['Coeff', 'scan', 'peptide', 'charge', 'windowMZ', 'spectrumRT', 'level', 'corr'])
    # print(Coeffs)
    
    ids = pd.read_csv(ids_file, sep=',')
    Coeffs = Coeffs[Coeffs['peptide'].apply(
        lambda x: x in set(ids['peptide']))
    ]

    Coeffs.to_csv(SSM_file.replace('.csv', '_Coeffs.csv'), index=False, header=[
        'Coeff', 'scan', 'peptide', 'charge', 'windowMZ', 'spectrumRT', 'level', 'corr'])
    text_queue.put(
        smf.print_milestone('calculate coeffs over!')
    )
    
    # 系数补全
    coeffs_toquant=Coeffs.copy()
    scans_per_cycle = get_scanNum_per_cycle(mzxml_file)
    
    coeffs_toquant=coeffs_toquant[coeffs_toquant['level']==2]
    unikeys = set(coeffs_toquant[['peptide', 'charge']].apply(tuple, axis=1))
    for key in unikeys:
        tmp_df = coeffs_toquant[(coeffs_toquant['peptide'] == key[0]) & (coeffs_toquant['charge'] == key[1])]
        tmp_df = tmp_df.sort_values('scan')
        i=0
        

    

def fillcoeffs(
    coeffs: np.ndarray,
    max_void_num: int = 4
):
    pass

def quantification_from_coeffs(
    coeffs: np.ndarray,
):
    pass
