# 06 — Model Evaluation and Generalization

[Foundations](README.md) | [Previous: Dataset design](05-dataset-design.md) | [Next: Inference and deployment](07-inference-and-deployment.md)

## Why training accuracy is not enough

A model may recognize examples it has already seen while performing poorly with a different person, microphone, orientation, background or device. Evaluation asks whether the model **generalizes** to truly unseen operating conditions.

A complete evaluation should identify:
- What task and labels were evaluated.
- How the train/validation/test partitions were constructed.
- The number of examples in each class.
- Errors that matter for the intended application.
- Model confidence thresholds and rejection policy.
- End-to-end latency and resource requirements, when relevant.

## The confusion matrix

For a classifier with true labels as rows and predictions as columns, consider an illustrative test set:

| Actual / Predicted | red | green | unknown |
|---|---:|---:|---:|
| red | 27 | 1 | 2 |
| green | 2 | 26 | 2 |
| unknown | 4 | 2 | 24 |

There are 90 examples, and 77 appear on the diagonal. **Accuracy** is `77/90 ≈ 85.6%`.

For the class **red**:
- True positive (TP): 27.
- False positive (FP): 2 green examples + 4 unknown examples classified red = 6.
- False negative (FN): 1 green prediction + 2 unknown predictions when actual red = 3.
- Precision = TP/(TP+FP) = `27/33 ≈ 81.8%`.
- Recall = TP/(TP+FN) = `27/30 = 90.0%`.

The confusion matrix explains *which* errors occur; accuracy alone does not.

## False triggers versus missed triggers

A false positive is a command triggered without the correct event. A false negative is a genuine event the system missed. The consequences differ by application:
- In a colorful web dashboard, one false color change is inconvenient.
- In a moving robot, a false start or missed fault may be dangerous.

Choose decision thresholds based on the application's actual error costs. A high precision requirement may reduce false positives but increase missed commands.

## Negative classes and uncertainty

For keyword spotting, the `_silence_` and `_unknown_` classes help the system distinguish supported words from background noise and unsupported speech. They should be measured as normal test classes, not discarded when reporting accuracy.

A classifier often generates softmax scores that sum to 1. This does **not** guarantee calibrated probabilities. A model may be confidently wrong on unfamiliar sound, unusual movements or corrupt input.

An application can use:
- A minimum confidence threshold.
- Explicit rejection of unknown or silence.
- Temporal smoothing.
- A refractory interval to suppress repeated detections.
- Data-quality validity rules and deterministic state checks.

## Leakage from poor dataset splits

Suppose a student records 100 consecutive clips in one room. A random clip split can place almost identical speaker and environment conditions into training and testing. The resulting score exaggerates performance for unfamiliar speakers or rooms.

For speech, split by speaker or session when possible. For IMU gestures, evaluate on different people and, if relevant, another physical platform. Keep all overlapping windows from one original recording within one partition.

Do not tune thresholds on the final test set: that converts it into an implicit validation set.

## Domain shift

**Domain shift** occurs when the distribution of operational inputs differs from the training inputs. Examples:
- Training uses a laptop microphone; deployment uses an embedded audio codec.
- Training happens in a quiet room; deployment includes ventilation fans.
- An IMU classifier is trained with one board orientation; the actual robot uses another orientation.
- Sensor sample rate, gain, filter chain or units change.

Improve robustness through data collection in multiple conditions, physically justified augmentation, standardized preprocessing and real deployment-like tests.

## Quantization regression

A float32 model and its optimized INT8 version may not make identical predictions. After conversion, evaluate both models on the same untouched test split and report:
- Float32 accuracy and per-class metrics.
- INT8 accuracy and per-class metrics.
- Change in percentage points.
- Model file size and required operators.
- Runtime RAM and latency on the intended target.

An insignificant average accuracy change can still hide a severe regression for one important class.

## Timing and resource measurements

Classification compute time is only one part of the response delay. For a streaming recognizer, include:
1. Sensor sampling and buffering.
2. Observation/window duration.
3. Preprocessing and feature extraction.
4. Model invocation.
5. Confidence smoothing and event suppression.
6. Transport and actuation.

A model that invokes in 10 ms may still respond much later when it must first collect a long analysis window.

## Practice questions

1. Explain why 99% training accuracy could coexist with poor real-world accuracy.
2. Calculate precision and recall for `red` from the example confusion matrix.
3. Which metric matters most when false activation has severe consequences?
4. Why should model evaluation be repeated after INT8 quantization?
5. How would you construct a test set for unseen speakers and unseen robot operators?
6. What can the system do with a low-confidence result instead of selecting a command?

**Checkpoint:** A valid model report should let another engineer understand the target, split policy, confusion matrix, rejection behavior and runtime constraints.

[Next: Inference and deployment](07-inference-and-deployment.md)
