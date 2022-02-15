from typing import List, Tuple, Callable, TypeVar, Optional, Generic
from typing_extensions import Protocol
import scipy.stats as sp
import math
from math import log, comb, inf
import utils
import matplotlib.pyplot as plt

_A = TypeVar('_A')
_C = TypeVar('_C')


class CallableProtocol(Protocol[_C]):
    __call__: _C


class Support(Generic[_A]):
    values: List[_A]
    logits: List[float]
    probs: List[float]

    def __init__(self, values: List[_A], logits: List[float],
                 probs: List[float]):
        self.values = values
        self.logits = logits
        self.probs = probs

    def __iter__(self) -> List[Tuple[_A, float, float]]:
        return list(zip(self.values, self.logits, self.probs))


class Distrib(Generic[_A]):
    _sample: CallableProtocol[Callable[[], _A]]
    _logpdf: CallableProtocol[Callable[[_A], float]]
    mean: Optional[Callable[[], _A]]
    var: Optional[Callable[[], float]]
    _samples: Optional[List[_A]]
    _support: Optional[Support[_A]]
    _n: int

    def __init__(self, sample: Callable[[], _A], logpdf: Callable[[_A], float],
                 mean: Optional[Callable[[], _A]] = None,
                 var: Optional[Callable[[], float]] = None,
                 support: Optional[Support[_A]] = None,
                 n: int = 10000):
        self._n = n
        self._sample = sample
        self._logpdf = logpdf
        self.mean = mean
        self.var = var
        self._samples = None
        self._support = support

    def draw(self) -> _A:
        return self._sample()

    def get_samples(self) -> List[_A]:
        if self._samples is not None:
            return self._samples
        else:
            samples = [self._sample() for i in range(self._n)]
            self._samples = samples
            return samples

    def get_support(self, shrink: bool = False) -> Optional[Support[_A]]:
        if not shrink:
            return self._support
        else:
            assert (self._support is not None)
            values = self._support.values
            probs = self._support.probs
            values, probs = utils.shrink(values, probs)
            return Support(values, [math.log(x) if x != 0. else -float('inf')
                                    for x in probs], probs)

    def logpdf(self, x: _A) -> float:
        return self._logpdf(x)

    def shrink_support(self) -> None:
        if self._support is not None:
            values = self._support.values
            probs = self._support.probs
            values, probs = utils.shrink(values, probs)
            self._support = Support(values,
                                    [math.log(x) if x != 0. else -float('inf')
                                     for x in probs], probs)

    def plot(self, plot_with_support: bool = False,
             plot_style: str = 'scatter',
             model_name: str = "", method_name: str = "") -> None:
        if plot_with_support:
            if self._support is None:
                print("Pas de support à plot")
                return
            supp = self.get_support()
            assert(isinstance(supp, Support))
            if plot_style == 'bar':
                plt.bar(supp.values, supp.probs, width=0.05)
            elif plot_style == 'scatter':
                plt.scatter(supp.values, supp.probs)
                plot_y_size = max(supp.probs)
                plt.ylim((-plot_y_size*1/20, plot_y_size*21/20))
            elif plot_style == 'line':
                plt.plot(*zip(*sorted(zip(supp.values, supp.probs))))
                plot_y_size = max(supp.probs)
                plt.ylim((-plot_y_size*1/20, plot_y_size*21/20))
            else:
                print("L'argument plot_style est invalide. Il doit être "\
                      "'bar', 'scatter', ou 'line'")
                return
        else:
            plt.hist(self.get_samples(), 100)
        plt.title(f"{model_name} - {method_name}")
        plt.grid(True)
        plt.show()


def bernoulli(p: float) -> Distrib[int]:
    assert(0 <= p <= 1)
    sample  = lambda: sp.bernoulli.rvs(p)
    logpdf  = lambda x: sp.bernoulli.logpmf(x, p)
    mean    = lambda: sp.bernoulli.mean(p)
    var     = lambda: sp.bernoulli.var(p)
    if p == 0:
        logits = [-float('inf'), 0]
    elif p == 1:
        logits = [0, -float('inf')]
    else:
        logits = [log(1.-p), log(p)]
    support = Support([0, 1], logits, [1.-p, p])
    return Distrib(sample, logpdf, mean, var, support)


