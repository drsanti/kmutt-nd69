"""Example 04: Programmatic training and evaluation using robotos_kws.Trainer."""
try:
    import robotos_edge as rk
except ImportError:
    import robotos_kws as rk


def main():
    print("[robotos_kws] Starting training pipeline...")
    trainer = rk.Trainer(data_dir="dataset", out_dir="artifacts")

    # 1. Train model
    print("Training DS-CNN with 4x data augmentation...")
    meta = trainer.train(epochs=40, augment=4)
    print("\nTraining finished! Saved int8 model:")
    print(f"  Labels: {meta.get('labels')}")
    print(f"  Int8 model size: {meta.get('int8_tflite_bytes', 0) / 1024:.1f} KiB")
    print(f"  Float32 model size: {meta.get('float_tflite_bytes', 0) / 1024:.1f} KiB")
    print(f"  Best val accuracy: {meta.get('best_val_accuracy', 0):.1%}")

    # 2. Evaluate accuracy on test split
    print("\nEvaluating test set performance...")
    rc = trainer.evaluate(split="test")
    print(f"\nEvaluation finished with exit code {rc}. See artifacts/report.md for details.")
    return rc


if __name__ == "__main__":
    main()
