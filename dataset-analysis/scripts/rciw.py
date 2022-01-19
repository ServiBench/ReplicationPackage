# Imports
from statistics import variance
from scipy.stats import norm
from scipy.stats.mstats import mjci, hdquantiles

# Statistics helper
# laaber:21 "Predicting unstable software benchmarks using static source code features"
# See 4.4.2 Variability Measure > Maritz-Jarrett Confidence Interval of the Median Estimation
# Source: https://github.com/sealuzh/benchmark-instability-prediction-replication-package/blob/51d55bbc91fe0084860081cf627e0c81b9732c4c/approach/BenchmarkVariabilities/calculation.py#L105
def calculate_RCIW_MJ_HD(data, prob = 0.5, alpha = 0.01, axis = None):
    """
    Computes the alpha confidence interval for the selected quantiles of the data, with Maritz-Jarrett estimators.
    :param prob:
    :param alpha:
    :param axis:
    :return:
    """
    if len(data) < 2:
        return -1
    
    if variance(data) == 0.0:
        return 0.0
    
    alpha = min(alpha, 1 - alpha)
    z = norm.ppf(1 - alpha/2.)
    xq = hdquantiles(data, prob, axis=axis)
    med = round(xq[0], 5)
    if med == 0:
        return 0.0

    smj = 0.0

    try:
        smj = mjci(data, prob, axis=axis)
    except:
        return 0.0

    ci_bounds = (xq - z * smj, xq + z * smj)
    ci_lower = ci_bounds[0][0]
    ci_lower = 0 if ci_lower < 0 else ci_lower
    ci_upper = ci_bounds[1][0]
    ci_upper = 0 if ci_upper < 0 else ci_upper

    rciw = ((ci_upper - ci_lower) / med) * 100
    
    return rciw
