
import sys,os
import json
import argparse
import numpy as np
import ubjson
import json
from scipy.special import sph_harm, lpmn
from mpmath import mp, spherharm

# shape (nb_unit_vectors,3)
def load_unit_vectors_from_json():
    fn = "../tests/reference_data/spherical_harmonics_test.json"
    with open(fn,'r') as f:
        data = json.load(f)
    return data['unit_vectors']

# Sized (l_max+0)**2, contains the l,m components in compressed
# format, i.e. (00)(1-1)(10)(11)(2-2).... as it is in our spherical
# harmonics calculation

def get_ascending_angular_lists(max_angular_l):
    ascending_angular_m_list = []
    ascending_angular_l_list = []
    for angular_l in range(max_angular_l+1):
        ascending_angular_m_list += list(range(-angular_l,angular_l+1))
        ascending_angular_l_list += [angular_l] * (angular_l*2+1)
    return ascending_angular_m_list, ascending_angular_l_list


def dump_lpmn_reference_json():
    # TODO(alex) lpmn think about how the matrix should be saved because they are a (m+1,n+1) array
    path = '../'
    sys.path.insert(0, os.path.join(path, 'build/'))
    sys.path.insert(0, os.path.join(path, 'tests/'))
    data = []
    mp.dps = 200;

    directions = load_unit_vectors_from_json()
    max_angular_l = 31
    for direction in directions:
        lpmn_results = []
        z = direction[2] # = cos_theta
        # one could use numpy broadcasting, but this is more readable
        for angular_l in range(max_angular_l+1):
            for angular_m in range(-angular_l, angular_l+1):
                result = np.real(lpmn(angular_m, angular_l, z))
                lpmn_results.append(result)
        data.append(dict(max_angular_l=max_angular_l, direction=direction, associated_legendre=lpmn_results))
    print(len(data))
    with open(path+"tests/reference_data/associated_legendre_reference.ubjson",'wb') as f:
        ubjson.dump(data,f)
    return

# scipy alreay includes the Condon-Shortley phase, therefore to calculate the
# real form we use
#         ╭ √2 Im[Y_l^|m|] for m<0
#         |
# Y_l^m = ┤     Y_l^0      for m==0
#         |
#         ╰ √2 Re[Y_l^m]   for m<0
# where Y_l^m is the output of the spherical harmonics function of scipy
def dump_reference_json():
    verbose=False
    path = '../'
    sys.path.insert(0, os.path.join(path, 'build/'))
    sys.path.insert(0, os.path.join(path, 'tests/'))
    data = []

    # Calculation of spherical harmonics
    ## with mpmath:
    ## spherharm(angular_l,angular_m, theta, phi)
    ## with scipy:
    ## sph_harm(angular_m, angular_l, phi, theta)

    unit_vectors = load_unit_vectors_from_json()
    # to produces more readable tests change to 1 or 2
    max_angular_l = 31
    for unit_vector in unit_vectors:
        harmonics = []
        # copy of c++ code:
        # double cos_theta = unit_vector[2];
        theta = np.arccos(unit_vector[2])
        # copy of c++ code:
        # double phi = std::atan2(unit_vector[1], unit_vector[0]);
        phi = np.arctan2(unit_vector[1], unit_vector[0])
        if verbose:
            print(unit_vector)
        for angular_l in range(max_angular_l+1):
            # this part could be done more efficient by using the results from 
            # the last calculation but this seems more readable

            # calculation for negative angular_m
            for angular_m in range(-angular_l,0):
                result = np.sqrt(2)*np.imag(sph_harm(np.abs(angular_m), angular_l, phi, theta)) 
                harmonics.append(float(result))
                if verbose:
                    print(angular_l, angular_m, result)
            # calculation for m=0 
            result = np.real(sph_harm(0, angular_l, phi, theta))
            harmonics.append(float(result))
            if verbose:
                print(angular_l, 0, result)
            # calculation for positive angular_m
            for angular_m in range(1, angular_l+1):
                result = np.sqrt(2)*np.real(sph_harm(angular_m, angular_l, phi, theta)) 
                harmonics.append(float(result))
                if verbose:
                    print(angular_l, angular_m, result)
        data.append(dict(max_angular_l=int(max_angular_l), unit_vector=unit_vector, harmonics=harmonics))
    print(len(data))
    with open(path+"tests/reference_data/spherical_harmonics_reference.ubjson",'wb') as f:
        ubjson.dump(data,f)


##########################################################################################
##########################################################################################

def main(json_dump):
    if json_dump == True:
        dump_reference_json()

##########################################################################################
##########################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-json_dump', action='store_true', help='Switch for dumping json')

    args = parser.parse_args()
    main(args.json_dump)
