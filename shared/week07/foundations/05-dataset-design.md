# 05 — Dataset Design, Labels, and Reproducibility

[Foundations](README.md) | [Previous: ML fundamentals](04-machine-learning-fundamentals.md) | [Next: Evaluation](06-model-evaluation.md)

## A model cannot be better than its measurement and labels

A dataset contains **observations** (such as waveforms or motion windows), **labels** (such as `blue` or `lift`), and **metadata** describing how measurements were made. Sensor failures, inconsistent labels, and biased collection procedures enter the learned model.

A common beginner mistake is to collect many examples very quickly using one person and one session, then assume a high test score proves universal performance. Quantity is helpful only when paired with adequate variation and honest evaluation.

## Define the problem before recording

For every class, write a short operational definition:
- `red`: a participant says the spoken word “red” within the capture window.
- `_unknown_`: speech that is **not** one of the supported command words.
- `_silence_`: background noise or absence of intentional speech.
- `shake`: a specified energetic movement of the board.
- `idle`: normal stationary condition, including small vibrations and drift.

Ambiguous labels make the model's objective ambiguous. Do not use the same label for substantially different actions without explaining the intended invariance.

## Good collection protocol

1. **Select sensors and settings:** sampling rate, format, range, gain, axis order and firmware version.
2. **Choose class definitions:** include negative/background classes, not only interesting positive gestures.
3. **Collect variability:** speakers or operators, sessions, distances, orientations, environments and devices.
4. **Track provenance:** identify who/what produced each example, when it was collected, and its settings.
5. **Apply quality checks:** reject corrupted frames, clipping and invalid windows; record rejection counts.
6. **Define the split by groups:** avoid dividing near-duplicates between training and testing.
7. **Protect privacy:** obtain permission before collecting or sharing another person's voice or identifiable data.

## Why negative classes are essential

If a keyword classifier has only `red`, `green` and `blue`, it may be forced to choose one of these labels when hearing “hello,” a cough or room noise. `_unknown_` and `_silence_` teach it about rejection cases. These classes do not magically make a model robust; they still need varied examples.

For a robot, normal movement and inertial noise should be represented, so the model does not trigger on every slight vibration.

## Class imbalance

Suppose a collection contains 400 examples of `red` and 40 each of `green`, `blue`, and `off`. A naive classifier may maximize aggregate accuracy by favoring `red`. Possible remedies include:
- Collect more examples of minority classes.
- Use class weighting.
- Targeted augmentation of underrepresented cases.
- Downsampling if there is ample majority-class data.

Evaluate per-class performance; overall accuracy can hide minority failures.

## Augmentation

Artificial transformations can imitate some variation:
- Audio: gain adjustment, modest noise, small time shifts.
- IMU: orientation augmentation (if physically valid), modest time shifts, measurement noise.
- Both: only augment training data, not the final held-out test set.

Augmentation is not a substitute for fresh recordings. A signal transformation is valid only if it preserves the intended class. An extreme time shift can remove a keyword; arbitrary rotation can invalidate a gesture defined relative to gravity.

## A simple metadata schema

```json
{
  "label": "shake",
  "person_id": "participant_03",
  "session_id": "session_02",
  "device": "ws28p",
  "sensor": "QMI8658",
  "sample_rate_hz": 50,
  "channels": ["ax", "ay", "az", "gx", "gy", "gz"],
  "units": ["m/s2", "m/s2", "m/s2", "rad/s", "rad/s", "rad/s"],
  "window_samples": 100,
  "valid": true
}
```

This is an **illustrative** schema, not a claim about the exact current CLI file format. In real code, save calibration and firmware/model pipeline version as well.

## Train / validation / test

- **Training set:** examples used to optimize model weights.
- **Validation set:** used to choose hyperparameters, thresholds and candidates.
- **Test set:** held out for the final performance claim.

For speech, group by **speaker or session** when assessing new speakers/sessions. For gesture recognition, split by **person or robot platform** when targeting unseen operators/hardware. Random individual-window splitting from overlapping streams leaks near-identical input segments into the test set.

## Discussion exercises

1. Describe five ways a speech dataset might fail to represent real deployment.
2. What differs between a `_silence_` example and an `_unknown_` example?
3. Why can two windows from the same recording be near-duplicates?
4. What should happen when an IMU window contains missing timestamps?
5. Why is test data augmentation usually inappropriate?

[Next: Evaluation](06-model-evaluation.md)
