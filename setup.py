import setuptools

setuptools.setup(
    name="dunetoolkit",
    version="0.0.1",
    author="Elise Saxon",
    author_email="elise.saxon@pnnl.gov",
    maintainer="Chris Cacciatore",
    maintainer_email="christopher.cacciatore@pnnl.gov",
    description="A package that helps collaborators use the DUNE radiopurity database assistant",
    url="https://gitlab.pnnl.gov/dune/dune-collaborations/dune",
    package_data={'dunetoolkit':['synonyms.txt', 'units.csv', 'isotopes.csv']},
    packages=setuptools.find_packages(),
    license="BSD",
    python_requires='>=3.7',
    include_package_data=True,
    install_requires=[
        'jsonschema==3.2.0',
        'pymongo',
        'importlib'
    ],
)
