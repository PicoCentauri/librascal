#!/usr/bin/env python
# coding: utf-8

import os

import ase.io
import numpy as np

from rascal import representations, utils
from rascal import models # Must happen after 'import rascal.utils'; see #273

WORKDIR = os.getcwd()


def calculate_representation(
        geoms, rep_parameters,
        rep_class=representations.SphericalInvariants, auto_wrap=True):
    """Calculate SOAP vectors without sparsification

    Parameters:
        geoms       List of Atoms objects to transform
        rep_parameters
                    Dictionary of parameters used to initialize the
                    representation
    Optional arguments:
        rep_class   Class that specifies which representation to use
                    (default rascal.representations.SphericalInvariants)
        auto_wrap   Automatically wrap all the atoms so they are
                    "inside" the periodic cell by the libRascal
                    definition?  (Default True, recommended for periodic
                    structures).
                    WARNING: Structures intended to be treated as
                    non-periodic require special handling -- do not use
                    this option!  Manually pad the cell and shift the
                    positions instead.

    Returns the Representation object and the SOAP vectors in a tuple.
    """
    rep = rep_class(**rep_parameters)
    if auto_wrap:
       for geom in geoms:
           geom.wrap(eps=1E-10)
    soaps = rep.transform(geoms)
    return rep, soaps


#TODO support FPS as well as CUR selection
def calculate_and_sparsify(geoms, rep_parameters, n_sparse,
                           rep_class=representations.SphericalInvariants,
                           auto_wrap=True):
    """Calculate SOAP vectors and sparsify using CUR

    Parameters:
        geoms       List of Atoms objects to transform
        rep_parameters
                    Dictionary of parameters used to initialize the
                    representation
        n_sparse    Number of sparse points per species, in the form of
                    a dict mapping atomic number to number of requested
                    sparse points
    Optional arguments:
        rep_class   Class that specifies which representation to use
                    (default rascal.representations.SphericalInvariants)
        auto_wrap   Automatically wrap all the atoms so they are
                    "inside" the periodic cell by the libRascal
                    definition?  (Default True, recommended for periodic
                    structures).
                    WARNING: Structures intended to be treated as
                    non-periodic require special handling -- do not use
                    this option!  Manually pad the cell and shift the
                    positions instead.

    Returns the Representation object, the SOAP vectors, and the sparse
    points, in a 3-tuple.
    """
    rep = rep_class(**rep_parameters)
    if auto_wrap:
       for geom in geoms:
           geom.wrap(eps=1E-10)
    soaps = rep.transform(geoms)
    compressor = utils.CURFilter(
            rep, n_sparse, act_on='sample per species')
    sparse_points_cur = compressor.fit_transform(soaps)
    utils.dump_obj(os.path.join(WORKDIR, 'sparsepoints.json'),
                   sparse_points_cur)
    return rep, soaps, sparse_points_cur


def compute_kernels(rep, soaps, sparse_points, soap_power=2,
                    do_gradients=True, compute_sparse_kernel=True):
    """Compute the kernels necessary for a GAP fit

    Parameters:
        rep     Representation object (holds representation
                hyperparameters; necessary for initializing the kernel)
        soaps   SOAP vectors of all training structures
        sparse_points
                Support points for the fit, containing SOAP vectors for
                the selected environments

    Optional arguments:
        soap_power
                Integer power to which to raise the SOAP kernel;
                defaults to 2 (to make the kernel nonlinear)
        do_gradients
                Whether to compute the gradients kernel as well in order
                to fit forces.  Default True; fitting with gradients is
                more expensive but usually much more accurate than
                fitting on energies alone.
        compute_sparse_kernel
                Whether to compute the sparse-sparse kernel (K_MM)
                needed to do a fit.  Note that it is not necessary to
                recompute this kernel when evaluating an existing fit on
                new data; therefore, this option can be set to False for
                that task.  If this option is set to False, an empty
                array will be returned in place of the sparse kernel.

    Returns a tuple of: the kernel object (which contains all the kernel
    parameters), the sparse kernel, and the energy kernel (and force
    kernel, if requested).
    """
    kernel = models.Kernel(
            rep, name='GAP', zeta=soap_power,
            target_type='Structure', kernel_type='Sparse')
    if compute_sparse_kernel:
        kernel_sparse = kernel(sparse_points)
        np.save(os.path.join(WORKDIR, 'K_MM'), kernel_sparse)
    else:
        kernel_sparse = np.array([])
    kernel_sparse_full = kernel(soaps, sparse_points)
    #TODO make kernel name configurable so we don't overwrite training
    #     kernels with possible future test kernels
    np.save(os.path.join(WORKDIR, 'K_NM_E'), kernel_sparse_full)
    if do_gradients:
        kernel_sparse_full_grads = kernel(soaps, sparse_points,
                                          grad=(True, False))
        np.save(os.path.join(WORKDIR, 'K_NM_F'), kernel_sparse_full_grads)
        return (kernel, kernel_sparse,
                kernel_sparse_full, kernel_sparse_full_grads)
    else:
        return kernel, kernel_sparse, kernel_sparse_full


