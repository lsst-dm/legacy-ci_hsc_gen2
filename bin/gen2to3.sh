#!/bin/bash
#
# Use the obs_base convert script to produce a gen3 repo from the gen2 output.

# On OS X El Capitan we need to pass through the library load path
if [[ $(uname -s) = Darwin* ]]; then
    if [[ -z "$DYLD_LIBRARY_PATH" ]]; then
        export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH
    fi
fi

INSTRUMENTCLASS=lsst.obs.subaru.HyperSuprimeCam
GEN2ROOT="--gen2root $CI_HSC_GEN2_DIR/DATA"
GEN3ROOT="--gen3root $CI_HSC_GEN2_DIR/DATAgen3"
CALIBS="--calibs CALIB"  # note path is relative to GEN2ROOT
SKYMAPNAME="--skymapName discrete/ci_hsc"
SKYMAPCONFIG="--skymapConfig skymap.py"
RERUNS="--reruns rerun/ci_hsc"
# shellcheck disable=SC2086
"$OBS_BASE_DIR/bin/convert_gen2_repo_to_gen3.py" $INSTRUMENTCLASS $GEN2ROOT $GEN3ROOT $RERUNS $CALIBS $SKYMAPNAME $SKYMAPCONFIG
