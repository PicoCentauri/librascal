/**
 * @file   behler_fixtures.hh
 *
 * @author Till Junge <till.junge@epfl.ch>
 *
 * @date   18 Dec 2019
 *
 * @brief  common fixtures for testing Behler-Parrinello descriptors
 *
 * Copyright © 2019 Till Junge
 *
 * rascal is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation, either version 3, or (at
 * your option) any later version.
 *
 * rascal is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with rascal; see the file COPYING. If not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 *
 */

#ifndef TESTS_BEHLER_FIXTURES_HH_
#define TESTS_BEHLER_FIXTURES_HH_

#include "rascal/representations/cutoff_functions_inlineable.hh"
#include "rascal/representations/symmetry_functions.hh"

#include <Eigen/Dense>

#include <iostream>

namespace rascal {

  template <InlCutoffFunctionType FunType>
  struct InlCutoffFunFixture {};

  template <>
  struct InlCutoffFunFixture<InlCutoffFunctionType::Cosine> {
    using CutoffFun = CutoffFunction<InlCutoffFunctionType::Cosine>;
    InlCutoffFunFixture() : cut_fun{unit_style, correct_input} {}
    const units::UnitStyle unit_style{units::metal};

    const double r_cut{1.1};
    CutoffFunctionBase::Hypers_t correct_input{
        {"params", {}}, {"r_cut", {{"value", r_cut}, {"unit", "Å"}}}};

    CutoffFunctionBase::Hypers_t incorrect_put{
        {"params", {}}, {"r_cut", {{"value", r_cut}, {"unit", "J"}}}};
    CutoffFun cut_fun;
  };

  template <SymmetryFunctionType FunType>
  struct SymmetryFunFixture {};

  /* ---------------------------------------------------------------------- */
  /**
   * Fixture for the Behler type Gaussian radial symmetry function
   */
  template <>
  struct SymmetryFunFixture<SymmetryFunctionType::Gaussian> {
    using SymFun = SymmetryFunction<SymmetryFunctionType::Gaussian>;
    SymmetryFunFixture()
        : sym_fun{unit_style, correct_input, units::default_species_numbers} {}
    const units::UnitStyle unit_style{units::metal};

    const double r_ij{1.1};
    json correct_input{{"eta", {{"value", .1}, {"unit", "(Å)^(-2)"}}},
                       {"r_s", {{"value", 5.6}, {"unit", "Å"}}},
                       {"species", {"Mg", "Si"}}};

    json incorrect_put{{"eta", {{"value", .1}, {"unit", "(Å)^(-1)"}}},
                       {"r_s", {{"value", 5.6}, {"unit", "Å"}}},
                       {"species", {"Mg", "Si"}}};
    SymFun sym_fun;
  };

  /* ---------------------------------------------------------------------- */
  /**
   * Fixture for the Behler type narrow (all atoms in a triplet within each
   * others cutoff) angular symmetry function
   */
  template <>
  struct SymmetryFunFixture<SymmetryFunctionType::AngularNarrow> {
    using SymFun = SymmetryFunction<SymmetryFunctionType::AngularNarrow>;
    SymmetryFunFixture()
        : sym_fun{unit_style, correct_input, units::default_species_numbers} {
      this->cos_theta << cos(2.96706), .5, 1;  // ~170°
      this->dists << 1.1, 1.2, 1.3;
      this->cutoffs << .1, .2, .3;
      this->cutoff_derivatives << -.1, -.2, -.3;
    }
    const units::UnitStyle unit_style{units::metal};

    Eigen::Vector3d cos_theta{};
    Eigen::Vector3d dists{};
    Eigen::Vector3d cutoffs{};
    Eigen::Vector3d cutoff_derivatives{};

    json correct_input{{"zeta", {{"value", .1}, {"unit", "-"}}},
                       {"lambda", {{"value", .1}, {"unit", "-"}}},
                       {"eta", {{"value", .1}, {"unit", "(Å)^(-2)"}}},
                       {"species", {"Mg", "Si", "Si"}}};

    json incorrect_put{{"zeta", {{"value", .1}, {"unit", "-"}}},
                       {"lambda", {{"value", .1}, {"unit", "-"}}},
                       {"eta", {{"value", .1}, {"unit", "(Å)^(-1)"}}},
                       {"species", {"Mg", "Si", "Si"}}};
    SymFun sym_fun;
  };

  /* ---------------------------------------------------------------------- */
  /**
   * Fixture for the Behler type narrow (all atoms in a triplet within each
   * others cutoff) angular symmetry function
   */
  template <>
  struct SymmetryFunFixture<SymmetryFunctionType::AngularWide> {
    using SymFun = SymmetryFunction<SymmetryFunctionType::AngularWide>;
    SymmetryFunFixture()
        : sym_fun{unit_style, correct_input, units::default_species_numbers} {
      this->cos_theta << cos(2.96706), .5, 1;  // ~170°
      this->dists << 1.1, 1.2, 1.3;
      this->cutoffs << .1, .2, .3;
      this->cutoff_derivatives << -.1, -.2, -.3;
    }
    const units::UnitStyle unit_style{units::metal};

    Eigen::Vector3d cos_theta{};
    Eigen::Vector3d dists{};
    Eigen::Vector3d cutoffs{};
    Eigen::Vector3d cutoff_derivatives{};

    json correct_input{{"zeta", {{"value", .1}, {"unit", "-"}}},
                       {"lambda", {{"value", .1}, {"unit", "-"}}},
                       {"eta", {{"value", .1}, {"unit", "(Å)^(-2)"}}},
                       {"species", {"Mg", "Si", "Si"}}};

    json incorrect_put{{"zeta", {{"value", .1}, {"unit", "-"}}},
                       {"lambda", {{"value", .1}, {"unit", "-"}}},
                       {"eta", {{"value", .1}, {"unit", "(Å)^(-1)"}}},
                       {"species", {"Mg", "Si", "Si"}}};
    SymFun sym_fun;
  };

}  // namespace rascal

#endif  // TESTS_BEHLER_FIXTURES_HH_
