# -*- python -*-

import os
from collections import defaultdict
from lsst.pipe.base import Struct
from lsst.sconsUtils.utils import libraryLoaderEnvironment
from lsst.utils import getPackageDir
from lsst.ci.hsc.gen2.validate import (RawValidation, DetrendValidation, SfmValidation,
                                       SkyCorrValidation, SkymapValidation, WarpValidation,
                                       CoaddValidation, DetectionValidation, MergeDetectionsValidation,
                                       MeasureValidation, MergeMeasurementsValidation,
                                       ForcedPhotCoaddValidation, ForcedPhotCcdValidation,
                                       VersionValidation, DeblendSourcesValidation,
                                       WriteSourceValidation, TransformSourceValidation,
                                       ConsolidateSourceValidation,
                                       WriteObjectValidation, TransformObjectValidation,
                                       ConsolidateObjectValidation)

from SCons.Script import SConscript
SConscript(os.path.join(".", "bin.src", "SConscript"))  # build bin scripts

env = Environment(ENV=os.environ)
env["ENV"]["OMP_NUM_THREADS"] = "1"  # Disable threading; we're parallelising at a higher level

gen3validateCmds = {}


def validate(cls, root, dataId=None, gen3id=None, filepath=None, **kwargs):
    """!Construct a command-line for validation

    @param cls  Validation class to use
    @param root  Data repo root directory
    @param dataId  Data identifier dict (Gen2), or None
    @param gen3Id  Gen3 data identifier dict, or None
    @param filepath  an input file containing expected values to validate with
    @param kwargs  Additional key/value pairs to add to dataId
    @return Command-line string to run validation
    """
    if dataId:
        dataId = dataId.copy()
        dataId.update(kwargs)
    elif kwargs:
        dataId = kwargs
    cmd = [getExecutable("ci_hsc_gen2", "validate.py"), cls.__name__, root]
    if filepath:
        cmd += ["--filepath", filepath]
    gen3 = cmd + ["--gen3", "--collection", "HSC/runs/ci_hsc"]
    if dataId:
        cmd += ["--id %s" % (" ".join("%s=%s" % (key, value) for key, value in dataId.items()))]
    if gen3id:
        gen3 += ["--id %s" % (" ".join("%s=%s" % (key, value) for key, value in gen3id.items()))]
        gen3validateCmds.setdefault(cls.__name__, []).append(" ".join(gen3))
    return " ".join(cmd)


profileNum = -1


def getProfiling(script):
    """Return python command-line argument string for profiling

    If activated (via the "--enable-profile" command-line argument),
    we write the profile to a filename starting with the provided
    base name and including a sequence number and the script name,
    so its contents can be quickly identified.

    Note that this is python function-level profiling, which won't
    descend into C++ elements of the codebase.

    A basic profile can be printed using python:

        >>> from pstats import Stats
        >>> stats = Stats("profile-123-script.pstats")
        >>> stats.sort_stats("cumulative").print_stats(30)
    """
    base = GetOption("enable_profile")
    if not base:
        return ""
    global profileNum
    profileNum += 1
    if script.endswith(".py"):
        script = script[:script.rfind(".")]
    return "-m cProfile -o %s-%03d-%s.pstats" % (base, profileNum, script)


def getExecutable(package, script, directory=None):
    """
    Given the name of a package and a script or other python executable which
    lies within the given subdirectory (defaults to "bin"), return an
    appropriate string which can be used to set up an appropriate environment
    and execute the command.

    This includes:
    * Specifying an explict list of paths to be searched by the dynamic linker;
    * Specifying a Python executable to be run (we assume the one on the
      default ${PATH} is appropriate);
    * Specifying the complete path to the script.
    """
    if directory is None:
        directory = "bin"
    return "{} python {} {}".format(libraryLoaderEnvironment(),
                                    getProfiling(script),
                                    os.path.join(env.ProductDir(package), directory, script))


Execute(Mkdir(".scons"))

root = Dir('.').srcnode().abspath
AddOption("--raw", default=os.path.join(root, "raw"), help="Path to raw data")
AddOption("--repo", default=os.path.join(root, "DATA"), help="Path for data repository")
AddOption("--calib", default=os.path.join(root, "CALIB"), help="Path for calib repository")
AddOption("--rerun", default="ci_hsc", help="Rerun name")
AddOption("--no-versions", dest="no_versions", default=False, action="store_true",
          help="Add --no-versions for LSST scripts")
