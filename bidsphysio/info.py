__version__ = "2.0"
__author__ = "Pablo Velasco"
__url__ = "https://github.com/cbinyu/bidsphysio"
__packagename__ = 'bidsphysio'
__description__ = "Physio-to-BIDS Converter"
__license__ = "MIT"
__longdesc__ = """Converts physio data from either CMRR DICOM or AcqKnowledge file to BIDS physiological recording."""

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Scientific/Engineering'
]

PYTHON_REQUIRES = ">=3.6"

REQUIRES = [
    'numpy >= 1.17.1',
    'pydicom >= 1.4.1',
    'bioread >= 1.0.4',
    'etelemetry',
]

TESTS_REQUIRES = [
]

EXTRA_REQUIRES = {
    'tests': TESTS_REQUIRES,
}

# Flatten the lists
EXTRA_REQUIRES['all'] = sum(EXTRA_REQUIRES.values(), [])