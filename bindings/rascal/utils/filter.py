import logging
import numpy as np
from .io import BaseIO
from ..models.sparse_points import SparsePoints

LOGGER = logging.getLogger(__name__)

try:
    from skcosmo._selection import _FPS, _CUR
except ImportError as ie:
    LOGGER.warn(
        "Warning: skcosmo module not found. CUR and FPS filters will be unavailable."
    )
    LOGGER.warn("Original error:\n" + str(ie))
    _FPS = _CUR = None

# utility functions for Filters


def get_index_mappings_sample_per_species(managers, sps):
    """Get various info from the structures about the center atom species
    and indexing per species.

    Parameters
    ----------

    managers : AtomsList
        list of atomic structures
    sps : list
        list of unique center atom species present in managers

    Returns
    -------

    strides_by_sp : dict
        list the positions of the begining of each structure in arrays that
        have one row per atom of species sp
    global_counter : dict
        count the number of atoms of a particular element sp
    map_by_manager : dict
        map species / structure index / global atom index to the atom index
        in the structure
    indices_by_sp : dict
        map position in arrays that have one row per atom of species sp to
        the position in array that has one row per atom
    """

    # list of the atom types following the order in managers accross the
    # atomic structures
    types = []
    strides_by_sp = {sp: [0] for sp in sps}
    global_counter = {sp: 0 for sp in sps}
    indices_by_sp = {sp: [] for sp in sps}
    map_by_manager = {sp: [{} for ii in range(len(managers))] for sp in sps}
    for i_man in range(len(managers)):
        man = managers[i_man]
        counter = {sp: 0 for sp in sps}
        for i_at, at in enumerate(man):
            types.append(at.atom_type)
            if at.atom_type in sps:
                map_by_manager[at.atom_type][i_man][global_counter[at.atom_type]] = i_at
                counter[at.atom_type] += 1
                global_counter[at.atom_type] += 1
            else:
                raise ValueError(
                    "Atom type {} has not been specified in fselect: {}".format(
                        at.atom_type, sps
                    )
                )
        for sp in sps:
            strides_by_sp[sp].append(counter[sp])

    for sp in sps:
        strides_by_sp[sp] = np.cumsum(strides_by_sp[sp])

    for ii, sp in enumerate(types):
        indices_by_sp[sp].append(ii)

    return strides_by_sp, global_counter, map_by_manager, indices_by_sp


def get_index_mappings_sample(managers):
    """Get various info from the structures about the center atom species and indexing.

    Parameters
    ----------

    managers : AtomsList
        list of atomic structures

    Returns
    -------

    strides : list
        list the positions of the begining of each structure in arrays that
        have one row per atom
    global_counter : int
        count the number of atoms in managers
    map_by_manager : dict
        map the structure index / global atom index to the atom index in the
        structure
    """

    strides = [0]
    global_counter = 0
    map_by_manager = [{} for ii in range(len(managers))]
    for i_man in range(len(managers)):
        man = managers[i_man]
        counter = 0
        for i_at, _ in enumerate(man):
            map_by_manager[i_man][global_counter] = i_at
            counter += 1
            global_counter += 1
        strides.append(counter)

    strides = np.cumsum(strides)

    return strides, global_counter, map_by_manager


def convert_selected_global_index2perstructure_index_per_species(
    managers, selected_ids_by_sp, strides_by_sp, map_by_manager, sps
):
    """Convert selected center indexing into the rascal format.

    See get_index_mappings_sample_per_species to make the intput

    Parameters
    ----------

    managers : AtomsList
        list of atomic structures
    selected_ids_by_sp : dict
        map position in arrays that have one row per atom of species sp to
        the position in array that has one row per atom
    strides_by_sp : dict
        list the positions of the begining of each structure in arrays that
        have one row per atom of species sp
    map_by_manager : dict
        map species / structure index / global atom index to the atom index
        in the structure
    sps : list(int)
        list of unique center atom species present in managers

    Returns
    -------

    selected_ids : list of lists
        list the atom indices (within their structure) that have been selected
    """

    selected_ids = [[] for ii in range(len(managers))]
    for sp in sps:
        ids = convert_selected_global_index2perstructure_index(
            managers,
            selected_ids_by_sp[sp],
            strides_by_sp[sp],
            map_by_manager[sp],
        )
        for ii, selected_idx in zip(ids, selected_ids):
            selected_idx.extend(ii)
    for ii in range(len(selected_ids)):
        selected_ids[ii] = list(np.sort(selected_ids[ii]))
    return selected_ids


