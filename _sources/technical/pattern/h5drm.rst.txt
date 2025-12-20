H5DRM Pattern
=============

The H5DRM pattern implements the Domain Reduction Method (DRM) using the H5DRM data format for seismic analysis.

Overview
--------
The H5DRM pattern is used to apply seismic forces and displacements to a finite element model using data stored in the H5DRM format. It supports coordinate transformations and scaling for flexible integration with different models.

Parameters
----------
The following table describes the parameters for the H5DRM pattern:

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - **filepath**
     - str
     - Path to the H5DRM dataset (required).
   * - **factor**
     - float
     - Scale factor for DRM forces and displacements (required).
   * - **crd_scale**
     - float
     - Scale factor for dataset coordinates (required).
   * - **distance_tolerance**
     - float
     - Tolerance for DRM point to FE mesh matching (required).
   * - **do_coordinate_transformation**
     - int
     - Whether to apply coordinate transformation (0/1, required).
   * - **transform_matrix**
     - list[float]
     - 3x3 transformation matrix [T00, T01, T02, T10, T11, T12, T20, T21, T22] (required).
   * - **origin**
     - list[float]
     - Origin location after transformation [x00, x01, x02] (required).

Usage Example
-------------

.. code-block:: python

   from femora.components.Pattern.patternBase import PatternManager

   # Get the pattern manager instance
   pattern_manager = PatternManager()

   # Create an H5DRM pattern
   h5drm_pattern = pattern_manager.create_pattern(
       'h5drm',
       filepath='path/to/h5drm/file',
       factor=1.0,
       crd_scale=1.0,
       distance_tolerance=0.01,
       do_coordinate_transformation=1,
       transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
       origin=[0.0, 0.0, 0.0]
   )

