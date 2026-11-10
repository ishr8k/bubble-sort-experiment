package exp01;

import java.io.IOException;
import java.io.PrintWriter;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Measurement infrastructure for Assignment 1 (The Bubble Algorithm Library).
 *
 * <h2>Design</h2>
 * Full factorial design with three independent variables (factors):
 * <ul>
 *   <li>algorithm: UntilNoChange, WhileNeeded, PassPerItem (3 levels)</li>
 *   <li>input size: 100, 1,000, 10,000 elements (3 levels)</li>
 *   <li>initial order of the input: random, sorted, reversed, nearly_sorted (4 levels)</li>
 * </ul>
 * Dependent variable: execution time of {@code sort()} in nanoseconds (ratio scale).
 *
 * <h2>Procedure</h2>
 * <ol>
 *   <li>Warm-up phase (results discarded) so the JIT compiler has compiled all three algorithms
 *       for all input conditions before the first measurement.</li>
 *   <li>Measurement phase: 12 input conditions (size x order) x 30 repetitions = 360 trials.
 *       The 360 trials are executed in a random order (randomization against time threats).</li>
 *   <li>Within a trial, one input array is generated and every algorithm sorts its own copy of
 *       that same array (within-subjects design: same experimental material for all levels).
 *       The order of the three algorithms follows a 3x3 Latin square to counterbalance order
 *       effects.</li>
 *   <li>Only the call to {@code sort()} is timed with {@code System.nanoTime()}. Copying the
 *       input and verifying the result happen outside the timed region.</li>
 * </ol>
 *
 * Usage: {@code java exp01.Experiment [outputDirectory]} (default output directory: "data").
 */
public final class Experiment {

	// ---------------------------------------------------------------- design constants

	static final int[] SIZES = { 100, 1_000, 10_000 };
	static final String[] ORDERS = { "random", "sorted", "reversed", "nearly_sorted" };
	static final String[] ALGORITHM_NAMES = { "UntilNoChange", "WhileNeeded", "PassPerItem" };

	/** Number of repetitions (independent input arrays) per input condition. */
	static final int REPETITIONS = 30;

	/** Warm-up invocations per (algorithm, order) -- more for small sizes, which run only for microseconds. */
	static final int[] WARMUP_INVOCATIONS = { 500, 50, 3 };

	/** Fraction of positions that are randomly swapped to create a "nearly sorted" input (1/20 = 5%). */
	static final int NEARLY_SORTED_SWAP_DIVISOR = 20;

	/** Master seed: all randomness (inputs, trial order) is derived from it, so the experiment is repeatable. */
	static final long MASTER_SEED = 20261110L;

	/** Cyclic 3x3 Latin square: each algorithm occurs exactly once in every position (row = sequence). */
	static final int[][] LATIN_SQUARE = { { 0, 1, 2 }, { 1, 2, 0 }, { 2, 0, 1 } };

	// ---------------------------------------------------------------- helpers

	private static Sorter<Integer> newSorter(final int algorithm) {
		switch (algorithm) {
			case 0:
				return new BubbleSortUntilNoChange<Integer>();
			case 1:
				return new BubbleSortWhileNeeded<Integer>();
			case 2:
				return new BubbleSortPassPerItem<Integer>();
			default:
				throw new IllegalArgumentException("unknown algorithm " + algorithm);
		}
	}

	/**
	 * Generates the input array for a given order. Values are the distinct integers 0..n-1.
	 * <ul>
	 *   <li>random: uniformly random permutation (Fisher-Yates)</li>
	 *   <li>sorted: 0, 1, ..., n-1</li>
	 *   <li>reversed: n-1, ..., 1, 0</li>
	 *   <li>nearly_sorted: sorted array in which n/20 random pairs of positions have been swapped</li>
	 * </ul>
	 */
	static Integer[] generateInput(final String order, final int n, final long seed) {
		final Random rnd = new Random(seed);
		final Integer[] a = new Integer[n];
		switch (order) {
			case "random":
				for (int i = 0; i < n; i++) {
					a[i] = i;
				}
				for (int i = n - 1; i > 0; i--) {
					swap(a, i, rnd.nextInt(i + 1));
				}
				break;
			case "sorted":
				for (int i = 0; i < n; i++) {
					a[i] = i;
				}
				break;
			case "reversed":
				for (int i = 0; i < n; i++) {
					a[i] = n - 1 - i;
				}
				break;
			case "nearly_sorted":
				for (int i = 0; i < n; i++) {
					a[i] = i;
				}
				final int swaps = Math.max(1, n / NEARLY_SORTED_SWAP_DIVISOR);
				for (int s = 0; s < swaps; s++) {
					final int i = rnd.nextInt(n);
					int j = rnd.nextInt(n);
					while (j == i) {
						j = rnd.nextInt(n);
					}
					swap(a, i, j);
				}
				break;
			default:
				throw new IllegalArgumentException("unknown order " + order);
		}
		return a;
	}

	private static void swap(final Integer[] a, final int i, final int j) {
		final Integer t = a[i];
		a[i] = a[j];
		a[j] = t;
	}

	private static long seedFor(final int sizeIdx, final int orderIdx, final int repetition) {
		return MASTER_SEED * 1_000_003L + sizeIdx * 100_003L + orderIdx * 1_009L + repetition;
	}

