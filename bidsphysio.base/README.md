# bidsphysio.base
Base classes for BIDS Physiology

[![Docker image](https://img.shields.io/badge/docker-cbinyu/bidsphysio:latest-brightgreen.svg?logo=docker&style=flat)](https://hub.docker.com/r/cbinyu/bidsphysio/tags/)
[![TravisCI](https://travis-ci.com/cbinyu/bidsphysio.svg?branch=master)](https://travis-ci.com/cbinyu/bidsphysio)
[![CodeCoverage](https://codecov.io/gh/cbinyu/bidsphysio/branch/master/graph/badge.svg)](https://codecov.io/gh/cbinyu/bidsphysio)
[![DOI](https://zenodo.org/badge/239006399.svg)](https://zenodo.org/badge/latestdoi/239006399)

## Installation
You can install the base class from PyPI with `pip`:

```
pip install bidsphysio.base
```

## How to use in your own Python program
After installing the module using `pip` (see [above](https://github.com/cbinyu/bidsphysio#installation "Installation") ), you can use it in your own Python program this way:
```
from bidsphysio.base.bidsphysio import (physiosignal,
                                        physiodata)

mySignal = physiosignal()
```
or:
```
from bidsphysio import acq2bidsphysio
acq2bidsphysio.acq2bids( [acq_files],    prefix )
```
or:
```
from bidsphysio import pmu2bidsphysio
pmu2bidsphysio.pmu2bids( [pmu_files], prefix )
```

