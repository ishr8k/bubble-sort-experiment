# Bubble Sort Experiment — Experimentation & Evaluation 2026, Assignment 1

This repository contains a reproducible experiment comparing the execution time of three Java bubble-sort implementations supplied with the assignment:

- `BubbleSortPassPerItem`
- `BubbleSortUntilNoChange`
- `BubbleSortWhileNeeded`

**Recommendation to Bubble Inc.:** Choose **`BubbleSortWhileNeeded`** among the three tested implementations. It had the lowest median time on every nearly sorted, random, and reversed condition, and matched or slightly improved on `UntilNoChange` for sorted inputs. These findings apply to the tested configurations and machine.

The three sorting classes and the `Sorter` interface were supplied for the assignment and used without modification. `Experiment.java` implements the measurements.

## Experimental design

- **Independent variables:** algorithm (3 levels), array size (`100`, `1000`, `10000`; 3 levels), and initial array order (`sorted`, `nearly_sorted`, `random`, `reversed`; 4 levels).
- **Dependent variable:** elapsed time of one `sort()` call, measured with `System.nanoTime()` (ratio scale, recorded in nanoseconds and reported in milliseconds).
- **Design:** 3 × 3 × 4 full factorial = **36 conditions**, with **30 measurements per condition**, for **1,080 measurements**.
- **Trial structure:** 12 size-by-order combinations × 30 repetitions = **360 matched-input trial blocks**. Within each block, all three algorithms sort their own copy of the same input array.
- **Order control:** trial blocks are shuffled; a 3 × 3 Latin square balances the three algorithms across the first, second, and third positions (each order appears ten times for every size-by-order combination).
- **Additional controls:** fixed input-generation rules, deterministic master seed (`20261110`), JIT warm-up before timing, fixed JVM settings, and an untimed ascending-order check after each sort.
- **Timing boundary:** only `sort()` is timed. Array generation, cloning, data recording, and correctness checks are excluded.

Input arrays contain distinct integers `0` through `n - 1`. Nearly sorted arrays are produced from sorted arrays by swapping `n / 20` randomly chosen pairs of different positions. The data should not be interpreted as covering every possible form of near-sortedness.

## Environment of the published measurements

The committed `data/raw_measurements.csv` was collected on **10 November 2026**, on the following computer:

| Component | Recorded configuration |
| --- | --- |
| Processor | Apple M3 Pro (11 logical processors) |
| Memory | 18 GiB |
| Operating system | macOS 26.0.1 (ARM64) |
| Java | Eclipse Temurin OpenJDK 25.0.2 |
| JVM arguments | `-Xms512m -Xmx512m -XX:+UseSerialGC` |
| Timer | `System.nanoTime()`; observed minimum nonzero increment: 41 ns |
| Master seed | `20261110` |

See `machine_details.txt` and `data/environment.txt` for machine-readable records. Absolute running times may differ on other hardware or during a new run.

## Repository contents

| Path | Description |
| --- | --- |
| `src/exp01/` | Assignment-provided algorithms and `Sorter` interface, plus `Experiment.java` measurement harness |
| `run_experiment.sh` | Compile and run the Java experiment with fixed JVM arguments |
| `analysis/analyze.py` | Descriptive statistics, approximate 95% confidence intervals, checks, and graphs |
| `data/raw_measurements.csv` | All 1,080 raw measurements (`time_ns`) and trial metadata |
| `data/environment.txt` | Recorded Java, OS, timer, seed, and run settings |
| `data/summary_statistics.csv` | Five-number summaries, means, standard deviations, and CIs for each condition |
| `data/analysis_output.txt` | Console output of the statistical analysis |
| `figures/fig1_design.png` | Experimental design diagram |
| `figures/fig2_boxplots.png` | Measurement distributions by condition |
| `figures/fig3_scaling.png` | Mean times across array sizes, with approximate 95% CIs |
| `machine_details.txt` | Mac hardware and Java versions |
| `requirements.txt` | Python analysis packages (names; versions not pinned) |

## Reproduce the analysis from the saved data

From the repository root, use Python 3 and install the dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
mkdir -p figures
python3 analysis/analyze.py
```

This regenerates `data/summary_statistics.csv` and `figures/*.png` from the committed raw CSV. To save the console output as well:

```sh
python3 analysis/analyze.py > data/analysis_output.txt 2>&1
```

The recorded measurements are **not** changed by the analysis step.

## Re-run the Java measurements (optional)

Java 17+ is required. Run from the repository root:

```sh
./run_experiment.sh
```

**Warning:** This regenerates and **overwrites** `data/raw_measurements.csv` and `data/environment.txt`. Make a backup or use a separate checkout if you want to preserve the submitted measurements. Re-running the program measures the current machine, so the times may differ from the published values.

## Interpretation and limitations

The result summaries use medians, five-number summaries, means and 95% confidence intervals as taught in the course. Confidence-interval overlap is a descriptive comparison, **not** a formal hypothesis test. Timings close to the timer's minimum observed increment (especially short sorted inputs) should be interpreted cautiously. The results were collected on one computer and with distinct `Integer` inputs only.

## Generative-AI assistance

Claude was used to guide the experiment workflow. ChatGPT was used to verify the recorded experimental steps against the supplied files and course material, and to assist with drafting, revising, and formatting the final report as a PDF. The recorded measurements came from a local run on the Mac described above; the Java sorting implementations were provided with the assignment.

