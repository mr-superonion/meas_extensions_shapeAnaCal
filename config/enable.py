# Enable AnaCal measurements
#
# The 'config' should be a SourceMeasurementConfig.
#
# We activate the REGAUSS PSF-corrected shape measurement, the adaptive moments of the source and PSF and the
# higher-order moments measurements of the same.

import lsst.meas.extensions.shapeAnaCal

config.plugins.names |= [
    "ext_shapeAnaCal_Fpfs",
]
config.slots.shape = "ext_shapeAnaCal_Fpfs"