def convert_selected_global_index2perstructure_index(
    managers, selected_ids_global, strides, map_by_manager
):
    """Convert selected center indexing into the rascal format.

    See get_index_mappings_sample to make the intput

    Parameters
    ----------

    managers : AtomsList
        list of atomic structures
    selected_ids_global : list of int
        list of unique center atom species present in managers
    strides : list
        list the positions of the begining of each structure in arrays that
        have one row per atom
    map_by_manager : dict
        map the structure index / global atom index to the atom index in the
        structure

    Returns
    -------

    selected_ids : list of lists
        list the atom indices (within their structure) that have been selected
    """

    selected_ids = [[] for ii in range(len(managers))]
    i_manager = 0
    for idx in selected_ids_global:
        carry_on = True
        while carry_on:
            if idx >= strides[i_manager] and idx < strides[i_manager + 1]:
                selected_ids[i_manager].append(map_by_manager[i_manager][idx])
                carry_on = False
            else:
                i_manager += 1
    for ii in range(len(selected_ids)):
        selected_ids[ii] = list(np.sort(selected_ids[ii]).astype(int))
    return selected_ids


class Filter(BaseIO):
    """
    A super class for filtering representations based upon a standard
    sample or feature selection class.

    This is mainly a wrapper around selectors (implemented e.g. in
    scikit-cosmo) that handles the semantic-index transformations
    required after selection.

    Parameters
    ----------

    representation : Calculator
        Representation calculator associated with the kernel

    Nselect: int
        number of points to select. If act_on='sample per species' then it should
        be a dictionary mapping atom type to the number of samples, e.g.
        Nselect = {1:200,6:100,8:50}.

    selector: selector to use for filtering. The selector should
            have a `fit` function, which when called will select from the input
            matrix the desired features / samples and a `get_support` function
            which takes parameters `indices` and `ordered`, and returns a list
            of selection indices, in the order that they were selected,
            when `indices=True` and `ordered=True`.

    act_on: string
        Select how to apply the selection. Can be either of 'sample',
        'sample per species','feature'.  Default 'sample per species'.
        Note that for 'feature' mode only the SphericalInvariants
        representation is supported.

    """

    def __init__(
        self,
        representation,
        Nselect,
        selector,
        act_on="sample per species",
    ):
        self._representation = representation
        self.Nselect = Nselect

        if self.act_on is None:
            self._check_set_mode(act_on)

        # effectively selected list of indices at the filter step
        # the indices have been reordered for effiency and compatibility with
        # the c++ routines
        self.selected_ids = None
        # for 'sample' selection
        self.selected_sample_ids = None
        # for 'sample per species' selection
        self.selected_sample_ids_by_sp = None
        # for feature selection
        self.selected_feature_ids_global = None

        self._selector = selector

    def _check_set_mode(
        self, act_on, modes=["sample", "sample per species", "feature"]
    ):
        """Check that the supplied act_on is one of the supported modes

        Set the mode if it is valid, aise a ValueError with a helpful
        message otherwise

        A list of valid modes can be supplied in case it differs from the
        superclass default.
        """
        if act_on in modes:
            self.act_on = act_on
        else:
            valid_modes = ['"{}"'.format(mode) for mode in modes]
            if len(valid_modes) > 1:
                valid_modes[-1] = "or " + valid_modes[-1]
            valid_modes_str = ", ".join(valid_modes)
            raise ValueError('"act_on" should be one of: ' + valid_modes_str)

    def select(self, managers):
        """Perform selection of samples/features.

        Parameters
        ----------
        managers : AtomsList
            list of structures containing features computed with representation

        Returns
        -------
        Filter (self)
            Returns self; use `filter()` to perform the actual filtering
            operation

        """

        # get the dense feature matrix
        X = managers.get_features(self._representation)

        if self.act_on == "sample per species":
            sps = list(self.Nselect.keys())

            # get various info from the structures about the center atom species and indexing
            (
                strides_by_sp,
                global_counter,
                map_by_manager,
                indices_by_sp,
            ) = get_index_mappings_sample_per_species(managers, sps)

            LOGGER.info(
                f"The number of pseudo points selected by central atom species is: {self.Nselect}"
            )

            # organize features w.r.t. central atom type
            X_by_sp = {}
            for sp in sps:
                X_by_sp[sp] = X[indices_by_sp[sp]]
            self._XX = X_by_sp

            # split the dense feature matrix by center species and apply CUR decomposition
            self.selected_sample_ids_by_sp = {}

            for sp in sps:
                LOGGER.info(f"Selecting species: {sp}")
                if self._selector[sp] is not None:
                    self._selector[sp].fit(X_by_sp[sp])

                    in_sample_indices = np.array(
                        self._selector[sp].get_support(indices=True, ordered=True),
                        dtype=int,
                    )
                    self.selected_sample_ids_by_sp[sp] = in_sample_indices
                else:
                    self.selected_sample_ids_by_sp[sp] = []

            return self

        else:
            self._selector.fit(X)

            if self.act_on == "sample":
                self.selected_sample_ids = self._selector.get_support(
                    indices=True, ordered=True
                )
            else:
                self.selected_feature_ids_global = self._selector.get_support(
                    indices=True, ordered=True
                )

            return self

    def filter(self, managers, n_select=None):
        """Apply the fitted selection to a new set of managers

        Parameters
        ----------
        managers : AtomsList
            list of structures containing features computed with representation

        n_select : int
            number of selections to return, must be less than self.Nselect

        Returns
        -------
        SparsePoints or list(int) or dict
            Selected samples.  The format depends on self.act_on - if it is
            "sample" or "sample per species", then a SparsePoints instance
            is directly returned.  If it is "feature", then it is a dictionary
            containing the "coefficient_subselection" key that can be directly
            passed to the SphericalInvariants constructor.

        Warnings
        --------
        Note that the selected points are sorted in order of selection,
        _except_ if self.act_on=="sample", in which case the sparse points
        are afterwards sorted by species.

        Raises
        ------
        ValueError
            if requesting more selected samples or features than were used
            to initialize the representation

        """

        if n_select is None:
            n_select = self.Nselect

        else:
            if n_select > self.Nselect:
                raise ValueError(
                    f"It is only possible to filter {self.Nselect} {self.act_on}(s), "
                    f"you have requested {n_select}"
                )

        if self.act_on == "sample per species":
            sps = list(n_select.keys())
            # get various info from the structures about the center atom species and indexing
            (
                strides_by_sp,
                global_counter,
                map_by_manager,
                indices_by_sp,
            ) = get_index_mappings_sample_per_species(managers, sps)
            selected_ids_by_sp = {
                key: np.sort(val[: n_select[key]])
                for key, val in self.selected_sample_ids_by_sp.items()
            }
            self.selected_ids = (
                convert_selected_global_index2perstructure_index_per_species(
                    managers,
                    selected_ids_by_sp,
                    strides_by_sp,
                    map_by_manager,
                    sps,
                )
            )
            # return self.selected_ids
            # build the pseudo points
            pseudo_points = SparsePoints(self._representation)
            pseudo_points.extend(managers, self.selected_ids)
            return pseudo_points

        elif self.act_on == "sample":

            selected_ids_global = np.sort(self.selected_sample_ids[:n_select])
            strides, _, map_by_manager = get_index_mappings_sample(managers)
            self.selected_ids = convert_selected_global_index2perstructure_index(
                managers, selected_ids_global, strides, map_by_manager
            )
            # The sparse points will be reordered since they're not per-species
            # but the resulting object is still usable
            sparse_points = SparsePoints(self._representation)
            sparse_points.extend(managers, self.selected_ids)
            return sparse_points

        elif self.act_on == "feature":
            feat_idx2coeff_idx = self._representation.get_feature_index_mapping(
                managers
            )
            self.selected_ids = {key: [] for key in feat_idx2coeff_idx[0].keys()}
            selected_ids_sorting = np.argsort(
                self.selected_feature_ids_global[:n_select]
            )
            selected_feature_ids = self.selected_feature_ids_global[
                selected_ids_sorting
            ]
            for idx in selected_feature_ids:
                coef_idx = feat_idx2coeff_idx[idx]
                for key in self.selected_ids.keys():
                    self.selected_ids[key].append(int(coef_idx[key]))
            # keep the global indices and ordering for ease of use
            self.selected_ids[
                "selected_feature_ids_global"
            ] = selected_feature_ids.tolist()
            self.selected_ids[
                "selected_feature_ids_global_selection_ordering"
            ] = selected_ids_sorting.tolist()
            self.selected_ids = dict(coefficient_subselection=self.selected_ids)
            return self.selected_ids

    def select_and_filter(self, managers):
        return self.select(managers).filter(managers)

    def _get_data(self):
        return dict(
            selected_ids=self.selected_ids,
            selected_sample_ids=self.selected_sample_ids,
            selected_sample_ids_by_sp=self.selected_sample_ids_by_sp,
            selected_feature_ids_global=self.selected_feature_ids_global,
        )

    def _set_data(self, data):
        self.selected_ids = data["selected_ids"]
        self.selected_sample_ids = data["selected_sample_ids"]
        self.selected_sample_ids_by_sp = data["selected_sample_ids_by_sp"]
        self.selected_feature_ids_global = data["selected_feature_ids_global"]

    def _get_init_params(self):
        return dict(
            representation=self._representation,
            Nselect=self.Nselect,
            act_on=self.act_on,
        )


