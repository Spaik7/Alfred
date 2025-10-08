# Archived Files - Old Mycroft Precise Approach

This folder contains the old wake word detection approach using Mycroft Precise that **didn't work properly**.

---

## Why These Files Are Archived

### ❌ Problems with Old Approach

1. **Broken Model** - 32.84% accuracy (should be 95%+)
2. **All predictions = 1.000** - Model stuck, predicted everything as wake word
3. **0% rejection rate** - Couldn't distinguish wake from not-wake words
4. **TensorFlow compatibility issues** - Broke with TensorFlow 2.x
5. **Large model size** - ~2MB vs new 32KB

### ✅ New Approach (Main Project)

- **100% accuracy** with proper PyTorch implementation
- **60x smaller model** (~32KB)
- **No TensorFlow issues**
- **Built-in data augmentation**
- **Raspberry Pi optimized**

---

## What's in This Folder

### `precise_trainer_old_mycroft.py`
Old training script for Mycroft Precise. Replaced by `/train.py`.

**Don't use this** - it's broken and produces unusable models.

### `precise_test.py`
Old testing script with TensorFlow 1.x code. Replaced by `/test.py`.

### `WWD.h5`
Old wake word model file (935KB). Replaced by `models/alfred_pytorch.pt` (32KB).

### `old_models/`
Contains old Mycroft Precise model files:
- `alfred.net` - Keras model (broken)
- `alfred.pb` - TensorFlow protobuf (broken)
- `alfred.epoch`, `alfred.logs/` - Training artifacts
- `*.params` - Model parameters

---

## Comparison: Old vs New

| Feature | Old (Mycroft Precise) | New (PyTorch) |
|---------|----------------------|---------------|
| **Accuracy** | 32.84% ❌ | 100.00% ✅ |
| **Wake Detection** | 100% (22/22) | 100% (22/22) |
| **Not-Wake Rejection** | 0% (0/45) ❌ | 100% (45/45) ✅ |
| **Model Size** | ~2MB | ~32KB |
| **Training Time** | ~30 mins | ~15 mins |
| **Data Required** | 500+ samples | 100+ samples |
| **TensorFlow Issues** | Yes ❌ | No ✅ |
| **Data Augmentation** | No | Yes (5x) ✅ |
| **RPi Optimized** | No | Yes ✅ |

---

## Test Results Comparison

### Old Model (Broken)
```
Wake word detection:     100.00% (22/22)
Not-wake rejection:        0.00% (0/45) ❌
Overall accuracy:         32.84% ❌

All scores: 1.000 (stuck) ❌
```

### New Model (Working)
```
Wake word detection:     100.00% (22/22) ✅
Not-wake rejection:      100.00% (45/45) ✅
Overall accuracy:        100.00% ✅

Wake scores:     0.547-0.792 (avg 0.753) ✅
Not-wake scores: 0.056-0.465 (avg 0.121) ✅
```

---

## Can I Delete This Folder?

**Yes!** You can safely delete the entire `archived/` folder.

Everything in here is:
- Broken and doesn't work
- Replaced by better implementations
- Kept only for reference/backup

To delete:
```bash
rm -rf archived/
```

---

## Migration Notes

If you were using the old approach, see `/MIGRATION_GUIDE.md` for how to switch to the new system.

**Summary:**
- Old: `python precise_trainer.py "Alfred" --step train` ❌
- New: `python train.py --epochs 100` ✅

The new approach uses your existing data in `precise_data/` - no need to re-record!

---

## Why We Kept This

This folder serves as:
1. **Backup** - In case you want to reference old files
2. **Documentation** - Shows what didn't work and why
3. **Comparison** - Demonstrates improvement in new approach

But it's safe to delete if you don't need it.

---

**Bottom line:** Use the new PyTorch approach in the main project. These archived files are broken and outdated.