AddOption("--enable-profile", nargs="?", const="profile", dest="enable_profile",
          help=("Profile base filename; output will be <basename>-<sequence#>-<script>.pstats; "
                "(Note: this option is for profiling the scripts, while --profile is for scons)"))

RAW = GetOption("raw")
REPO = GetOption("repo")
REPO_GEN3 = REPO + "gen3"
CALIB = GetOption("calib")
PROC = GetOption("repo") + " --rerun " + GetOption("rerun")  # Common processing arguments
DATADIR = os.path.join(GetOption("repo"), "rerun", GetOption("rerun"))
STDARGS = "--doraise" + (" --no-versions" if GetOption("no_versions") else "")


def command(target, source, cmd):
    """Run a command and record that we ran it

    The record is in the form of a file in the ".scons" directory.
    """
    name = os.path.join(".scons", target)
    if isinstance(cmd, str):
        cmd = [cmd]
    out = env.Command(name, source, cmd + [Touch(name)])
    env.Alias(target, name)
    return out


class Data(Struct):
    """Data we can process"""
    def __init__(self, visit, ccd):
        Struct.__init__(self, visit=visit, ccd=ccd)

    @property
    def name(self):
        """Returns a suitable name for this data"""
        return "%d-%d" % (self.visit, self.ccd)

    @property
    def dataId(self):
        """Returns the dataId for this data"""
        return dict(visit=self.visit, ccd=self.ccd)

    def gen3id(self, raw=False):
        """Returns the Gen3 data ID for this data"""
        if raw:
            return dict(instrument="HSC", exposure=self.visit, detector=self.ccd)
        else:
            return dict(instrument="HSC", visit=self.visit, detector=self.ccd)

    def id(self, prefix="--id", tract=None):
        """Returns a suitable --id command-line string"""
        r = "%s visit=%d ccd=%d" % (prefix, self.visit, self.ccd)
        if tract is not None:
            r += " tract=%d" % tract
        return r

    def sfm(self, env):
        """Process this data through single frame measurement"""
        return command("sfm-" + self.name, ingestValidations + calibValidations + [preSfm, refcat],
                       [getExecutable("pipe_tasks", "processCcd.py") + " " + PROC + " " + self.id() + " " +
                        STDARGS + " -c calibrate.astrometry.maxMeanDistanceArcsec=0.025 " +
                        "calibrate.requireAstrometry=False calibrate.requirePhotoCal=False " +
                        "charImage.doWriteExposure=True",
                        validate(SfmValidation, DATADIR, self.dataId, gen3id=self.gen3id())])

    def writeSource(self, env):
        return command("writeSource-" + self.name, [preWriteSource, sfm[(self.visit, self.ccd)]],
                       [getExecutable("pipe_tasks", "writeSourceTable.py") +
                        " " + PROC + " " + self.id() + " " + STDARGS,
                        validate(WriteSourceValidation, DATADIR, self.dataId, gen3id=self.gen3id())])

    def transformSource(self, env):
        return command("transformSource-" + self.name,
                       [preTransformSource, writeSource[(self.visit, self.ccd)]],
                       [getExecutable("pipe_tasks", "transformSourceTable.py") +
                        " " + PROC + " " + self.id() + " " + STDARGS,
                        validate(TransformSourceValidation, DATADIR, self.dataId, gen3id=self.gen3id())])

    def forced(self, env, tract):
        """Process this data through CCD-level forced photometry"""
        dataId = self.dataId.copy()
        dataId["tract"] = tract
        return command("forced-ccd-" + self.name, ingestValidations + calibValidations + [preForcedPhotCcd],
                       [getExecutable("meas_base", "forcedPhotCcd.py") + " " + PROC + " " +
                        self.id(tract=tract) + " " + STDARGS + " -C forcedPhotCcdConfig.py" +
                        " -c externalPhotoCalibName=jointcal",
                        validate(ForcedPhotCcdValidation, DATADIR, dataId,
                                 gen3id=dict(tract=0, skymap="discrete/ci_hsc", **self.gen3id()))])


