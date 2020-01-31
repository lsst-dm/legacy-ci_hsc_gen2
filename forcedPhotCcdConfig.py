# We haven't processed all the patches that overlap some of our CCDs
# to save some time.
config.references.skipMissing = True

# We don't run jointcal, so can't load its results
config.recalibrate.doApplyExternalPhotoCalib = False
config.recalibrate.doApplyExternalSkyWcs = False