#!/bin/sh
# Compiles and runs the experiment. Requires a JDK (javac) or a JRE that ships the jdk.compiler module.
set -e
cd "$(dirname "$0")"
mkdir -p out data
java -m jdk.compiler/com.sun.tools.javac.Main -d out src/exp01/*.java
# Fixed JVM settings = control variables (heap size, garbage collector).
java -Xms512m -Xmx512m -XX:+UseSerialGC -cp out exp01.Experiment data