allData = {"HSC-R": [Data(903334, 16),
                     Data(903334, 22),
                     Data(903334, 23),
                     Data(903334, 100),
                     Data(903336, 17),
                     Data(903336, 24),
                     Data(903338, 18),
                     Data(903338, 25),
                     Data(903342, 4),
                     Data(903342, 10),
                     Data(903342, 100),
                     Data(903344, 0),
                     Data(903344, 5),
                     Data(903344, 11),
                     Data(903346, 1),
                     Data(903346, 6),
                     Data(903346, 12),
                     ],
           "HSC-I": [Data(903986, 16),
                     Data(903986, 22),
                     Data(903986, 23),
                     Data(903986, 100),
                     Data(904014, 1),
                     Data(904014, 6),
                     Data(904014, 12),
                     Data(903990, 18),
                     Data(903990, 25),
                     Data(904010, 4),
                     Data(904010, 10),
                     Data(904010, 100),
                     Data(903988, 16),
                     Data(903988, 17),
                     Data(903988, 23),
                     Data(903988, 24),
                     ],
           }
# Link against existing data
links = env.Command(["CALIB", "raw", "brightObjectMasks", "ps1_pv3_3pi_20170110", "jointcal"], [],
                    ["bin/linker.sh"])

# Set up the data repository
mapper = env.Command(os.path.join(REPO, "_mapper"), ["bin", links],
                     ["mkdir -p " + REPO,
                      "echo lsst.obs.hsc.HscMapper > " + os.path.join(REPO, "_mapper"),
                      ])

calib = env.Command(os.path.join(REPO, "CALIB"), mapper,
                    ["rm -f " + os.path.join(REPO, "CALIB"),
                     "ln -s " + CALIB + " " + os.path.join(REPO, "CALIB")]
                    )
ingest = env.Command(os.path.join(REPO, "registry.sqlite3"), calib,
                     [getExecutable("pipe_tasks", "ingestImages.py") + " " + REPO + " " + RAW +
                     "/*.fits --mode=link " + "-c clobber=True register.ignore=True " + STDARGS]
                     )
ingestValidations = [command("ingestValidation-%(visit)d-%(ccd)d" % data.dataId, ingest,
                             validate(RawValidation, REPO, data.dataId, gen3id=data.gen3id(True))) for
                     data in sum(allData.values(), [])]
calibValidations = [command("calibValidation-%(visit)d-%(ccd)d" % data.dataId, ingest,
                            validate(DetrendValidation, REPO, data.dataId)) for
                    data in sum(allData.values(), [])]

installExternalData = command("installExternalData", [ingest, links],
                              [getExecutable("ci_hsc_gen2", "installExternalData.py") +
                               f" jointcal {REPO} --tract 0 " +
                               " ".join(f"--visitCcd {dd.visit} {dd.ccd}" for
                                        dd in sum(allData.values(), []))])

refcatName = "ps1_pv3_3pi_20170110"
refcatPath = os.path.join(REPO, "ref_cats", refcatName)
refcat = env.Command(refcatPath, mapper,
                     ["rm -f " + refcatPath,  # Delete any existing, perhaps leftover from previous
                      "ln -s %s %s" % (os.path.join(root, refcatName), refcatPath)])

# Add transmission curves to the repository.
transmissionCurvesTarget = os.path.join(REPO, "transmission")
transmissionCurves = env.Command(transmissionCurvesTarget, calib,
                                 [getExecutable("obs_subaru", "installTransmissionCurves.py") + " " + REPO])

# Create skymap
# This needs to be done early and in serial, so that the package versions
# produced by it aren't clobbered by other commands in-flight.
skymap = command("skymap", mapper,
                 [getExecutable("pipe_tasks", "makeSkyMap.py") + " " + PROC + " -C skymap.py " + STDARGS,
                  validate(SkymapValidation, DATADIR, gen3id=dict(skymap="discrete/ci_hsc"))])

# Add brightObjectMasks to the *rerun* dir, because their data IDs involve
# the tracts and patches defined by the skymap.
brightObjSource = os.path.join(root, "brightObjectMasks")
brightObjTarget = os.path.join(DATADIR, "deepCoadd", "BrightObjectMasks")
brightObj = env.Command(brightObjTarget, [mapper, skymap],
                        ["rm -f " + brightObjTarget,  # Delete any existing
                         "mkdir -p " + os.path.dirname(brightObjTarget),
                         "ln -s %s %s" % (brightObjSource, brightObjTarget)])

