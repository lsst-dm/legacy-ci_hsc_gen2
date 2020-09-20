#!/bin/bash
#
# Use the obs_base convert script to produce a gen3 repo from the gen2 output.

# On OS X El Capitan we need to pass through the library load path
if [[ $(uname -s) = Darwin* ]]; then
    if [[ -z "$DYLD_LIBRARY_PATH" ]]; then
        export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH
    fi
fi

GEN2ROOT="--gen2root $CI_HSC_GEN2_DIR/DATA"
GEN3ROOT="$CI_HSC_GEN2_DIR/DATAgen3"
CALIBS="--calibs CALIB"  # note path is relative to GEN2ROOT
SKYMAPNAME="--skymap-name discrete/ci_hsc"
SKYMAPCONFIG="--skymap-config skymap.py"
JOINTCAL_DATASET_CONFIG="-C convertJointcalDatasets.py"
RERUNS="--reruns rerun/ci_hsc"
# shellcheck disable=SC2086
"$DAF_BUTLER_DIR/bin/butler" convert $GEN3ROOT $GEN2ROOT $CALIBS $RERUNS $SKYMAPNAME $SKYMAPCONFIG $JOINTCAL_DATASET_CONFIG
