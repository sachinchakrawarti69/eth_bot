"""Model registry -- name -> module mapping."""

from __future__ import annotations
from importlib import import_module

_REGISTRY = {}


def register(name, module_path):
    """Register a predictor module by name."""
    _REGISTRY[name] = module_path


def get(name):
    """Return the module for a predictor."""
    if name not in _REGISTRY:
        raise KeyError("unknown predictor: " + name +
                       ". known: " + str(list(_REGISTRY)))
    return import_module(_REGISTRY[name])


def list_all():
    return list(_REGISTRY)


# -------- register predictors here --------
register("logistic",     "ml.predictors.logistic")
register("hmm",          "ml.predictors.hmm")
register("hmm_logistic", "ml.predictors.hmm_logistic")
register("naive_bayes",  "ml.predictors.naive_bayes")
