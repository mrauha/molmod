 # PyChem is a general chemistry oriented python package.
# Copyright (C) 2005 Toon Verstraelen
# 
# This file is part of PyChem.
# 
# PyChem is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 
# --

from pychem.interfaces.g98.file_parsers import *
from pychem.interfaces.output_parsers import OutputParser


import math, Numeric, LinearAlgebra
import unittest


__all__ = ["G98Interface"]


class G98Interface(unittest.TestCase):
    def test_parser(self):
        output_parser = OutputParser([
            HessianParser(),
            MassParser(),
            CoordinatesParser(),
            EnergyParser(),
            LowFrequenciesParser(),
            SelectedFrequenciesParser(),
        ])

        result = output_parser.parse("input", "g98_1")

        expected_keys = ['energies', 'masses', 'coordinates', 'low_frequencies', 'selected_frequencies', 'hessian']
        for expected_key in expected_keys:
            self.assert_(expected_key in result)

        #print "hessian:", result["hessian"]
        #print "masses:", result["masses"]
        #print "coordinates:", result["coordinates"]
        #print "energies:", result["energies"]
        #print "low frequencies:", result["low_frequencies"]
        #print "selected frequencies:", result["selected_frequencies"]
        