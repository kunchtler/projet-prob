from typing import Callable, TypeVar, Type
from inference import Prob, InferenceMethod, RejectionSampling, \
    ImportanceSampling, EnumerationSampling, MetropolisHastings

A = TypeVar('A')
B = TypeVar('B')

def rejsamp_test(model: Callable[[Prob, A], B], data: A, name: str,
                 shrink: bool = False,
                 plot_with_support: bool = False,
                 plot_style: str = 'scatter') \
                 -> None:
    print("-- {}, Basic Rejection Sampling --".format(name))
    rejsamp = RejectionSampling(model, data)
    dist = rejsamp.infer()
    if shrink:
        dist.shrink_support()
    supp = dist.get_support()
    assert (supp is not None)
    for i in range(len(supp.values)):
        print(f"{supp.values[i]} {supp.probs[i]}")
    dist.plot(plot_with_support=plot_with_support, plot_style=plot_style)


def impsamp_test(model: Callable[[Prob, A], B], data: A, name: str,
                 shrink: bool = False,
                 plot_with_support: bool = False,
                 plot_style: str = 'scatter') \
                 -> None:
    print("-- {}, Basic Importance Sampling --".format(name))
    impsamp = ImportanceSampling(model, data)
    dist = impsamp.infer()
    if shrink:
        dist.shrink_support()
    supp = dist.get_support()
    assert (supp is not None)
    for i in range(len(supp.values)):
        print(f"{supp.values[i]} {supp.probs[i]}")
    dist.plot(plot_with_support=plot_with_support, plot_style=plot_style)


def enumsamp_test(model: Callable[[Prob, A], B], data: A, name: str,
                  shrink: bool = False,
                  plot_with_support: bool = False,
                  plot_style: str = 'scatter') \
                  -> None:
    print("-- {}, Enumeration Sampling --".format(name))
    dist = EnumerationSampling.infer(model, data)
    if shrink:
        dist.shrink_support()
    supp = dist.get_support()
    assert (supp is not None)
    for i in range(len(supp.values)):
        print(f"{supp.values[i]} {supp.probs[i]}")
    dist.plot(plot_with_support=plot_with_support, plot_style=plot_style,
              model_name=name, method_name='Enumeration Sampling')


def mh_test(model: Callable[[Prob, A], B], data: A, name: str,
            shrink: bool = False,
            plot_with_support: bool = False,
            plot_style: str = 'scatter') \
            -> None:
    print("-- {}, Metropolis-Hastings --".format(name))
    mh = MetropolisHastings(model, data)
    dist = mh.infer()
    if shrink:
        dist.shrink_support()
    # supp = dist.get_support()
    # for i in range(len(supp.values)):
    #     print(f"{supp.values[i]} {supp.probs[i]}")
    dist.plot(plot_with_support=plot_with_support, plot_style=plot_style)


def test(model: Callable[[Prob, A], B], data: A, name: str,
         method: Type[InferenceMethod[A, B]] = ImportanceSampling,
         print_support: bool = False,
         shrink: bool = False,
         plot_with_support: bool = False,
         plot_style: str = 'scatter') \
         -> None:
    print("-- {}, {} --".format(name, method.name()))
    mh = method(model, data)
    dist = mh.infer()
    if shrink:
        dist.shrink_support()
    if print_support:
        supp = dist.get_support()
        assert (supp is not None)
        for i in range(len(supp.values)):
            print(f"{supp.values[i]} {supp.probs[i]}")
    dist.plot(plot_with_support=plot_with_support, plot_style=plot_style,
              model_name=name, method_name=method.name())
