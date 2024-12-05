
# Supplementary Data and Analysis:
# One nest, two niches? Distribution of alimentary resources between an inquiline termite and its host.

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

To estimate standard errors and confidence intervals for the mean or median durations by activity type, we employed a bootstrap approach, as detailed below.
  - For a given activity type, let `D` represent the set of recorded activity durations, and let `n` denote the number of durations in `D`.
  - We generated `50,000` resampled lists `Di`​ (for `i=1,…,50,000`) by randomly selecting `n` durations from `D` with replacement.
  - The standard error for the mean or median was estimated as the standard deviation of the means or medians across the `50,000` resampled lists `Di`​.
  - The `95%` confidence interval was calculated as the range from the 2.5th to the 97.5th percentiles of the means or medians across the resampled lists.

## References

  [1] One nest, two niches? Distribution of alimentary resources between an inquiline termite and its host. Johanne Timmermans, Matsvei Tsishyn, Nicolas Fontaine and Yves Roisin.