# Single frame measurement
# preSfm step is a work-around for a race on schema/config/versions
preSfm = command("sfm", [skymap, transmissionCurvesTarget],
                 getExecutable("pipe_tasks", "processCcd.py") + " " + PROC + " " + STDARGS +
                 " -c calibrate.astrometry.maxMeanDistanceArcsec=0.025 " +
                 "calibrate.requireAstrometry=False calibrate.requirePhotoCal=False " +
                 "charImage.doWriteExposure=True")
env.Depends(preSfm, refcat)
sfm = {(data.visit, data.ccd): data.sfm(env) for data in sum(allData.values(), [])}

visitDataLists = defaultdict(list)
for filterName in allData:
    for data in allData[filterName]:
        visitDataLists[data.visit].append(data)


# Sky correction
def processSkyCorr(visitDataLists):
    """Generate sky corrections"""
    preSkyCorr = command("skyCorr", skymap,
                         getExecutable("pipe_drivers", "skyCorrection.py") + " " + PROC + " " + STDARGS +
                         " --batch-type=smp --cores=1")
    nameList = ("skyCorr-%d" % (vv,) for vv in visitDataLists)
    depList = ([sfm[(data.visit, data.ccd)] for data in visitDataLists[vv]] for vv in visitDataLists)
    cmdList = (getExecutable("pipe_drivers", "skyCorrection.py") + " " + PROC + " " + STDARGS +
               " --batch-type=none --id visit=%d --job=skyCorr-%d" % (vv, vv) for vv in visitDataLists)
    validateList = ([validate(SkyCorrValidation, DATADIR, data.dataId, gen3id=data.gen3id())
                    for data in visitDataLists[vv]] for vv in visitDataLists)
    return {vv: command(target=name, source=[preSkyCorr] + dep, cmd=[cmd] + val)
            for vv, name, dep, cmd, val in zip(visitDataLists, nameList, depList, cmdList, validateList)}


skyCorr = processSkyCorr(visitDataLists)

# a work-around for a race on config/versions
preWriteSource = command("writeSource", preSfm,
                         [getExecutable("pipe_tasks", "writeSourceTable.py") +
                          " " + PROC + " " + STDARGS])
preTransformSource = command("transformSource", preWriteSource,
                             [getExecutable("pipe_tasks", "transformSourceTable.py") +
                              " " + PROC + " " + STDARGS])
preConsolidateSource = command("consolidateSource", preTransformSource,
                               [getExecutable("pipe_tasks", "consolidateSourceTable.py") +
                                " " + PROC + " " + STDARGS])

writeSource = {(data.visit, data.ccd): data.writeSource(env) for data in sum(allData.values(), [])}
transformSource = {(data.visit, data.ccd): data.transformSource(env) for data in sum(allData.values(), [])}


def processConsolidateSource(visitDataLists):
    nameList = ("consolidateSource-%d" % (vv,) for vv in visitDataLists)
    depList = ([transformSource[(data.visit, data.ccd)] for data in visitDataLists[vv]]
               for vv in visitDataLists)
    cmdList = (getExecutable("pipe_tasks", "consolidateSourceTable.py") + " " + PROC + " " + STDARGS +
               "  --id visit=%d " % (vv) for vv in visitDataLists)
    catSchema = os.path.join(getPackageDir("sdm_schemas"), 'yml', 'hsc_gen2.yaml')
    validateList = ([validate(ConsolidateSourceValidation, DATADIR, visit=vv,
                              gen3id=dict(instrument="HSC", visit=vv), filepath=catSchema)]
                    for vv in visitDataLists)
    return {vv: command(target=name, source=[preConsolidateSource] + dep, cmd=[cmd] + val)
            for vv, name, dep, cmd, val in zip(visitDataLists, nameList, depList, cmdList, validateList)}


consolidateSource = processConsolidateSource(visitDataLists)

patchDataId = dict(tract=0, patch="5,4")
patchGen3id = dict(skymap="discrete/ci_hsc", tract=0, patch=69)
patchId = " ".join(("%s=%s" % (k, v) for k, v in patchDataId.items()))

