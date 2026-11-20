"""Example 04: Programmatic training and evaluation using robotos_kws.Trainer."""
import robotos_kws as rk


def main():
    print("[robotos_kws] Starting training pipeline...")
    trainer = rk.Trainer(data_dir="dataset", out_dir="artifacts")

    # 1. Train model
    print("Training DS-CNN with 4x data augmentation...")
    meta = trainer.train(epochs=40, augment=4)
    print("Training finished! Saved int8 model:")
    print(f"  Labels: {meta.get('labels')}")

    # 2. Evaluate accuracy on test split
    print("\nEvaluating test set performance...")
    rc = trainer.evaluate(split="test")
    print(f"Evaluation finished with exit code {rc}. See artifacts/report.md for details.")
    return rc


if __name__ == "__main__":
    main()
