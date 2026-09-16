# Assessment of Stack Usage Estimation Using GCC for a Keil-Based Project

## 1. Purpose

The objective of this assessment is to evaluate the reliability of using GCC-generated stack usage information as an alternative method for estimating stack consumption in a project that is actually built using Keil ARM Compiler.

The production software is compiled using:

- Arm Compiler 5 (ARMCC, AC5)
- Arm Compiler 6 (ARMCLANG, AC6)

with optimization levels:

```text
-O2
or
-O3
```

However, neither AC5 nor AC6 provides a stack usage report mechanism equivalent to GCC's `.su` files generated through `-fstack-usage`.

Therefore, GCC is used as an analysis tool to generate:

```bash
-fstack-usage
-fcallgraph-info=su
```

and estimate stack usage at function level and call-chain level.

This document evaluates the possible discrepancies between the GCC analysis environment and the production build environment and assesses the confidence level of the obtained results.

---

# 2. Analysis Method

The stack analysis is performed using GCC with the following options:

```bash
-fstack-usage
-fcallgraph-info=su
```

These options generate:

- Function-level stack usage information (`.su` files).
- Call graph information.
- Function call dependencies required to estimate worst-case stack consumption.

The stack usage value reported in the `.su` file corresponds to the amount of stack allocated by the compiler for a specific function. GCC officially supports generation of stack usage reports for this purpose. 

---

# 3. Potential Differences Between GCC Analysis and Production Build

Although the same source code is compiled, several factors may result in differences between:

```text
Stack Usage Estimated by GCC
```

and

```text
Stack Usage in the Production Firmware
```

---

## 3.1 Compiler Backend Differences

The analysis environment uses:

```text
GCC
```

while the production firmware uses:

```text
ARM Compiler 5 (ARMCC)
ARM Compiler 6 (ARMCLANG)
```

Each compiler implements its own:

- Register allocation strategy.
- Instruction selection.
- Function frame generation.
- Optimization heuristics.
- Spill and reload algorithms.

Although all compilers conform to the ARM Procedure Call Standard (AAPCS), they are not required to generate identical machine code or identical stack frames. Consequently, stack usage may differ even when compiling the same source code. 【3-84b7df】【4-07b2f8】

### Impact

Typical differences include:

- Different numbers of saved registers.
- Different temporary variable placement.
- Different stack frame layouts.

As a result, individual function stack usage can differ by several bytes up to several tens of bytes depending on complexity.

---

## 3.2 Calling Convention and Register Saving

The ARM architecture follows the AAPCS specification defining:

- Argument passing.
- Return value handling.
- Register preservation rules.
- Stack behavior.

However, compilers remain free to choose different implementation strategies when deciding which registers to save and restore. This directly affects stack frame size. 【3-84b7df】【4-07b2f8】

Example:

```asm
push {r4-r7,lr}
```

versus

```asm
push {r4-r11,lr}
```

The second implementation consumes significantly more stack space.

Therefore, GCC and ARM Compiler may report different stack usage for the same function.

---

## 3.3 Optimization Level Difference

This is typically the largest source of discrepancy.

Current analysis configuration:

```text
GCC -O0
```

Production configuration:

```text
AC5 -O2 / -O3
AC6 -O2 / -O3
```

According to the official Arm Compiler User Guide Version 6.15:

> "Code size and stack usage are significantly higher at -O0 than at other optimization levels." 【5-745817】

The same document also states that optimization levels enable additional transformations that improve stack efficiency. 【5-745817】

### Impact

At O0:

- Most local variables remain on the stack.
- Very limited optimization is applied.
- Large stack frames are common.

At O2/O3:

- Variables may be kept in registers.
- Redundant variables can be eliminated.
- Stack allocation can be reduced.

As a result:

```text
Stack(O0) > Stack(O2/O3)
```

in many situations.

Therefore, GCC O0 often represents a conservative estimate rather than a realistic representation of release firmware.

---

## 3.4 Function Inlining

The Arm Compiler User Guide Version 6.13 states that Arm Compiler automatically performs function inlining at higher optimization levels when it improves performance. 【6-1ab717】

When a function is inlined:

```text
Caller
    -> Callee
```

becomes:

```text
Caller
```

The called function no longer exists as a separate stack frame.

### Impact

Consequences include:

- Reduced call depth.
- Reduced stack consumption.
- Different call graph structure.

Therefore, GCC O0 analysis may overestimate stack usage compared with AC5/AC6 release builds. 【6-1ab717】【5-745817】

---

## 3.5 Tail Call Optimization

The Arm Compiler User Guide Version 6.15 explicitly states that tail calls are enabled at optimized build levels. 【5-745817】

A statement such as:

```c
return func2();
```

can be transformed into a direct branch to `func2()`.

Instead of maintaining two stack frames:

```text
A -> B -> C
```

the compiler may remove one frame:

```text
A -> C
```

### Impact

This optimization can significantly reduce:

- Call depth.
- Worst-case stack usage.

Such behavior is generally absent or much less frequent at O0. 【5-745817】

---

## 3.6 Dead Code Elimination

Higher optimization levels allow the compiler to remove:

- Unused variables.
- Redundant calculations.
- Unreachable branches.
- Entire unused functions.

The Arm Compiler User Guide Version 6.15 notes that O0 generates substantially more code, including dead code, than optimized builds. 【5-745817】

### Impact

