Installation Guide
==================

System Requirements
-------------------

Before installing FEMORA, ensure your system meets the following requirements:

* **Operating System**: Windows, macOS, or Linux
* **Python**: Version 3.8 or higher
* **Disk Space**: Approximately 100 MB
* **Dependencies**: NumPy, SciPy, Matplotlib, PySide6

Installation Methods
--------------------

There are several ways to install FEMORA:

Using pip
~~~~~~~~~

The easiest way to install FEMORA is using pip:

.. code-block:: bash

   pip install femora

From Source
~~~~~~~~~~~

To install from source:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/yourusername/femora.git
      cd femora

2. Install the package:

   .. code-block:: bash

      pip install -e .

Using Conda
~~~~~~~~~~~

FEMORA can also be installed using conda:

.. code-block:: bash

   conda env create -f environment.yml
   conda activate femora

Verifying Installation
----------------------

To verify that FEMORA has been installed correctly, run:

.. code-block:: python

   import femora
   print(femora.__version__)

This should display the version number of your FEMORA installation.

Dependencies
------------

FEMORA depends on several Python packages:

* **NumPy**: For numerical operations
* **SciPy**: For scientific computing
* **Matplotlib**: For visualization
* **PySide6**: For GUI components
* **OpenSees**: For structural analysis (optional)

Troubleshooting
---------------

Common Installation Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Missing Dependencies**:
   
   If you encounter errors related to missing dependencies, try:
   
   .. code-block:: bash
   
      pip install -r requirements.txt

2. **Version Conflicts**:
   
   If you have version conflicts with existing packages, try creating a virtual environment:
   
   .. code-block:: bash
   
      python -m venv femora_env
      source femora_env/bin/activate  # On Windows: femora_env\Scripts\activate
      pip install femora

3. **Permission Errors**:
   
   If you encounter permission errors, try:
   
   .. code-block:: bash
   
      pip install --user femora

Getting Help
~~~~~~~~~~~~

If you continue to experience installation issues, please:

1. Check the GitHub issues page for similar problems and solutions
2. Contact the support team at support@femora.org
3. Join our community forum at https://community.femora.org