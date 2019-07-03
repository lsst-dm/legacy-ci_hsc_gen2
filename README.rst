==========
``ci_hsc_gen2``
==========

``gen2_ci_hsc`` provides scripts which use the LSST stack to perform single frame and coadd processing based
on engineering test data from Hyper Suprime-Cam.

Obtaining test data
===================

The data used by ``gen2_ci_hsc`` is linked against data installed by ``testdata_ci_hsc``, please
setup that package before running scons on this one.

Running the tests
=================

Set up the package
------------------

The package must be set up in the usual way before running::

  $ cd ci_hsc_gen2
  $ setup -j -r .

Running the tests
-----------------

Execute ``scons``. On a Mac running OSX 10.11 or greater, you must specify a
Python interpreter followed by a full path to ``scons``::

  $ python $(which scons)

On other systems, simply running ``scons`` should be sufficient.
