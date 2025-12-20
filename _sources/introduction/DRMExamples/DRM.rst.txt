Domain Reduction Method (DRM) Examples
======================================

.. raw:: html

    <h1>Introduction</h1>

The Domain Reduction Method (DRM) is a powerful technique for modeling seismic wave propagation in a computationally efficient manner. This section provides a series of examples demonstrating how to use Femora's DRM capabilities to model increasingly complex scenarios.

.. raw:: html

    <h2>Key Concepts of Domain Reduction Method</h2>


The Domain Reduction Method, first proposed by Bielak et al. (2003), is a two-step approach for modeling wave propagation problems:

1. **Background Analysis**: A large-scale analysis (often simplified) to capture regional wave propagation from source to site.
2. **Local Analysis**: A detailed analysis of a smaller domain of interest, using the results from step 1 as boundary conditions.

This approach offers several advantages:

* **Computational Efficiency**: Focuses computational resources on the domain of interest
* **Realistic Wave Input**: Captures complex wave patterns without modeling the entire source-to-site path
* **Flexibility**: Works with various wave types, source mechanisms, and site conditions
* **Enhanced Resolution**: Allows for detailed analysis of local site effects and structure-soil interaction

.. raw:: html

    <span style="font-size: 1.5em;"><b>Example Overview</b></span>

This section includes multiple examples demonstrating DRM applications of increasing complexity:

.. toctree::
   :maxdepth: 1

   example1
   example2
   example3

These examples progress from simple configurations to more complex geological settings, demonstrating Femora's capabilities in handling realistic seismic wave propagation problems.



References
----------

1. Bielak, J., Loukakis, K., Hisada, Y., & Yoshimura, C. (2003). Domain reduction method for three-dimensional earthquake modeling in localized regions, Part I: Theory. Bulletin of the Seismological Society of America, 93(2), 817-824.

2. Yoshimura, C., Bielak, J., Hisada, Y., & Fernández, A. (2003). Domain reduction method for three-dimensional earthquake modeling in localized regions, Part II: Verification and applications. Bulletin of the Seismological Society of America, 93(2), 825-841.

3. Jeong, C., Esmaeilzadeh Seylabi, E., Taciroglu, E. (2018). A time-domain substructuring method for dynamic soil-structure interaction analysis of arbitrarily shaped foundation-soil systems. International Journal for Numerical Methods in Engineering, 114(11), 1211-1239.
