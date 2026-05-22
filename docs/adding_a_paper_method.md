# Adding A Paper Method

1. Pick the closest slot in `contracts/slots/`.
2. Create `experiments/<task>/<method_name>/`.
3. Add `README.md` using the required experiment section order.
4. Add `experiment.yaml` with Autoware-native input and output topics.
5. Add a launch file or write an explicit `launch.reason_not_needed`.
6. Add `params/default.yaml` if the method has parameters.
7. Run a smoke benchmark in shadow mode before proposing takeover mode.

Paper methods should add comparison value through benchmark results and failure analysis, not only source code.
