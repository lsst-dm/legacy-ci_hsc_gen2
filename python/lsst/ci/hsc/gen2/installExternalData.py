import os
import argparse
from lsst.daf.persistence import Butler


def linkFile(source, butler, datasetType, dataId):
    """Link a file in the butler to some source outside

    We use links to avoid copying files unnecessarily, and because the
    ci_hsc_gen3 ``exportExternalData`` script expects everything to live
    in testdata_ci_hsc still.

    Parameters
    ----------
    source : `str`
        Filename for source data.
    butler : `lsst.daf.peristence.Butler`
        Data butler.
    datasetType : `str`
        Dataset type in butler.
    dataId : `dict`
        Data identifiers.
    """
    target = butler.get(f"{datasetType}_filename", dataId)[0]
    dirName = os.path.dirname(target)
    if not os.path.isdir(dirName):
        os.makedirs(dirName)
    os.symlink(os.path.relpath(source, dirName), target)


def installJointcal(source, butler, tract, visitCcdList):
    """Install jointcal data

    The jointcal data is read from the nominated ``source``, and written using
    the butler.

    Parameters
    ----------
    source : `str`
        Path to the source jointcal data.
    butler : `lsst.daf.persistence.Butler`
        Data butler.
    tract : `int`
        Tract identifier.
    visitCcdList : iterable of pair of `int`
        List of ``visit``, ``ccd`` pairs.
    """
    for visit, ccd in visitCcdList:
        suffix = f"{visit:07d}-{ccd:03d}.fits"
        dataId = dict(tract=tract, visit=visit, ccd=ccd)
        linkFile(os.path.join(source, f"jointcal_photoCalib-{suffix}"), butler, "jointcal_photoCalib", dataId)
        linkFile(os.path.join(source, f"jointcal_wcs-{suffix}"), butler, "jointcal_wcs", dataId)


def installExternalData():
    """Command-line interface for installing external data"""
    parser = argparse.ArgumentParser(description="Install extenral data")
    parser.add_argument("source", help="Source of external data")
    parser.add_argument("root", help="Butler data root")
    parser.add_argument("--tract", type=int, default=0, help="Tract identifier")
    parser.add_argument("--visitCcd", nargs=2, type=int, default=[], action="append",
                        help="Visit and CCD of jointcal data to ingest (multiple OK)")
    args = parser.parse_args()

    butler = Butler(args.root)
    installJointcal(args.source, butler, args.tract, args.visitCcd)
