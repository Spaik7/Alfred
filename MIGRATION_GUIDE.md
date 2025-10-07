# Migration Guide: Mycroft Precise → Custom PyTorch

This document explains the changes from the old Mycroft Precise approach to the new custom PyTorch model.

## What Changed

### ✅ New Files

| File | Purpose |
|------|---------|
| `train.py` | **Main training script** - Replaces `precise_trainer.py` |
| `test.py` | **Main testing script** - Simplified interface |
| `wake_word_trainer.py` | PyTorch model architecture & training logic |
| `wake_word_detector.py` | Detection & testing logic |
| `requirements.txt` | Updated dependencies (PyTorch instead of TensorFlow) |

### 📦 Archived Files

Old Mycroft Precise files moved to `archived/` directory:
- `archived/precise_trainer_old_mycroft.py` - Old training script (broken)
- Note: `precise_recorder.py` still works! No changes needed for recording.

### 🗑️ Can Be Deleted

These are no longer needed:
- `precise_test.py` - Replaced by `test.py`
- `openwakeword_test/` - Keep if you want to compare approaches, otherwise delete

---

## Command Changes

### Recording (No Change!)

```bash
# Still the same
python precise_recorder.py --wake-word "Alfred" --count 150
```

### Training (New!)

**Old way (broken):**
```bash
python precise_trainer.py "Alfred" --epochs 100
```

**New way:**
```bash
python train.py --epochs 100
```

### Testing (New!)

**Old way (broken):**
```bash
python precise_trainer.py "Alfred" --step test
python precise_test.py models/alfred.net
```

**New way:**
```bash
python test.py --test          # Test dataset
python test.py --listen        # Live microphone
python test.py --test --listen # Both
```

---

## Key Improvements

### 1. **100% Accuracy** (was 32.84%)
- Old model was completely broken (all scores = 1.000)
- New model has proper score distribution
- Clear separation between wake/not-wake

### 2. **60x Smaller Model**
- Old: ~2MB
- New: ~32KB
- Faster loading, less memory

### 3. **Data Augmentation**
- Automatically multiplies your samples 5x
- 128 wake samples → 640 training samples
- Works with less data

### 4. **No TensorFlow Issues**
- No more Keras compatibility errors
- No TensorFlow 1.x vs 2.x problems
- Clean PyTorch implementation

### 5. **Simpler Interface**
```bash
# Old (complex)
python precise_trainer.py "Alfred" --step train --epochs 100
python precise_trainer.py "Alfred" --step test

# New (simple)
python train.py --epochs 100
python test.py --test --listen
```

---

## Migration Steps

If you have an existing project:

### 1. **Backup** (Optional)
```bash
# Your old model is already archived, but if you want extra safety:
cp -r models models_backup
cp -r precise_data precise_data_backup
```

### 2. **Update Dependencies**
```bash
source myvenv/bin/activate
pip install -r requirements.txt
```

This will install:
- PyTorch (CPU version)
- Librosa
- Other dependencies

### 3. **Retrain Your Model**
```bash
# Your existing data in precise_data/ will work!
python train.py --epochs 100
```

This creates: `models/alfred_pytorch.pt`

### 4. **Test New Model**
```bash
python test.py --test --listen
```

### 5. **Clean Up** (Optional)
```bash
# Delete old broken model
rm models/alfred.net

# Delete old test script
rm precise_test.py

# Delete comparison directory (if you don't need it)
rm -rf openwakeword_test
```

---

## Troubleshooting Migration

### "ModuleNotFoundError: No module named 'torch'"

```bash
source myvenv/bin/activate
pip install -r requirements.txt
```

### "Old model still shows up"

The old `models/alfred.net` won't interfere. The new scripts look for `alfred_pytorch.pt`.

To avoid confusion:
```bash
mv models/alfred.net archived/alfred.net
```

### "I want to compare old vs new"

Use the comparison script:
```bash
cd openwakeword_test
source venv/bin/activate
pip install tensorflow keras
cd ..
python openwakeword_test/compare_models.py
```

---

## What You Don't Need To Change

✅ **Recording workflow** - `precise_recorder.py` still works exactly the same

✅ **Data directory structure** - `precise_data/train/` and `precise_data/test/` are the same

✅ **Audio files** - All your existing recordings work with the new model

---

## Quick Reference

### Old Workflow
```bash
# 1. Record
python precise_recorder.py --wake-word "Alfred"

# 2. Train (BROKEN)
python precise_trainer.py "Alfred" --epochs 100

# 3. Test (BROKEN)
python precise_trainer.py "Alfred" --step test
```

### New Workflow
```bash
# 1. Record (same!)
python precise_recorder.py --wake-word "Alfred"

# 2. Train (new, works!)
python train.py --epochs 100

# 3. Test (new, works!)
python test.py --test --listen
```

---

## Results Comparison

### Old Model (Mycroft Precise)
```
Wake word detection:     100.00% (22/22)
Not-wake rejection:        0.00% (0/45)  ❌
Overall accuracy:         32.84%         ❌

All scores stuck at 1.000 ❌
Model size: ~2MB
```

### New Model (Custom PyTorch)
```
Wake word detection:     100.00% (22/22) ✅
Not-wake rejection:      100.00% (45/45) ✅
Overall accuracy:        100.00%         ✅

Proper score distribution ✅
Model size: ~32KB (60x smaller!)
```

---

## Questions?

**Q: Do I need to re-record data?**
A: No! Your existing data works perfectly.

**Q: Can I use both models?**
A: Technically yes, but the old one is broken. Use the new one.

**Q: Will this work on Raspberry Pi?**
A: Yes! The new model is specifically optimized for RPi.

**Q: What about the openwakeword_test directory?**
A: That was for testing alternatives. You can delete it or keep it for reference.

---

## Summary

✅ **Recording:** No change
✅ **Training:** `train.py` (new, works)
✅ **Testing:** `test.py` (new, works)
✅ **Results:** 100% accuracy (was 32.84%)
✅ **Model Size:** 32KB (was 2MB)
✅ **Data:** Existing recordings work

**Bottom line:** The new approach is better in every way. Migration is simple - just retrain with your existing data!
