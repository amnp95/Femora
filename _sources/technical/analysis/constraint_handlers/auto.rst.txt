Auto constraint handler
=======================

The Auto constraint handler automatically selects the most appropriate constraint handling method based on the problem characteristics and constraints present in the model.

Description
-----------

The Auto handler is particularly useful for:

* General-purpose analysis where the optimal constraint handler is not known
* Problems with mixed constraint types
* Users who want optimal performance without manual selection
* Automated analysis workflows

This handler analyzes the model's constraints and characteristics to choose between Plain, Transformation, Penalty, or Lagrange methods.

Parameters
----------

``verbose`` : bool, default=False
    Print detailed information about the selection process.

``auto_penalty`` : float, optional
    Penalty factor to use for automatic methods.

``user_penalty`` : float, optional
    Custom penalty factor specified by user.

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create an Auto constraint handler with default settings
    fm.analysis.constraint.create_handler("Auto")
    
    # Create with verbose output
    fm.analysis.constraint.create_handler("Auto", verbose=True)
    
    # Create with custom penalty factor
    fm.analysis.constraint.create_handler("Auto", user_penalty=1.0e8) 