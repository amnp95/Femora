PathTime
""""""""""""""""""

The PathTime time series represents a time series where both time points and values are specified, either directly or from separate files.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **time**
      - List of time points (optional if using fileTime)
      - list[float]
    * - **fileTime**
      - Path to file containing time points (optional if using time)
      - str
    * - **values**
      - List of force values (optional if using filePath)
      - list[float]
    * - **filePath**
      - Path to file containing force values (optional if using values)
      - str
    * - **factor**
      - Scale factor for force values (default: 1.0)
      - float
    * - **useLast**
      - Use last force value beyond the last time point (default: False)
      - bool
    * - **prependZero**
      - Prepend a zero value at the start (default: False)
      - bool
    * - **startTime**
      - Start time of the time series (default: 0.0)
      - float

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Using direct values
        from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        
        ts_manager = TimeSeriesManager()
        pathtime_ts = ts_manager.create_time_series(
            'PathTime',
            time=[0.0, 0.1, 0.2, 0.3, 0.4],
            values=[0.0, 0.5, 1.0, 0.5, 0.0],
            factor=2.0
        )

        # Using files
        pathtime_ts = ts_manager.create_time_series(
            'PathTime',
            fileTime='data/time.txt',
            filePath='data/forces.txt',
            factor=9.81,
            useLast=True
        )

        # Via Femora
        import femora as fm
        
         
        pathtime_ts = fm.timeSeries.create_time_series(
            'PathTime',
            time=[0, 1, 2, 3],
            values=[0, 1, 0, -1],
            factor=1.5,
            prependZero=True
        )

.. admonition:: File Format
    :class: info

    When using files to specify the time and force values, each file should contain one value per line:

    time.txt:

    .. code-block::

        0.0
        0.1
        0.2
        0.3
        0.4

    forces.txt:

    .. code-block::

        0.0
        0.5
        1.0
        0.5
        0.0

    The number of time points must match the number of force values.