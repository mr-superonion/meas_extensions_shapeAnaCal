``meas_extensions_shapeAnaCal`` is a package in the 
[LSST Science Pipelines](https://pipelines.lsst.io) . 

The ``lsst.meas.extensions.shapeAnaCal`` Python module provides algorithms for
AnaCal shape measurement and shear response calculation.

The AnaCal framework is introduced in 
[ref1](https://ui.adsabs.harvard.edu/abs/2023MNRAS.521.4904L/abstract).

The framework is devised to measure the responses for shape estimators that 
have been developed or are anticipated to be created in the future. We intend to
develop a suite of analytical shear estimators capable of inferring shear with
subpercent accuracy, all while maintaining minimal computational time. The
currently supported analytic shear estimators are:
+ [FPFS](https://github.com/mr-superonion/FPFS): A fixed moments method based
  on shapelets including analytic correction for selection, detection and noise
  bias. (see [ref1](https://ui.adsabs.harvard.edu/abs/2018MNRAS.481.4445L/abstract),
  [ref2](https://ui.adsabs.harvard.edu/abs/2021arXiv211001214L/abstract) and
  [ref3](https://ui.adsabs.harvard.edu/abs/2022arXiv220810522L/abstract).)
