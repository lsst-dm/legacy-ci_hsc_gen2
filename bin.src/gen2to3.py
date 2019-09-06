#!/usr/bin/env python

# This file is part of ci_hsc_gen2.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import argparse
import os

from lsst.log import Log, LogHandler
from lsst.utils import getPackageDir
from lsst.obs.base.gen2to3 import ConvertRepoTask, ConvertRepoSkyMapConfig
from lsst.obs.subaru.gen3.hsc import HyperSuprimeCam
from lsst.ci.hsc.gen2.gen2to3 import makeButler, REPO_ROOT


def main(config=None):
    instrument = HyperSuprimeCam()
    convertRepoConfig = ConvertRepoTask.ConfigClass()
    instrument.applyConfigOverrides(ConvertRepoTask._DefaultName, convertRepoConfig)
    convertRepoConfig.skyMaps["discrete/ci_hsc"] = ConvertRepoSkyMapConfig()
    convertRepoConfig.skyMaps["discrete/ci_hsc"].load(os.path.join(getPackageDir("ci_hsc_gen2"), "skymap.py"))
    butler3 = makeButler(config)
    convertRepoTask = ConvertRepoTask(config=convertRepoConfig, butler3=butler3)
    convertRepoTask.run(
        root=REPO_ROOT,
        collections=["shared/ci_hsc"],
        calibs={"CALIB": ["calib/hsc"]},
        reruns={"rerun/ci_hsc": ["shared/ci_hsc"]},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert ci_hsc data repos to Butler Gen 3.")
    parser.add_argument("-v", "--verbose", action="store_const", dest="logLevel",
                        default=Log.INFO, const=Log.DEBUG,
                        help="Set the log level to DEBUG.")
    parser.add_argument("-c", "--config",
                        help="Path to a butler configuration file to be used instead of the default"
                             " ci_hsc configuration.")
    args = parser.parse_args()
    log = Log.getLogger("convertRepo")
    log.setLevel(args.logLevel)

    # Forward python logging to lsst logger
    lgr = logging.getLogger("convertRepo")
    lgr.setLevel(logging.INFO if args.logLevel == Log.INFO else logging.DEBUG)
    lgr.addHandler(LogHandler())

    main(config=args.config)
