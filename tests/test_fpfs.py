# This file is part of meas_extensions_shapeAnaCal.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Unit tests for higher order moments measurement.

These double up as initial estimates of how accurate the measurement is with
different configuration options. The various tolerance levels here are based
on experimentation with the specific datasets used here.
"""

import unittest

import lsst.afw.geom
import lsst.meas.base.tests
import lsst.meas.extensions.shapeAnaCal  # noqa: F401
import lsst.utils.tests as tests
from lsst.meas.base import SingleFrameMeasurementConfig, SingleFrameMeasurementTask
from lsst.pex.config import FieldValidationError


class FpfsBaseTestCase(tests.TestCase):
    """Base test case to test higher order moments."""

    def setUp(self):
        """Create an exposure and run measurement on the source and the PSF"""
        super().setUp()

        # Initialize a config and activate the plugin
        sfmConfig = SingleFrameMeasurementConfig()
        sfmConfig.plugins.names |= [
            "ext_shapeAnaCal_Fpfs",
        ]
        # The min and max order determine the schema and cannot be changed
        # after the Task is created. So we set it generously here.
        sfmConfig.plugins["ext_shapeAnaCal_Fpfs"].n_order = 4

        # Create a minimal schema (columns)
        self.schema = lsst.meas.base.tests.TestDataset.makeMinimalSchema()

        # Create a task
        sfmTask = SingleFrameMeasurementTask(config=sfmConfig, schema=self.schema)

        dataset = self.create_dataset()

        # Get the exposure and catalog.
        exposure, catalog = dataset.realize(0.0, sfmTask.schema, randomSeed=0)

        self.catalog = catalog
        self.exposure = exposure
        self.task = sfmTask

        self.add_mask_bits()

    @staticmethod
    def add_mask_bits():
        """Add mask bits to the exposure.

        This must go along with the create_dataset method. This is a no-op for
        the base class and subclasses must set mask bits depending on the test.
        """
        pass

    @staticmethod
    def create_dataset():
        # Create a simple, fake dataset
        bbox = lsst.geom.Box2I(lsst.geom.Point2I(0, 0), lsst.geom.Extent2I(100, 100))
        dataset = lsst.meas.base.tests.TestDataset(bbox)
        # Create a point source with Gaussian PSF
        dataset.addSource(100000.0, lsst.geom.Point2D(49.5, 49.5))

        # Create a galaxy with Gaussian PSF
        dataset.addSource(
            300000.0,
            lsst.geom.Point2D(76.3, 79.2),
            lsst.afw.geom.Quadrupole(2.0, 3.0, 0.5),
        )
        return dataset

    def run_measurement(self, **kwargs):
        """Run measurement on the source and the PSF"""
        self.task.run(self.catalog, self.exposure, **kwargs)

    def check(self, row, plugin_name, atol):
        M_source_40 = row[f"{plugin_name}_40"]
        self.assertFloatsAlmostEqual(M_source_40, 0.75, atol=atol)

    @lsst.utils.tests.methodParameters(plugin_name=("ext_shapeAnaCal_Fpfs",))
    def test_validate_config(self, plugin_name):
        """Test that the validation of the configs works as expected."""
        config = self.task.config.plugins[plugin_name]
        config.validate()  # This should not raise any error.

        # Test that the validation fails when the max_order is smaller than the
        # min_order.
        config.n_order = 9
        with self.assertRaises(FieldValidationError):
            config.validate()

    @lsst.utils.tests.methodParameters(plugin_name=("ext_shapeAnaCal_Fpfs",))
    def test_fpfs_shear_estimate(self, plugin_name):
        """Test shear estimation"""
        self.assertFloatsAlmostEqual(1, 1, atol=1e-7)


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
