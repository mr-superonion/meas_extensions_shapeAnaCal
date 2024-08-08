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
import lsst.afw.table as afwTable
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

        self.peakCenter = afwTable.Point2IKey.addFields(
            self.schema,
            name="anacal_peak_center",
            doc="Center used to apply constraints in scarlet",
            unit="pixel",
        )

        # Create a task
        sfmTask = SingleFrameMeasurementTask(config=sfmConfig, schema=self.schema)

        self.create_dataset(sfmTask.schema)
        self.task = sfmTask

    def add_mask_bits(self):
        """Add mask bits to the exposure.

        This must go along with the create_dataset method. This is a no-op for
        the base class and subclasses must set mask bits depending on the test.
        """
        pass

    def create_dataset(self, schema):
        # Create a simple, fake dataset
        bbox = lsst.geom.Box2I(lsst.geom.Point2I(0, 0), lsst.geom.Extent2I(100, 100))
        dataset = lsst.meas.base.tests.TestDataset(bbox)
        # Create a galaxy with Gaussian PSF
        dataset.addSource(
            300000.0,
            lsst.geom.Point2D(50, 50),
            lsst.afw.geom.Quadrupole(ixx=2.0, iyy=2.0, ixy=0.5),
        )
        # Get the exposure and catalog.
        exposure, catalog = dataset.realize(0.0, schema, randomSeed=0)
        catalog[0].set("anacal_peak_center_x", 50)
        catalog[0].set("anacal_peak_center_y", 50)

        self.exposure = exposure
        self.catalog = catalog
        self.add_mask_bits()
        return dataset

    def run_measurement(self, **kwargs):
        """Run measurement on the source and the PSF"""
        self.task.run(self.catalog, self.exposure, **kwargs)

    @lsst.utils.tests.methodParameters(plugin_name=("ext_shapeAnaCal_Fpfs",))
    def test_validate_config(self, plugin_name):
        """Test that the validation of the configs works as expected."""
        config = self.task.config.plugins[plugin_name]
        config.validate()  # This should not raise any error.

        # Test that the validation fails when the n_order is not 4 or 6
        config.n_order = 7
        with self.assertRaises(FieldValidationError):
            config.validate()

        config.n_order = 3
        with self.assertRaises(FieldValidationError):
            config.validate()

    @lsst.utils.tests.methodParameters(plugin_name=("ext_shapeAnaCal_Fpfs",))
    def test_fpfs_shear_estimate(self, plugin_name):
        """Test shear estimation"""
        self.run_measurement()
        row = self.catalog[0]
        m22c = row[f"{plugin_name}_source_m22c"]
        m22s = row[f"{plugin_name}_source_m22s"]
        m00 = row[f"{plugin_name}_source_m00"]
        m40 = row[f"{plugin_name}_source_m40"]

        g1_estimate = m22c / (m00 - m40)
        g2_estimate = m22s / (m00 - m40)
        assert g2_estimate > 0.0
        self.assertFloatsAlmostEqual(g1_estimate, 0.0, atol=1e-7)


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
