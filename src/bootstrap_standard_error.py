
# Imports ----------------------------------------------------------------------
import numpy as np
from typing import Callable

# Main -------------------------------------------------------------------------
def bootstrap_standard_error(arr: np.ndarray, measure_function: Callable):
    """
    Returns the Standard Error on Measure and the [2.5, 97.5] CI of the <measure_function> on <arr>.
    """

    # Init
    CI_RANGE = [2.5, 97.5]
    N_REPEATS = 50000
    bootstrap_measures = []
    
    # Repeats measurements on samples
    for i in range(N_REPEATS):
        # Sample with replacement from the original data
        sample = np.random.choice(arr, size=len(arr), replace=True)
        measure = measure_function(sample)
        bootstrap_measures.append(measure)

    # Compute stats
    SE = np.std(bootstrap_measures) # Standard Error on Measure (mean, median, ...)
    # Compute the 2.5th and 97.5th percentiles (Containing 95% of all data)
    CI = np.percentile(bootstrap_measures, CI_RANGE)
    return SE, CI
