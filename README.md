[![Build Status](https://travis-ci.org/rosenbrockc/aflow.svg?branch=master)](https://travis-ci.org/rosenbrockc/aflow) [![Coverage Status](https://coveralls.io/repos/github/rosenbrockc/aflow/badge.svg?branch=master)](https://coveralls.io/github/rosenbrockc/aflow?branch=master)


# `AFLOW` Python API - *Patched*

**This repo is a forked version of [rosenbrockc/aflow](https://rosenbrockc.github.io/aflow/) for bug fix**

The patched Python API intends to have (almost) identical behavior with the
original `aflow`, while several functionalities are fixed:

1. Allow dynamic schema loading and keyword class creation. Can work
   with further versions of aflow without major modifications
2. More robust keyword casting for both string-type or converted inputs. 
3. Improved filter conditions, powered by boolean operations in `sympy`.
4. Better handling of aurl with multiple colons (e.g. GGA+U calculations)


For a list of examples in the patched API, please check the notebook in [notebooks/demo_patched_api.ipynb](notebooks/demo_patched_api.ipynb). 

To install:
```
pip install git+https://github.com/ulissigroup/aflow.git
```

---

# Descriptions for original aflow python API

Python API wrapping the AFLUX API language for AFLOW library. _Note:_ This is not an official repo of the AFLOW consortium and is not maintained by them. [API Documentation](https://rosenbrockc.github.io/aflow/).

If you use this package, please cite it:

```
@ARTICLE{2017arXiv171000813R,
   author = {{Rosenbrock}, C.~W.},
    title = "{A Practical Python API for Querying AFLOWLIB}",
  journal = {ArXiv e-prints},
archivePrefix = "arXiv",
   eprint = {1710.00813},
 primaryClass = "cs.DB",
 keywords = {Computer Science - Databases},
     year = 2017,
    month = sep,
   adsurl = {http://adsabs.harvard.edu/abs/2017arXiv171000813R},
  adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}
```

## Quickstart

Install `aflow` from the python package index:

```
pip install aflow
```

Or alternatively install `aflow` from conda using:

```
conda install -c conda-forge aflow
```

Open an ipython notebook or terminal and execute the query from the paper:

```python
from aflow import *

result = search(batch_size=20
        ).select(K.agl_thermal_conductivity_300K
        ).filter(K.Egap > 6).orderby(K.agl_thermal_conductivity_300K, True)

# Now, you can just iterate over the results.
for entry in result:
    print(entry.Egap)
```

`aflow` supports lazy evaluation. This means that if you didn't ask for a particular property during the initial query, you can just ask for it later and the request will happen transparently in the background.

# Python 2 Support

Although the package was originally designed to be compatible with both python 2 and python 3, python 2 has 
reached the end of its life. As such, we don't guarantee anymore that it will work.