Stack space allocated for eliminated code no longer exists in the final executable.

This can further reduce actual stack usage compared to GCC O0 analysis.

---

## 3.7 Link-Time Optimization (LTO)

The Link Time Optimization in ARM Compiler 6 documentation explains that Arm Compiler 6 supports Link Time Optimization (LTO), allowing optimizations to occur at link time across compilation units. 【7-4fccf7】

Examples include:

- Cross-module inlining.
- Dead code elimination.
- Whole-program analysis.
- Additional optimization opportunities unavailable during individual compilation. 【7-4fccf7】

### Impact

LTO can further reduce stack usage and alter call-chain structure beyond what is visible in a standard GCC O0 build.

---

# 4. Why GCC O2/O3 Should Be Preferred

To reduce the gap between the analysis environment and the production environment, it is recommended to generate stack usage data using optimization levels similar to the production firmware:

```bash
arm-none-eabi-gcc \
-O2 \
-fstack-usage \
-fcallgraph-info=su
```

or

```bash
arm-none-eabi-gcc \
-O3 \
-fstack-usage \
-fcallgraph-info=su
```

Advantages:

- Function inlining behavior closer to production.
- Tail-call optimization closer to production.
- More realistic register allocation.
- More representative call graph.
- Reduced pessimism compared with O0.

Although GCC and Arm Compiler will never generate identical binaries, using O2/O3 significantly improves correlation with the production build.

---

# 5. Reliability Assessment

## GCC O0

### Advantages

- Easy to generate.
- Conservative estimation.
- Useful for identifying stack-intensive functions.

### Limitations

- Poor correlation with release firmware.
- Different call graph.
- Excessive stack allocation due to lack of optimization.

### Estimated Confidence

```text
60% - 75%
```

---

## GCC O2

### Advantages

- Closer to production behavior.
- Similar optimization philosophy.
- Better call graph representation.

### Estimated Confidence

```text
80% - 90%
```

---

## GCC O3

### Advantages

- Closest approximation when production firmware uses O3.
- Similar optimization opportunities.
- Better representation of release code.

### Estimated Confidence

```text
80% - 95%
```

---

## Runtime Measurement on Production Firmware

Methods such as:

- Stack watermarking.
- Stack painting.
- Runtime monitoring.

provide the most representative measurement because they observe the actual executable running on the target.

### Estimated Confidence

```text
>95%
```

However, they usually require additional instrumentation and test coverage to capture worst-case scenarios.

---

# 6. Conclusion

Because Arm Compiler 5 and Arm Compiler 6 do not provide a stack usage reporting mechanism equivalent to GCC `.su` files, GCC-based analysis represents a practical and technically justified alternative for stack usage estimation. 【1-3785bc】【2-000222】

The primary sources of discrepancy between GCC-generated stack usage and production firmware stack usage arise from:

- Compiler implementation differences.
- Register allocation strategies.
- Function inlining.
- Tail-call optimization.
- Dead code elimination.
- Link-Time Optimization.
- Optimization level mismatch. 【5-745817】【6-1ab717】【7-4fccf7】【3-84b7df】

Using:

```text
GCC -O0
```

typically produces conservative results but may significantly overestimate actual stack consumption.

Using:

```text
GCC -O2
or
GCC -O3
```

provides a much closer approximation to production firmware built using AC5/AC6 at equivalent optimization levels.

Therefore, for the purpose of:

- Worst-case stack estimation,
- Stack sizing,
- Static analysis,
- Safety assessment,
- Software architecture review,

the recommended approach is:

```bash
arm-none-eabi-gcc \
-O2 \
-fstack-usage \
-fcallgraph-info=su
```

or

```bash
arm-none-eabi-gcc \
-O3 \
-fstack-usage \
-fcallgraph-info=su
```

The resulting stack analysis should be considered a high-confidence engineering estimate rather than an exact replication of stack consumption in the final AC5/AC6 binary.

---

# 7. References

[1] GCC Online Documentation, GNU Project.  
https://gcc.gnu.org/onlinedocs/  
Accessed: 15-Sep-2026. 【1-3785bc】【2-000222】

[2] Arm Compiler User Guide Version 6.15, Arm Ltd., "Selecting Optimization Options".  
https://support.arm.com/documentation/100748/0615/Using-Common-Compiler-Options/Selecting-optimization-options  
Accessed: 15-Sep-2026. 【5-745817】

[3] Arm Compiler User Guide Version 6.13, Arm Ltd., "Inlining Functions".  
https://support.arm.com/documentation/100748/0613/writing-optimized-code/inlining-functions  
Accessed: 15-Sep-2026. 【6-1ab717】

[4] Link Time Optimization in ARM Compiler 6, Arm Developer Community.  
https://developer.arm.com/community/arm-community-blogs/b/tools-software-ides-blog/posts/link-time-optimization-in-arm-compiler-6  
Accessed: 15-Sep-2026. 【7-4fccf7】

[5] Procedure Call Standard for the ARM Architecture (AAPCS), ARM IHI 0042D.  
https://www.eecs.umich.edu/courses/eecs373/readings/ARM-AAPCS-EABI-v2.08.pdf  
Accessed: 15-Sep-2026. 【3-84b7df】

[6] Application Binary Interface for the Arm Architecture (ABI-AA), ARM Software.  
https://github.com/ARM-software/abi-aa  
Accessed: 15-Sep-2026. 【4-07b2f8】