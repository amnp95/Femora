PulseTrain
""""""""""""""""""""

The PulseTrain time series represents a sequence of pulses with specified timing and amplitude parameters.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **tStart**
      - Start time of pulse train (default: 0.0)
      - float
    * - **tEnd**
      - End time of pulse train (default: 1.0)
      - float
    * - **period**
      - Period between pulses (default: 1.0)
      - float
    * - **width**
      - Width of each pulse as a fraction of period (default: 0.5)
      - float
    * - **factor**
      - Amplitude of pulses (default: 1.0)
      - float
    * - **shift**
      - Phase shift of pulse train (default: 0.0)
      - float

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        
        ts_manager = TimeSeriesManager()
        
        # Create a pulse train with 0.2s period and 0.1s pulse width
        pulse_ts = ts_manager.create_time_series(
            'PulseTrain',
            tStart=0.0,
            tEnd=1.0,
            period=0.2,
            width=0.5,  # 50% duty cycle
            factor=1.0
        )

        # Via Femora
        import femora as fm
        
         
        pulse_ts = fm.timeSeries.create_time_series(
            'PulseTrain',
            tStart=0.0,
            tEnd=5.0,
            period=1.0,
            width=0.3,  # 30% duty cycle
            factor=2.0,
            shift=0.5  # Phase shift of 0.5 seconds
        )

.. admonition:: Mathematical Representation
    :class: info

    The pulse train time series generates rectangular pulses defined by:

    f(t) = factor  for t_n ≤ t ≤ t_n + width × period
    f(t) = 0       otherwise

    where t_n = tStart + n × period + shift, for n = 0, 1, 2, ... until tEnd