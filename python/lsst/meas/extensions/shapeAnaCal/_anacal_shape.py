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

__all__ = (
    "AnaCalFpfsConfig",
    "AnaCalFpfsPlugin",
)

import lsst.geom as geom
import lsst.meas.base as measBase
import numpy as np
from anacal.fpfs import FpfsMeasure
from lsst.pex.config import Field, FieldValidationError, ListField

from ._utils import make_anacal_peaks, resize_array


class AnaCalFpfsConfig(measBase.SingleFramePluginConfig):
    n_order = Field[int](
        doc="The maximum radial number of shapelets used in anacal.fpfs",
        default=4,
    )
    sigma_arcsec = Field[float](
        doc="Shapelet's Gaussian kernel size",
        default=0.52,
    )

    badMaskPlanes = ListField[str](
        doc="Mask planes used to reject bad pixels.",
        default=["BAD", "SAT"],
    )

    measureFromNoise = Field[bool](
        doc="Measure from pure noise for noise bias correction?",
        default=False,
    )

    def validate(self):
        if self.n_order not in [4, 6]:
            raise FieldValidationError(
                self.__class__.n_order, self, "we only support n = 4 or 6"
            )
        super().validate()


class AnaCalFpfsPlugin(measBase.SingleFramePlugin):
    """Base plugin for higher moments measurement"""

    ConfigClass = AnaCalFpfsConfig

    def __init__(self, config, name, schema, metadata, logName=None):
        super().__init__(config, name, schema, metadata, logName=logName)

        # Define flags for possible issues that might arise during measurement.
        # TODO: Understand what is this?
        flagDefs = measBase.FlagDefinitionList()
        self.FAILURE = flagDefs.addFailureFlag(
            "General failure flag, set if anything went wrong"
        )

        # Embed the flag definitions in the schema using a flag handler.
        self.flagHandler = measBase.FlagHandler.addFields(schema, name, flagDefs)
        # TODO: I should be able to get these two values from somewhere..
        pixel_scale = 0.2
        mag_zero = 30.0
        self.fpfs_task = FpfsMeasure(
            kmax=3.05,  # TODO: Use PSF image to determine a truncation scale
            pixel_scale=pixel_scale,
            sigma_arcsec=self.config.sigma_arcsec,
            klim_thres=self.config.klim_thres,
            nord=self.config.n_order,
            det_nrot=-1,
            mag_zero=mag_zero,
        )

        # TODO: Understand where is name defined
        for suffix in self.fpfs_task.colnames():
            schema.addField(
                schema.join(name, f"source_{suffix}"),
                type=float,
                doc=f"AnaCal FPFS source {suffix} for source",
            )

        if self.config.measureFromNoise:
            for suffix in self.fpfs_task.colnames():
                schema.addField(
                    schema.join(name, f"noise_{suffix}"),
                    type=float,
                    doc=f"AnaCal FPFS noise {suffix} for source",
                )

    @classmethod
    def getExecutionOrder(cls):
        # TODO: Understand what is this??
        return cls.FLUX_ORDER

    def fail(self, record, error=None):
        # Docstring inherited.
        self.flagHandler.handleFailure(record)

    def measure(self, record, exposure):
        # Docstring inherited.

        # TODO: need to create detection task for anacal and use that peak
        # positions
        x_center = (record["deblend_peak_center_x"],)
        y_center = (record["deblend_peak_center_y"],)
        coords = make_anacal_peaks(
            x_center=x_center,
            y_center=y_center,
        )

        bitValue = exposure.mask.getPlaneBitMask(self.config.badMaskPlanes)
        # TODO: need to include mask_array in the future
        mask_array = ((exposure.mask.array & bitValue) != 0).astype(int)
        psf_array = exposure.getPsf().computeImage(geom.Point2D(x_center, y_center)).array
        psf_array = resize_array(psf_array)
        gal_array = exposure.image.array

        # measurement from double noised image (src)
        # and pure noise image (nrc)
        src, nrc = self.fpfs_task.run(
            gal_array=gal_array,
            det=coords,
            noise_array=None,  # TODO: set to None now, but need to be added
        )

        # Record the moments
        for cname in self.fpfs_task.colnames:
            index = self.fpfs_task.di[cname]
            column_key = self.name + f"source_{cname}"
            record.set(column_key, src[0][index])

        if nrc is not None:
            for cname in self.fpfs_task.colnames:
                index = self.fpfs_task.di[cname]
                column_key = self.name + f"noise_{cname}"
                record.set(column_key, src[0][index])
