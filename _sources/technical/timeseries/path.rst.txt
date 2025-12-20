Path
"""""""""""""""""

The Path time series represents a time series defined by discrete points, either directly or from a file.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **dt**
      - Time increment for path points
      - float
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
        path_ts = ts_manager.create_time_series(
            'Path',
            dt=0.01,
            values=[0.0, 0.5, 1.0, 0.5, 0.0],
            factor=2.0
        )

        # Using a file
        path_ts = ts_manager.create_time_series(
            'Path',
            dt=0.01,
            filePath='data/forces.txt',
            factor=9.81,
            useLast=True
        )

        # Via Femora
        import femora as fm
        
         
        path_ts = fm.timeSeries.create_time_series(
            'Path',
            dt=0.02,
            filePath='acceleration.txt',
            factor=1.0,
            prependZero=True
        )

.. admonition:: File Format
    :class: info

    When using a file to specify the force values, the file should contain one value per line:

    .. code-block::

        0.0
        0.5
        1.0
        0.5
        0.0

    The time points will be generated using the specified dt value.