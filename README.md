# Bubble Sort Experiment (Experimentation & Evaluation 2026, Assignment 1)

Experiment comparing the execution time of three bubble sort variants
(`BubbleSortUntilNoChange`, `BubbleSortWhileNeeded`, `BubbleSortPassPerItem`).
The three algorithm classes and the `Sorter` interface are the files provided with the assignment, unmodified.

## Design (summary)
* Independent variables (full factorial, 3 x 3 x 4 = 36 conditions):
  algorithm (3), input size n in {100, 1,000, 10,000}, initial order in {sorted, nearly sorted, random, reversed}.
* Dependent variable: execution time of `sort()` (`System.nanoTime()`, ratio scale; reported in ms).
* 30 repetitions per condition -> 360 trials, executed in random order; in each trial all three algorithms
  sort a copy of the same input array, in the order given by a 3 x 3 Latin square.
* JIT warm-up before measuring; results verified to be sorted after each (untimed) check.
* All randomness derives from one master seed (`20261110`).

## Contents
| Path | Description |
|---|---|
| `src/exp01/` | provided algorithms + `Sorter` + `Experiment.java` (measurement harness) |
| `run_experiment.sh` | compiles and runs the experiment (fixed JVM flags) |
| `analysis/analyze.py` | descriptive statistics, 95% confidence intervals, figures, hypothesis checks |
| `data/raw_measurements.csv` | all 1,080 raw measurements (`time_ns` in nanoseconds) |
| `data/environment.txt` | JVM / OS / hardware information recorded by the harness |
| `data/summary_statistics.csv` | five-number summary, mean, SD and 95% CI for each of the 36 conditions |
| `data/analysis_output.txt` | printed output of the analysis script |
| `figures/` | figures used in the report |

## Reproduce
```sh
./run_experiment.sh            # needs Java 17+ (JDK, or a JRE that ships the jdk.compiler module); ~2 minutes
pip install pandas numpy matplotlib seaborn
python3 analysis/analyze.py    # run from the project root
```
Absolute times depend on the machine; re-running on your own computer is encouraged
(note the machine in your report). The provided `data/` was produced on a 1-vCPU Linux virtual machine
(see `data/environment.txt`).

Note: a first execution of the harness was interrupted by the environment before it finished;
it was discarded and the experiment was rerun from scratch. Only the complete run is included.