def _get_energy_baseline(geom, atom_contributions):
    """Get the energy baseline for a single structure

    Depends only on the number of atoms of each atomic species present;
    the 'atom_contributions' dictionary says how much energy to assign
    to an atom of each species.
    """
    e0 = 0.
    for species, e0_value in atom_contributions.items():
        e0 += e0_value * np.sum(geom.get_atomic_numbers() == species)
    return e0

#TODO also make energies optional
def fit_gap_simple(geoms, kernel_sparse, energies, kernel_energies_sparse,
                   energy_regularizer_peratom, energy_atom_contributions,
                   forces=None, kernel_gradients_sparse=None,
                   force_regularizer=None, rcond=None):
    """
    Fit a GAP model to total energies and optionally forces

    Simple version; just takes geometries, kernels, energies, and forces,
    returning only the weights.  No automatic scaling by target property
    variance; the regularizers should therefore be the _ratio_ of the
    expected error in the property to the expected scale (variance) of
    the fitted energy surface.

    In the notation below, M is the number of sparse points, N is the
    number of training structures, and P is the total number of atoms
    in the training structures.

    Parameters:
        geoms           Training structures: List of Atoms objects
        kernel_sparse   Kernel between sparse points and themselves:
                        NumPy array of shape MxM
        energies        Total energies of the structures to fit
        kernel_energies_sparse
                        Kernel between sparse points and training
                        structures: NumPy array of shape NxM
        energy_regularizer_peratom
                        Energy regularizer (actually ratio between
                        expected error and expected target variance;
                        see above).  Expressed in energy units per atom,
                        therefore scaled with the size of the structure.
        energy_atom_contributions
                        Baseline energy contributions per atomic species
                        Dict mapping species to baseline energy value
                        per atom

    Parameters for force fitting:
        forces          Forces of the structures to fit: NumPy array of
                        shape Px3 (or NxQx3 where N*Q=P)
        kernel_gradients_sparse
                        Gradient kernel between sparse points and target
                        structures: NumPy array of shape 3PxM
                        Note that gradients are the negative of the
                        forces, though this is mostly handled
                        transparently by the code (just pass in forces)
        force_regularizer
                        Force regularizer (see above), in units of
                        energy / distance (component-wise)

    Optional arguments:
        rcond           Condition number cutoff for matrix inversion at
                        the core of the fit.  Default (and highly
                        recommended) None; see the documentation for
                        numpy.linalg.lstsq for more details.

    Returns the weights (1-D array, size M) that define the fit.
    """
    e0_all = np.array([_get_energy_baseline(geom, energy_atom_contributions)
                       for geom in geoms])
    energies_shifted = energies - e0_all
    natoms_list = np.array([len(geom) for geom in geoms])
    energy_regularizer = energy_regularizer_peratom * np.sqrt(natoms_list)
    kernel_energies_norm = (kernel_energies_sparse
                            / energy_regularizer[:,np.newaxis])
    if forces is not None:
        gradients = -1 * forces
        kernel_gradients_norm = kernel_gradients_sparse / force_regularizer
        K_NM = np.vstack((kernel_energies_norm, kernel_gradients_norm))
        Y = np.concatenate((energies_shifted / energy_regularizer,
                            gradients.flatten() / force_regularizer))
    else:
        K_NM = kernel_energies_norm
        Y = energies_shifted / energy_regularizer
    K = kernel_sparse + K_NM.T @ K_NM
    weights, *_ = np.linalg.lstsq(K, K_NM.T @ Y, rcond=rcond)
    return weights


def load_potential(model_in, rep_parameters,
                   rep_class=representations.SphericalInvariants):
    """Load a previously fitted model as an ASE Calculator

    Parameters:
        model_in            KRR model, either a rascal.models.KRR
                            instance or the filename of a model stored
                            in JSON format
        rep_parameters      Dictionary of parameters used to initialize
                            the representation
        rep_class           Class that specifies which representation
                            to use (default
                            rascal.representations.SphericalInvariants)

    Returns an ASE Calculator (rascal.models.ASEMLCalculator instance)
    that computes energies and forces of ASE Atoms objects
    """
    if isinstance(model_in, models.KRR):
        model = model_in
    else:
        model = utils.load_obj(model_in)
    rep = rep_class(**rep_parameters)
    return models.IP_ase_interface.ASEMLCalculator(model, rep)

