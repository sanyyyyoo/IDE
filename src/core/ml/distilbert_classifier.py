# src/core/ml/distilbert_classifier.py

import os
import pathlib
import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast


class DistilBERTClassifier:
    def __init__(self, model_path: str):
        # Normalize path for cross-platform compatibility
        model_path = pathlib.Path(model_path).resolve().as_posix()
        print(f"[MODEL] 🔍 Loading DistilBERT model from local folder:\n    {model_path}")

        # ✅ Auto-check: confirm files in model directory
        if not os.path.isdir(model_path):
            raise FileNotFoundError(f"[ERROR] Model directory not found: {model_path}")

        files = os.listdir(model_path)
        print(f"[MODEL] 📦 Files detected in model folder ({len(files)}):")
        for f in files:
            print(f"   ├─ {f}")

        required_files = ["config.json", "tokenizer.json", "model.safetensors"]
        missing = [f for f in required_files if f not in files]
        if missing:
            print(f"[WARNING] ⚠ Missing files: {', '.join(missing)}")
        else:
            print("[MODEL] ✅ All core model files detected.")

        # ✅ Load model and tokenizer strictly from local files
        self.model = DistilBertForSequenceClassification.from_pretrained(
            model_path, local_files_only=True
        )
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(
            model_path, local_files_only=True
        )

        # ✅ Device setup
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        print(f"[MODEL] ✅ Model ready on device: {self.device}")

        # Label mapping
        self.id2label = {0: "name", 1: "category", 2: "address", 3: "phone"}
        self.label2id = {v: k for k, v in self.id2label.items()}

    def classify_batch(self, texts, max_length=128):
        if not texts:
            return []

        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encodings = {k: v.to(self.device) for k, v in encodings.items()}

        with torch.no_grad():
            outputs = self.model(**encodings)
            probs = torch.softmax(outputs.logits, dim=1)
            preds = torch.argmax(outputs.logits, dim=1)

        results = []
        for i, text in enumerate(texts):
            pred_id = preds[i].item()
            pred_label = self.id2label[pred_id]
            confidence = probs[i][pred_id].item()
            all_probs = {
                self.id2label[j]: probs[i][j].item() for j in range(len(self.id2label))
            }
            results.append((pred_label, confidence, all_probs))
        return results

    def classify(self, text):
        results = self.classify_batch([text])
        return results[0] if results else ("name", 0.0, {})