def binomial(p: float, n: int) -> Distrib[int]:
    assert(0 <= p <= 1 and 0 <= n)
    sample  = lambda: sp.binom.rvs(n, p)
    logpdf  = lambda x: sp.binom.logpmf(x, n, p)
    mean    = lambda: sp.binom.mean(n, p)
    var     = lambda: sp.binom.var(n, p)
    #If n is too big, it takes too much time to compute all comb(n,k)
    if n < 500:
        support_values = list(range(n+1))
        all_combs = [comb(n, k) for k in support_values]
        sum_combs = sum(all_combs)
        support_probs = [elem / sum_combs for elem in all_combs]
        support_logits = [log(x) for x in support_probs]
        support = Support(support_values, support_logits, support_probs)
    else:
        support = None
    return Distrib(sample, logpdf, mean, var, support)


def dirac(v: _A) -> Distrib[_A]:
    sample = lambda: v
    logpdf = lambda x: 0. if x == v else -inf
    mean   = lambda: v
    var    = lambda: 0.
    return Distrib(sample, logpdf, mean, var)


def support(values: List[_A], logits: List[float]) -> Distrib[_A]:
    assert(len(values) == len(logits))
    probs = utils.normalize(logits)
    sp_distrib = sp.rv_discrete(values=(range(len(values)), probs))
    sample  = lambda: values[sp_distrib.rvs()]
    logpdf  = lambda x: utils.findprob(values, probs, x)
    try:
        # if values support product with a floatting number
        _mean = sum(values[i] * probs[i] for i in range(len(values)))  # type: ignore
        _var = sum((values[i] - _mean)**2 for i in range(len(values))) / len(probs)  # type: ignore
    except TypeError:
        # otherwise, we cannot compute mean and variance
        _mean = None
        _var = None
    mean    = lambda: _mean
    var     = lambda: _var
    support = Support(values, logits, probs)
    # return Distrib(sample, logpdf, support)  # type: ignore
    return Distrib(sample, logpdf, mean, var, support)  # type: ignore


def uniform_support(values: List[_A]) -> Distrib[_A]:
    logits = [0.]*len(values)
    return support(values, logits)


def beta(a: float, b: float) -> Distrib[float]:
    assert(a > 0. and b > 0.)
    sample  = lambda: sp.beta.rvs(a, b)
    logpdf  = lambda x: sp.beta.logpdf(x, a, b)
    mean    = lambda: sp.beta.mean(a, b)
    var     = lambda: sp.beta.var(a, b)
    return Distrib(sample, logpdf, mean, var)


def gaussian(mu: float, sigma: float) -> Distrib[float]:
    assert(0. < sigma)
    sample  = lambda: sp.norm.rvs(loc=mu, scale=sigma)
    logpdf  = lambda x: sp.norm.logpdf(x, loc=mu, scale=sigma)
    mean    = lambda: sp.norm.mean(loc=mu, scale=sigma)
    var     = lambda: sp.norm.var(loc=mu, scale=sigma)
    return Distrib(sample, logpdf, mean, var)


def uniform(a: float, b: float) -> Distrib[float]:
    assert(a <= b)
    #scipy.stats.uniform(loc=0, scale=1) tire selon une loi uniforme
    #dans l'intervalle [loc, loc+scale]
    loc = a
    scale = b-a
    sample  = lambda: sp.uniform.rvs(loc=loc, scale=scale)
    logpdf  = lambda x: sp.uniform.logpdf(x, loc=loc, scale=scale)
    mean    = lambda: sp.uniform.mean(loc=loc, scale=scale)
    var     = lambda: sp.uniform.var(loc=loc, scale=scale)
    return Distrib(sample, logpdf, mean, var)


if __name__ == '__main__':
    '''p = 0.5
    x1 = bernoulli(p)
    x2 = binomial(p, 3)
    x3 = dirac(3)
    x4 = beta(2, 5)
    x5 = gaussian(0, 1)
    x6 = uniform(0, 2)'''
    logits = [log(2), log(3), log(5)]
    values = [0, 1, 3]
    y = support(values, logits)
    y.plot()
    print('main')