	/** Times a single call of sort(). Only this method's body is inside the measured interval. */
	private static long timeSort(final Sorter<Integer> sorter, final Integer[] data) {
		final long start = System.nanoTime();
		sorter.sort(data);
		final long end = System.nanoTime();
		return end - start;
	}

	private static void assertSorted(final Integer[] a, final String context) {
		for (int i = 0; i < a.length - 1; i++) {
			if (a[i].compareTo(a[i + 1]) > 0) {
				throw new IllegalStateException("Result not sorted: " + context);
			}
		}
	}

	/** Smallest non-zero difference between consecutive nanoTime() readings (timer granularity). */
	private static long estimateTimerResolution() {
		long min = Long.MAX_VALUE;
		for (int k = 0; k < 100_000; k++) {
			final long a = System.nanoTime();
			final long b = System.nanoTime();
			if (b > a && b - a < min) {
				min = b - a;
			}
		}
		return min;
	}

	// ---------------------------------------------------------------- phases

	private static void warmUp() {
		System.out.println("Warm-up phase ...");
		for (int s = 0; s < SIZES.length; s++) {
			for (int o = 0; o < ORDERS.length; o++) {
				for (int a = 0; a < ALGORITHM_NAMES.length; a++) {
					final Sorter<Integer> sorter = newSorter(a);
					for (int k = 0; k < WARMUP_INVOCATIONS[s]; k++) {
						// seeds of the warm-up inputs differ from all measured inputs
						final Integer[] data = generateInput(ORDERS[o], SIZES[s], seedFor(s, o, 1_000 + k));
						sorter.sort(data);
					}
				}
			}
		}
	}

	/** One (condition, repetition) pair. */
	private static final class Trial {
		final int sizeIdx;
		final int orderIdx;
		final int repetition;

		Trial(final int sizeIdx, final int orderIdx, final int repetition) {
			this.sizeIdx = sizeIdx;
			this.orderIdx = orderIdx;
			this.repetition = repetition;
		}
	}

	private static void measure(final Path csv) throws IOException {
		final List<Trial> trials = new ArrayList<>();
		for (int s = 0; s < SIZES.length; s++) {
			for (int o = 0; o < ORDERS.length; o++) {
				for (int r = 0; r < REPETITIONS; r++) {
					trials.add(new Trial(s, o, r));
				}
			}
		}
		// Randomization: trials of all conditions are interleaved in random order.
		Collections.shuffle(trials, new Random(MASTER_SEED));

		System.out.println("Measurement phase: " + trials.size() + " trials ...");
		try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(csv, StandardCharsets.UTF_8))) {
			out.println("trial,size,order,repetition,algorithm,position,latin_row,time_ns");
			int trialNo = 0;
			for (final Trial t : trials) {
				trialNo++;
				final int size = SIZES[t.sizeIdx];
				final String order = ORDERS[t.orderIdx];
				final Integer[] input = generateInput(order, size, seedFor(t.sizeIdx, t.orderIdx, t.repetition));
				// Each Latin-square row is used equally often (10 times) within a condition.
				final int latinRow = t.repetition % LATIN_SQUARE.length;
				final int[] sequence = LATIN_SQUARE[latinRow];

				for (int position = 0; position < sequence.length; position++) {
					final int algorithm = sequence[position];
					final Integer[] copy = input.clone(); // fresh, identical input for every algorithm
					final long ns = timeSort(newSorter(algorithm), copy);
					assertSorted(copy, ALGORITHM_NAMES[algorithm] + " " + order + " " + size);
					out.println(trialNo + "," + size + "," + order + "," + t.repetition + ","
							+ ALGORITHM_NAMES[algorithm] + "," + (position + 1) + "," + (latinRow + 1) + "," + ns);
				}
				if (trialNo % 60 == 0) {
					System.out.println("  " + trialNo + "/" + trials.size() + " trials done");
				}
			}
		}
	}

	private static void writeEnvironment(final Path file) throws IOException {
		final List<String> lines = new ArrayList<>();
		lines.add("java.version=" + System.getProperty("java.version"));
		lines.add("java.vm.name=" + System.getProperty("java.vm.name"));
		lines.add("java.vendor=" + System.getProperty("java.vendor"));
		lines.add("os.name=" + System.getProperty("os.name"));
		lines.add("os.version=" + System.getProperty("os.version"));
		lines.add("os.arch=" + System.getProperty("os.arch"));
		lines.add("availableProcessors=" + Runtime.getRuntime().availableProcessors());
		lines.add("maxHeapMB=" + Runtime.getRuntime().maxMemory() / (1024 * 1024));
		lines.add("jvmArguments=" + ManagementFactory.getRuntimeMXBean().getInputArguments());
		lines.add("nanoTimeResolutionNs=" + estimateTimerResolution());
		lines.add("masterSeed=" + MASTER_SEED);
		lines.add("repetitionsPerCondition=" + REPETITIONS);
		Files.write(file, lines, StandardCharsets.UTF_8);
	}

	public static void main(final String[] args) throws IOException {
		final Path dir = Paths.get(args.length > 0 ? args[0] : "data");
		Files.createDirectories(dir);
		writeEnvironment(dir.resolve("environment.txt"));
		warmUp();
		measure(dir.resolve("raw_measurements.csv"));
		System.out.println("Done. Data written to " + dir.toAbsolutePath());
	}
}
