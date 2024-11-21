
# Supplementary Data and Analysis: TITLE

## Description

Here are the supplementary data and the code for the statistical analysis of the publication [1] (2024) <LINK>.

**Authors**: Johanne Timmermans, Matsvei Tsishyn, Nicolas Fontaine, Yves Roisin

## Installation and Usage

- Install `python` version `3.9` or later.
- Install python packages `numpy` and `matplotlib` with `pip` (or `pip3` depending on your system):

```console
pip install numpy
pip install matplotlib
```

- From the root directory of this project, execute python scripts `generate_plot.py` and `generate_stats.py` with:

```console
python3 generate_plot.py
python3 generate_stats.py
```

## Content

- Folder `./data/`: contains all initial data measurements in `.csv` files.
- Folder `./fig/`: contains all generated figures by the project.
- Folder `./stats/`: contains all generated statistics by the project in `.csv` files.
- Files `generate_plot.py` and `generate_stats.py`: are the main scripts to generate all figures and statistics.
- Folder `./src/`: contains some python functions and classes thar are dependencies of the main scripts.
- Separator of all `.csv` files is `;`.

## Bootstrap method description

XXX.

## References

  [1] REFERENCE