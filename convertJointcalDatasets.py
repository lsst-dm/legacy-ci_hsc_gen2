# This file contains overrides for obs.base.gen2to3.ConvertRepoTask to export
# the jointcal_* datasets that are in the root of the Gen2 repo into a special
# "HSC/external" RUN collection, since it doesn't make sense to put them any of
# the other RUNs generated from that conversion.  This doesn't go in the
# obs_subaru config overrides because having those datasets in the root is
# unique to ci_hsc_gen2.

from lsst.obs.subaru import HyperSuprimeCam

collection = HyperSuprimeCam().makeCollectionName("external")
config.runs["jointcal_wcs"] = collection
config.runs["jointcal_photoCalib"] = collection