# Coadd construction
# preWarp, preCoadd and preDetect steps are a work-around for a race on
# schema/config/versions
preWarp = command("warp", [skymap, installExternalData],
                  getExecutable("pipe_tasks", "makeCoaddTempExp.py") + " " + PROC + " " + STDARGS +
                  " -c externalPhotoCalibName=jointcal")
preCoadd = command("coadd", [skymap, brightObj],
                   getExecutable("pipe_tasks", "assembleCoadd.py") + " --warpCompareCoadd  " +
                   PROC + " " + STDARGS +
                   " -c externalPhotoCalibName=jointcal")
preDetect = command("detect", skymap,
                    getExecutable("pipe_tasks", "detectCoaddSources.py") + " " + PROC + " " + STDARGS)


def processCoadds(filterName, dataList):
    """Generate coadds and run detection on them"""
    ident = "--id " + patchId + " filter=" + filterName
    exposures = defaultdict(list)
    for data in dataList:
        exposures[data.visit].append(data)
    warps = [command("warp-%d" % exp,
                     [skymap, preWarp] + [skyCorr[exp]],
                     [getExecutable("pipe_tasks", "makeCoaddTempExp.py") + " " + PROC + " " + ident +
                      " " + " ".join(data.id("--selectId") for data in exposures[exp]) + " " + STDARGS +
                      " -c externalPhotoCalibName=jointcal",
                      validate(WarpValidation, DATADIR, patchDataId, visit=exp, filter=filterName,
                               gen3id=dict(instrument="HSC", visit=exp, **patchGen3id))
                      ]) for exp in exposures]
    coadd = command("coadd-" + filterName, warps + [preCoadd],
                    [getExecutable("pipe_tasks", "assembleCoadd.py") + " --warpCompareCoadd " + PROC +
                     " " + ident + " " + " ".join(data.id("--selectId") for data in dataList) + " " +
                     STDARGS + " -c externalPhotoCalibName=jointcal",
                     validate(CoaddValidation, DATADIR, patchDataId, filter=filterName,
                              gen3id=dict(band=filterName[-1].lower(), **patchGen3id))
                     ])
    detect = command("detect-" + filterName, [coadd, preDetect],
                     [getExecutable("pipe_tasks", "detectCoaddSources.py") + " " + PROC + " " + ident +
                      " " + STDARGS,
                      validate(DetectionValidation, DATADIR, patchDataId, filter=filterName,
                               gen3id=dict(band=filterName[-1].lower(), **patchGen3id))
                      ])
    return detect


coadds = {ff: processCoadds(ff, allData[ff]) for ff in allData}

# Multiband processing
filterList = coadds.keys()
mergeDetections = command("mergeDetections", sum(coadds.values(), []),
                          [getExecutable("pipe_tasks", "mergeCoaddDetections.py") + " " + PROC + " --id " +
                           patchId + " filter=" + "^".join(filterList) + " " + STDARGS,
                           validate(MergeDetectionsValidation, DATADIR, patchDataId, gen3id=patchGen3id)
                           ])

# Since the deblender input is a single mergedDet catalog,
# but the output is a SourceCatalog in each band,
# we have to validate each band separately
deblendValidation = [validate(DeblendSourcesValidation, DATADIR, patchDataId, filter=ff,
                              gen3id=dict(band=ff[-1].lower(), **patchGen3id))
                     for ff in filterList]
deblendSources = command("deblendSources", mergeDetections,
                         [getExecutable("pipe_tasks", "deblendCoaddSources.py") + " " + PROC + " --id " +
                          patchId + " filter=" + "^".join(filterList) + " " + STDARGS
                          ] + deblendValidation)

# preMeasure step is a work-around for a race on schema/config/versions
preMeasure = command("measure", deblendSources,
                     getExecutable("pipe_tasks", "measureCoaddSources.py") + " " + PROC + " " + STDARGS)


def measureCoadds(filterName):
    return command("measure-" + filterName, preMeasure,
                   [getExecutable("pipe_tasks", "measureCoaddSources.py") + " " + PROC + " --id " +
                    patchId + " filter=" + filterName + " " + STDARGS,
                    validate(MeasureValidation, DATADIR, patchDataId, filter=filterName,
                             gen3id=dict(band=filterName[-1].lower(), **patchGen3id))
                    ])


measure = [measureCoadds(ff) for ff in filterList]

