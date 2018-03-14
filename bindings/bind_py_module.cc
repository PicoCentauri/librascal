/**
 * @file   bind_py_module.cc
 *
 * @author Federico Giberti <federico.giberti@epfl.ch>
 *
 * @date   14 Mar 2018
 *
 * @brief  Main binding file for Proteus
 *
 * Copyright © 2017 Felix Musil
 *
 * Proteus is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation, either version 3, or (at
 * your option) any later version.
 *
 * Proteus is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with GNU Emacs; see the file COPYING. If not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */



#include <pybind11/pybind11.h>

using namespace pybind11::literals;
namespace py=pybind11;

extern void prot_dist_mat(py::module&);

PYBIND11_MODULE(_proteus, mod) {
  mod.doc() = "Hello, World!";
  // py::add_ostream_redirect(m, "ostream_redirect");
  prot_dist_mat(mod);
}
