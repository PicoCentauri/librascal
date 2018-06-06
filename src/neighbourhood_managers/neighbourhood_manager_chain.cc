/**
 * file   neighbourhood_manager_chain.cc
 *
 * @author Markus Stricker <markus.stricker@epfl.ch>
 *
 * @date   30 May 2018
 *
 * @brief Implementation of the neighbourhood manager for polyalanine
 *        chain from json file
 *
 * Copyright © 2018 Markus Stricker, COSMO (EPFL), LAMMM (EPFL)
 *
 * rascal is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation, either version 3, or (at
 * your option) any later version.
 *
 * rascal is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with GNU Emacs; see the file COPYING. If not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include "neighbourhood_managers/neighbourhood_manager_chain.hh"

#include <numeric>
#include <fstream>
#include <iostream>




namespace rascal {

  //using json = nlohmann::json;

  /* ---------------------------------------------------------------------- */
  void NeighbourhoodManagerChain::update() {
    // Make map to Eigen types
    this->position = this->molecule_in.position;
    this->type = this->molecule_in.type;
    this->cell = this->molecule_in.cell;
    this->pbc = this->molecule_in.pbc;
    // this->natoms = t

    std::cout << "update function dummy" << std::endl;
  }


  /* ---------------------------------------------------------------------- */
  size_t NeighbourhoodManagerChain::get_nb_clusters(int cluster_size)  {
    switch (cluster_size) {
    case 1: {
      return natoms;
      break;
    }
    default:
      throw std::runtime_error("Can only handle single atoms; "
                               " use adaptor to increase MaxLevel.");
      break;
    }
  }

  /* ---------------------------------------------------------------------- */
  void NeighbourhoodManagerChain::
  read_structure_from_json(const std::string filename) {
    std::ifstream i(filename);
    json input_dataset;
    i >> input_dataset;

    // ASE json format is nested - first entry is actual molecule
    this->molecule_in = input_dataset.begin().value();
  }



}  // rascal
