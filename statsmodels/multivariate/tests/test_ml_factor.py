import numpy as np
from statsmodels.multivariate.factor import Factor
from numpy.testing import assert_allclose, assert_equal
from scipy.optimize import approx_fprime


# A small model for basic testing
def _toy():
    uniq = np.r_[4, 9, 16]
    load = np.asarray([[3, 1, 2], [2, 5, 8]]).T
    par = np.r_[2, 3, 4, 3, 1, 2, 2, 5, 8]
    corr = np.asarray([[1, .5, .25], [.5, 1, .5], [.25, .5, 1]])
    return uniq, load, corr, par


def test_loglike():

    uniq, load, corr, par = _toy()
    fa = Factor(n_factor=2, corr=corr)

    # Two ways of passing the parameters to loglike
    ll1 = fa.loglike((load, uniq))
    ll2 = fa.loglike(par)

    assert_allclose(ll1, ll2)


def test_score():

    uniq, load, corr, par = _toy()
    fa = Factor(n_factor=2, corr=corr)

    def f(par):
        return fa.loglike(par)

    par2 = np.r_[0.1, 0.2, 0.3, 0.4, 0.3, 0.1, 0.2, -0.2, 0, 0.8, 0.5, 0]

    for pt in (par, par2):
        g1 = approx_fprime(pt, f, 1e-8)
        g2 = fa.score(pt)
        assert_allclose(g1, g2, atol=1e-3)


def test_exact():
    # Test if we can recover exact factor-structured matrices with
    # default starting values.

    np.random.seed(23324)

    # Works for larger k_var but slow for routine testing.
    for k_var in 5, 10, 25:
        for n_factor in 1, 2, 3:
            load = np.random.normal(size=(k_var, n_factor))
            uniq = np.linspace(1, 2, k_var)
            c = np.dot(load, load.T)
            c.flat[::c.shape[0]+1] += uniq
            s = np.sqrt(np.diag(c))
            c /= np.outer(s, s)
            fa = Factor(corr=c, n_factor=n_factor, method='ml')
            rslt = fa.fit()
            assert_allclose(rslt.fitted_cov, c, rtol=1e-4, atol=1e-4)
            rslt.summary()  # smoke test


def test_1factor():
    """
    # R code:
    r = 0.4
    p = 4
    ii = seq(0, p-1)
    ii = outer(ii, ii, "-")
    ii = abs(ii)
    cm = r^ii
    factanal(covmat=cm, factors=1)
    """

    r = 0.4
    p = 4
    ii = np.arange(p)
    cm = r ** np.abs(np.subtract.outer(ii, ii))

    fa = Factor(corr=cm, n_factor=1, method='ml')
    rslt = fa.fit()

    if rslt.loadings[0, 0] < 0:
        rslt.loadings[:, 0] *= -1

    load = np.r_[0.401, 0.646, 0.646, 0.401]
    uniq = np.r_[0.839, 0.582, 0.582, 0.839]
    assert_allclose(load, rslt.loadings[:, 0], rtol=1e-3, atol=1e-3)
    assert_allclose(uniq, rslt.uniqueness, rtol=1e-3, atol=1e-3)

    assert_equal(rslt.df, 2)


def test_2factor():
    """
    # R code:
    r = 0.4
    p = 6
    ii = seq(0, p-1)
    ii = outer(ii, ii, "-")
    ii = abs(ii)
    cm = r^ii
    factanal(covmat=cm, factors=2)
    """

    r = 0.4
    p = 6
    ii = np.arange(p)
    cm = r ** np.abs(np.subtract.outer(ii, ii))

    fa = Factor(corr=cm, n_factor=2, nobs=100, method='ml')
    rslt = fa.fit()

    for j in 0, 1:
        if rslt.loadings[0, j] < 0:
            rslt.loadings[:, j] *= -1

    uniq = np.r_[0.782, 0.367, 0.696, 0.696, 0.367, 0.782]
    assert_allclose(uniq, rslt.uniqueness, rtol=1e-3, atol=1e-3)

    loads = [np.r_[0.323, 0.586, 0.519, 0.519, 0.586, 0.323],
             np.r_[0.337, 0.538, 0.187, -0.187, -0.538, -0.337]]
    for k in 0, 1:
        if np.dot(loads[k], rslt.loadings[:, k]) < 0:
            loads[k] *= -1
        assert_allclose(loads[k], rslt.loadings[:, k], rtol=1e-3, atol=1e-3)

    assert_equal(rslt.df, 4)

    # Smoke test for standard errors
    e = np.asarray([0.11056836, 0.05191071, 0.09836349, 0.09836349, 0.05191071, 0.11056836])
    assert_allclose(rslt.uniq_stderr, e, atol=1e-4)
    e = np.asarray([[0.08842151, 0.08842151], [0.06058582, 0.06058582], [0.08339874, 0.08339874],
                    [0.08339874, 0.08339874], [0.06058582, 0.06058582], [0.08842151, 0.08842151]])
    assert_allclose(rslt.load_stderr, e, atol=1e-4)
