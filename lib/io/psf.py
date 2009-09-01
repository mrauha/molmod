# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 - 2008 Toon Verstraelen <Toon.Verstraelen@UGent.be>
#
# This file is part of MolMod.
#
# MolMod is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# MolMod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --


import numpy
from molmod.data.periodic import periodic
from molmod.units import unified
from molmod.graphs import CriteriaSet, GraphSearch
from molmod.molecular_graphs import MolecularGraph, BondPattern, \
    BendingAnglePattern, DihedralAnglePattern
from molmod.graphs import Graph
from molmod.io.common import FileFormatError


__all__ = ["PSFFile"]


class PSFFile(object):
    "A very simplistic and limited implementation of the PSF file format"

    def __init__(self, filename=None):
        """Initialize a PSF file

           Argument:
             filename  --  When not given, an empty data structure is created,
                           otherwise the file is loaded from disk
        """
        if filename is None:
            self.clear()
        else:
            self.read_from_file(filename)

    def clear(self):
        """Clear the contents of the data structure"""
        self.title = None
        self.numbers = numpy.zeros(0,int)
        self.atom_types = [] # the atom_types in the second column, used to associate ff parameters
        self.charges = [] # ff charges
        self.names = [] # a name that is unique for the molecule composition and connectivity
        self.molecules = numpy.zeros(0,int) # a counter for each molecule
        self.bonds = numpy.zeros((0,2),int)
        self.bends = numpy.zeros((0,3),int)
        self.dihedrals = numpy.zeros((0,4),int)

        self.name_cache = {}

    def read_from_file(self, filename):
        """Load a PSF file"""
        self.clear()
        f = file(filename)
        # A) check the first line
        line = f.next()
        if not line.startswith("PSF"):
            raise FileFormatError("Error while reading: A PSF file must start with a line 'PSF'.")
        # B) read in all the sections, without interpreting them
        current_section = None
        sections = {}
        for line in f:
            line = line.strip()
            if line == "":
                continue
            elif "!N" in line:
                words = line.split()
                current_section = []
                section_name = words[1][2:]
                if section_name.endswith(":"):
                    section_name = section_name[:-1]
                sections[section_name] = current_section
            else:
                current_section.append(line)
        f.close()
        # C) interpret the supported sections
        # C.1) The title
        self.title = sections['TITLE'][0]
        molecules = []
        numbers = []
        # C.2) The atoms and molecules
        for line in sections['ATOM']:
            words = line.split()
            self.atom_types.append(words[5])
            self.charges.append(float(words[6]))
            self.names.append(words[3])
            molecules.append(int(words[2]))
            atom = periodic[words[4]]
            if atom is None:
                numbers.append(0)
            else:
                numbers.append(periodic[words[4]].number)
        self.molecules = numpy.array(molecules)-1
        self.numbers = numpy.array(numbers)
        self.charges = numpy.array(self.charges)
        # C.3) The bonds section
        tmp = []
        for line in sections['BOND']:
            tmp.extend(int(word) for word in line.split())
        self.bonds = numpy.reshape(numpy.array(tmp), (-1,2))-1
        # C.4) The bends section
        tmp = []
        for line in sections['THETA']:
            tmp.extend(int(word) for word in line.split())
        self.bends = numpy.reshape(numpy.array(tmp), (-1,3))-1
        # C.5) The dihedral section
        tmp = []
        for line in sections['PHI']:
            tmp.extend(int(word) for word in line.split())
        self.dihedrals = numpy.reshape(numpy.array(tmp), (-1,4))-1

    def _get_name(self, graph, group=None):
        if group is not None:
            graph = graph.get_subgraph(group, normalize=True)

        fingerprint = str(buffer(graph.fingerprint))
        name = self.name_cache.get(fingerprint)
        if name is None:
            name = "NM%02i" % len(self.name_cache)
            self.name_cache[fingerprint] = name
        return name

    def write_to_file(self, filename):
        """Write the data structure to a file"""
        f = file(filename, 'w')
        self.dump(f)
        f.close()

    def dump(self, f):
        """Dump the data structure to a file-like object"""
        # header
        print >> f, "PSF"
        print >> f

        # title
        print >> f, "      1 !NTITLE"
        print >> f, self.title
        print >> f

        # atoms
        print >> f, "% 7i !NATOM" % len(self.numbers)
        if len(self.numbers) > 0:
            for index, (number, atom_type, charge, name, molecule) in enumerate(zip(self.numbers,self.atom_types,self.charges,self.names,self.molecules)):
                atom = periodic[number]
                print >> f, "% 7i % 4s % 4i NAME % 6s % 6s % 8.4f % 12.6f 0" % (
                    index + 1,
                    name,
                    molecule + 1,
                    atom.symbol,
                    atom_type,
                    charge,
                    atom.mass/unified,
                )
        print >> f

        # bonds
        print >> f, "% 7i !NBOND" % len(self.bonds)
        if len(self.bonds) > 0:
            tmp = []
            for bond in self.bonds:
                tmp.extend(bond+1)
                if len(tmp) >= 8:
                    print >> f, " ".join("% 7i" % v for v in tmp[:8])
                    tmp = tmp[8:]
            if len(tmp) > 0:
                print >> f, " ".join("% 7i" % v for v in tmp)
        print >> f

        # bends
        print >> f, "% 7i !NTHETA" % len(self.bends)
        if len(self.bends) > 0:
            tmp = []
            for bend in self.bends:
                tmp.extend(bend+1)
                if len(tmp) >= 9:
                    print >> f, " " + (" ".join("% 6i" % v for v in tmp[:9]))
                    tmp = tmp[9:]
            if len(tmp) > 0:
                print >> f, " " + (" ".join("% 6i" % v for v in tmp))
        print >> f

        # dihedrals
        print >> f, "% 7i !NPHI" % len(self.dihedrals)
        if len(self.dihedrals) > 0:
            tmp = []
            for dihedral in self.dihedrals:
                tmp.extend(dihedral+1)
                if len(tmp) >= 8:
                    print >> f, " " + (" ".join("% 6i" % v for v in tmp[:8]))
                    tmp = tmp[8:]
            if len(tmp) > 0:
                print >> f, " " + (" ".join("% 6i" % v for v in tmp))
        print >> f

        # not implemented fields
        print >> f, "      0 !NIMPHI"
        print >> f
        print >> f, "      0 !NDON"
        print >> f
        print >> f, "      0 !NNB"
        print >> f
        print >> f, "      0 !NGRP"
        print >> f

    def add_molecule(self, molecule, atom_types=None, charges=None, split=True):
        """Add the graph of the molecule to the data structure

           The molecular graph is estimated from the molecular geometry based on
           interatomic distances.

           Arguments:
             molecule  --  a Molecule instance
             atom_types  --  a list with atom type strings (optional)
             charges  --  The net atom charges
             split  --  When True, the molecule is split into disconnected
                        molecules (default=True)
        """
        molecular_graph = MolecularGraph.from_geometry(molecule)
        self.add_molecular_graph(molecular_graph, atom_types, charges, split)

    def add_molecular_graph(self, molecular_graph, atom_types=None, charges=None, split=True):
        """Add the molecular graph to the data structure

           Arguments:
             molecule  --  a Molecule instance
             atom_types  --  a list with atom type strings (optional)
             charges  --  The net atom charges
             split  --  When True, the molecule is split into disconnected
                        molecules (default=True)
        """
        # add atom numbers and molecule indices
        new = len(molecular_graph.numbers)
        if new == 0: return
        prev = len(self.numbers)
        offset = prev
        self.numbers.resize(prev + new)
        self.numbers[-new:] = molecular_graph.numbers
        if atom_types is None:
            atom_types = [periodic[number].symbol for number in molecular_graph.numbers]
        self.atom_types.extend(atom_types)
        if charges is None:
            charges = [0.0]*len(molecular_graph.numbers)
        self.charges.extend(charges)
        self.molecules.resize(prev + new)
        # add names (autogenerated)
        if split:
            groups = molecular_graph.independent_nodes
            names = [self._get_name(molecular_graph, group) for group in groups]
            group_indices = numpy.zeros(new, int)
            for group_index, group in enumerate(groups):
                for index in group:
                    group_indices[index] = group_index
            self.names.extend([names[group_index] for group_index in group_indices])
            if prev == 0:
                self.molecules[:] = group_indices
            else:
                self.molecules[-new:] = self.molecules[-new]+group_indices+1
        else:
            if prev == 0:
                self.molecules[-new:] = 0
            else:
                self.molecules[-new:] = self.molecules[-new]+1
            name = self._get_name(molecular_graph)
            self.names.extend([name]*new)


        # add bonds
        match_generator = GraphSearch(BondPattern([CriteriaSet()]))
        tmp = [(
            match.get_destination(0),
            match.get_destination(1),
        ) for match in match_generator(molecular_graph)]
        tmp.sort()
        new = len(tmp)
        if new > 0:
            prev = len(self.bonds)
            self.bonds.resize((prev + len(tmp), 2))
            self.bonds[-len(tmp):] = tmp
            self.bonds[-len(tmp):] += offset

        # add bends
        match_generator = GraphSearch(BendingAnglePattern([CriteriaSet()]))
        tmp = [(
            match.get_destination(0),
            match.get_destination(1),
            match.get_destination(2),
        ) for match in match_generator(molecular_graph)]
        tmp.sort()
        new = len(tmp)
        if new > 0:
            prev = len(self.bends)
            self.bends.resize((prev + len(tmp), 3))
            self.bends[-len(tmp):] = tmp
            self.bends[-len(tmp):] += offset

        # add dihedrals
        match_generator = GraphSearch(DihedralAnglePattern([CriteriaSet()]))
        tmp = [(
            match.get_destination(0),
            match.get_destination(1),
            match.get_destination(2),
            match.get_destination(3),
        ) for match in match_generator(molecular_graph)]
        tmp.sort()
        new = len(tmp)
        if new > 0:
            prev = len(self.dihedrals)
            self.dihedrals.resize((prev + len(tmp), 4))
            self.dihedrals[-len(tmp):] = tmp
            self.dihedrals[-len(tmp):] += offset

    def get_graph(self):
        """Return the bond graph represented by the data structure"""
        return Graph(self.bonds)

    def get_molecular_graph(self):
        """Return the molecular graph represented by the data structure"""
        return MolecularGraph(self.bonds, self.numbers)

    def get_groups(self):
        """Return a list of groups of atom indexes

           Each atom in a group belongs to the same molecule or residue.
        """
        groups = []
        for a_index, m_index in enumerate(self.molecules):
            if m_index >= len(groups):
                groups.append([a_index])
            else:
                groups[m_index].append(a_index)
        return groups