class CURFilter(Filter):
    def __init__(
        self,
        representation,
        Nselect,
        act_on="sample per species",
        selector_args={},
        **kwargs,
    ):
        modes = ["sample", "sample per species", "feature"]
        self._check_set_mode(act_on, modes)
        if act_on == "sample":
            selector = _CUR(
                selection_type="sample", n_to_select=Nselect, **selector_args
            )
        elif act_on == "sample per species":
            selector = {
                n: _CUR(
                    selection_type="sample", n_to_select=Nselect[n], **selector_args
                )
                if Nselect[n] > 0
                else None
                for n in Nselect
            }

        else:
            assert act_on == "feature"
            selector = _CUR(
                selection_type="feature", n_to_select=Nselect, **selector_args
            )

        super().__init__(
            representation=representation,
            Nselect=Nselect,
            act_on=act_on,
            selector=selector,
            **kwargs,
        )


class FPSFilter(Filter):
    def __init__(
        self,
        representation,
        Nselect,
        act_on="sample per species",
        selector_args={},
        **kwargs,
    ):
        modes = ["sample", "sample per species", "feature"]
        self._check_set_mode(act_on, modes)
        if act_on == "sample":
            selector = _FPS(
                selection_type="sample", n_to_select=Nselect, **selector_args
            )
        elif act_on == "sample per species":
            selector = {
                n: _FPS(
                    selection_type="sample", n_to_select=Nselect[n], **selector_args
                )
                if Nselect[n] > 0
                else None
                for n in Nselect
            }

        else:
            assert act_on == "feature"
            selector = _FPS(
                selection_type="feature", n_to_select=Nselect, **selector_args
            )

        super().__init__(
            representation=representation,
            Nselect=Nselect,
            act_on=act_on,
            selector=selector,
            **kwargs,
        )

    def get_fps_distances(self):
        """Return the Hausdorff distances over the course of selection

        This may be a useful (rough) indicator for choosing how many points to
        select, as a small distance generally indicates that the selected point
        is close to the existing set of selected points and therefore probably
        does not add much additional information.

        Returns either an array of Hausdorff distances, or a species-indexed
        dict of arrays (for the "sample per species" mode).
        """
        if self.act_on == "sample per species":
            return {
                sp: self._selector[sp].get_select_distance() for sp in self._selector
            }
        else:
            return self._selector.get_select_distance()