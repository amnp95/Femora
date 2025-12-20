Trig
""""""""""""""""""""""""""""

The Trig time series represents a trigonometric function (sine or cosine) with specified period, phase shift, and amplitude.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **trig_type**
      - Type of function ('Sine' or 'Cosine')
      - string
    * - **period**
      - Period of the function (required)
      - float
    * - **phase_shift**
      - Phase shift in radians (default: 0.0)
      - float
    * - **factor**
      - Amplitude of the function (default: 1.0)
      - float

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        
        ts_manager = TimeSeriesManager()
        
        # Create a sine wave with period 0.5s and amplitude 2.0
        sine_ts = ts_manager.create_time_series(
            'Trig',
            trig_type='Sine',
            period=0.5,
            phase_shift=0.0,
            factor=2.0
        )
        
        # Create a cosine wave with period 1.0s, phase shift π/4, and amplitude 0.5
        cosine_ts = ts_manager.create_time_series(
            'Trig',
            trig_type='Cosine',
            period=1.0,
            phase_shift=0.7853981634,  # π/4
            factor=0.5
        )

        # Via Femora
        import femora as fm
        import math
        
         
        trig_ts = fm.timeSeries.create_time_series(
            'Trig',
            trig_type='Sine',
            period=0.5,
            phase_shift=math.pi/6,  # 30 degrees
            factor=1.5
        )

.. admonition:: Mathematical Representation
    :class: info

    The trigonometric time series are defined by the following formulas:

    **Sine Function**:
    
    f(t) = factor × sin(2π × t/period + phase_shift)
    
    **Cosine Function**:
    
    f(t) = factor × cos(2π × t/period + phase_shift)
    
    where t is the time.