mergeMeasurements = command("mergeMeasurements", measure,
                            [getExecutable("pipe_tasks", "mergeCoaddMeasurements.py") + " " + PROC +
                             " --id " + patchId + " filter=" + "^".join(filterList) + " " + STDARGS,
                             validate(MergeMeasurementsValidation, DATADIR, patchDataId, gen3id=patchGen3id)
                             ])

# preForcedPhotCoadd step is a work-around for a race on schema/config/versions
preForcedPhotCoadd = command("forcedPhotCoadd", [mapper, mergeMeasurements],
                             getExecutable("meas_base", "forcedPhotCoadd.py") + " " + PROC + " " + STDARGS)


def forcedPhotCoadd(filterName):
    return command("forced-coadd-" + filterName, [mergeMeasurements, preForcedPhotCoadd],
                   [getExecutable("meas_base", "forcedPhotCoadd.py") + " " + PROC + " --id " + patchId +
                    " filter=" + filterName + " " + STDARGS,
                    validate(ForcedPhotCoaddValidation, DATADIR, patchDataId, filter=filterName,
                             gen3id=dict(band=filterName[-1].lower(), **patchGen3id))
                    ])


forcedPhotCoadd = [forcedPhotCoadd(ff) for ff in filterList]

# preForcedPhotCcd step is a work-around for a race on schema/config/versions
preForcedPhotCcd = command("forcedPhotCcd", [mapper, mergeMeasurements, installExternalData],
                           getExecutable("meas_base", "forcedPhotCcd.py") + " " + PROC +
                           " -C forcedPhotCcdConfig.py" + " " + STDARGS +
                           " -c externalPhotoCalibName=jointcal")

forcedPhotCcd = [data.forced(env, tract=0) for data in sum(allData.values(), [])]

# post-processing
writeObjectTable = command("writeObjectTable", [forcedPhotCoadd],
                           [getExecutable("pipe_tasks", "writeObjectTable.py") + " " + PROC +
                            " --id " + patchId + " filter=" + "^".join(filterList) + " " + STDARGS,
                            validate(WriteObjectValidation, DATADIR, patchDataId, gen3id=patchGen3id)])

catSchema = os.path.join(getPackageDir("sdm_schemas"), 'yml', 'hsc_gen2.yaml')
transformObjectCatalog = command("transformObjectCatalog", [writeObjectTable],
                                 [getExecutable("pipe_tasks", "transformObjectCatalog.py") + " " + PROC +
                                  " --id " + patchId + " " + STDARGS,
                                  validate(TransformObjectValidation, DATADIR, patchDataId,
                                           gen3id=patchGen3id, filepath=catSchema)])

consolidateObjectTable = command("consolidateObjectTable", [transformObjectCatalog],
                                 [getExecutable("pipe_tasks", "consolidateObjectTable.py") + " " + PROC +
                                  " --id " + patchId + " " + STDARGS,
                                  validate(ConsolidateObjectValidation, DATADIR, patchDataId,
                                           gen3id=patchGen3id)])

gen3repo = env.Command([os.path.join(REPO_GEN3, "butler.yaml"), os.path.join(REPO, "gen3.sqlite3")],
                       [forcedPhotCcd, consolidateObjectTable] + list(consolidateSource.values()),
                       "bin/gen2to3.sh")
env.Alias("gen3repo", gen3repo)

gen3repoValidate = [command("gen3repo-{}".format(k), [gen3repo], v) for k, v in gen3validateCmds.items()]
env.Alias("gen3repo-validate", gen3repoValidate)

tests = [command(f"test_{name}", [gen3repo], getExecutable("ci_hsc_gen2", f"test_{name}.py", "tests"))
         for name in ("import", "butlerShims", "gen2to3")]

env.Alias("tests", tests)

everything = [gen3repoValidate, tests]

if not GetOption("no_versions"):
    versions = command("versions", [forcedPhotCcd, forcedPhotCoadd], validate(VersionValidation, DATADIR, {}))
    everything.append(versions)

# Add a no-op install target to keep Jenkins happy.
env.Alias("install", "SConstruct")

env.Alias("all", everything)
Default(everything)

env.Clean(everything, [".scons", "DATA/rerun/ci_hsc"] + [x for x in links] + ["DATA", "DATAgen3"])
