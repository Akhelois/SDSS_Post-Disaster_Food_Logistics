# New baselines — checkpoints, dependencies, execution order

No existing file was modified. All new artifacts use new filenames only.

## 1. Proposed architectures (no U-Net decoder anywhere)

### CV: image-level damage-presence classification (NOT segmentation)

The existing task is pixel-level binary semantic segmentation
(`256x256x6` pre+post input → `256x256x1` sigmoid mask, BCE+Dice loss,
Dice/IoU/PR-AUC on flattened pixels). A pretrained ViT or ConvNeXt
**classification** model cannot output a segmentation mask, and attaching a
U-Net-style decoder (`Conv2DTranspose` + skips) is forbidden. The technically
valid adaptation is therefore a **task-shifted image-level head**:

- Label derived from the existing masks, no new annotation:
  `y_img = 1{damage_ratio >= TAU_LABEL}`, `damage_ratio = (mask > 0).mean()`,
  `TAU_LABEL = 0.01` (aligns with the existing Low/Medium break at 1%).
- Same `1959/420/420` pair split (`SEED=42`), same `256x256` resize + `/255`
  norm, same train-only flips. Post-disaster RGB only (`256x256x3`), because
  ImageNet stems expect 3 channels; early-fusion 6-ch would break pretrained
  weights.
- Head: `Base(include_top=False, pooling="avg") -> Dropout -> Dense(1, sigmoid)`,
  loss `binary_crossentropy`, threshold selected on **val by image-F1**,
  reported on **test once**.
- Metrics ONLY: Accuracy / Precision / Recall / F1 / ROC-AUC / PR-AUC +
  confusion at `t*`. **Never Dice/IoU for these heads; never rank them
  against the segmentation Dice/IoU numbers.**

| Model | Pretrained checkpoint | TF/Keras-native? |
|---|---|---|
| ConvNeXt-Tiny classifier | `tf.keras.applications.ConvNeXtTiny(weights="imagenet", include_top=False, input_shape=(256,256,3), pooling="avg")` | Yes, TF 2.13 / Keras 2.13, no new dep |
| ViT-B/16 classifier | `VIT_PRESET = "vit_base_patch16_224"` via `keras_hub.models.ViTBackbone.from_preset(..., load_weights=True)` | **No — requires `pip install keras-hub`** (guarded import; cell skips with instructions if absent). Verify the preset string against your installed keras-hub version (`ViTBackbone.presets`). Do NOT train a ViT from scratch and call it pretrained. |

### Logistics: multi-output regression (same task, no change)

- Same 7 inputs in order: `damage_count, affected_kk, total_population,
  disaster_type_enc, severity_level, emergency_duration, vulnerability_idx`.
- Same 17 targets in notebook order (`beras_kg ... kipas_angin_pcs`).
- Same `SEED=42` two-stage split (fit 32k / val 8k / test 10k), same
  `calculate_metrics()` (MAE_macro / RMSE_macro / R2_macro + per-item MAE).

| # | Model | Why suitable | Note |
|---|---|---|---|
| 1 | `RandomForestRegressor` (sklearn, native multi-output) | Bagging baseline; no scaling needed; robust to the `kipas` discontinuity | Needs no new dependency |
| 2 | `HistGradientBoostingRegressor` wrapped in `MultiOutputRegressor` (sklearn) | Boosted-trees counterpart; closest native analogue of XGBoost | **XGBoost substitute**: `xgboost` is absent repo-wide and installs are forbidden. To swap later: `MultiOutputRegressor(xgb.XGBRegressor(...))` with identical splits/metrics, no other change. |

## 2. Dependencies (documented only — nothing installed)

- Present (pinned in `requirements copy.txt`): `scikit-learn==1.3.2`
  (covers RF + HGB), `tensorflow==2.13.0`, `pandas`, `numpy`, `opencv`.
- Optional, ViT only: `pip install keras-hub` (do this yourself before running
  the ViT cell; the ConvNeXt cell runs without it).
- Not used / not installed: `xgboost`, `lightgbm`, `timm`, `transformers`,
  `segmentation_models`.

## 3. Execution order (you run these; nothing was executed)

1. `backend/model/compare_vit_convnext_classification.ipynb` — run top to
   bottom from `backend/model/`. Writes only to `comparison_cls/`.
2. `backend/model/compare_logistics_tree_baselines.ipynb` — run top to bottom
   from `backend/model/`. Writes only `model_logistics_rf.pkl`,
   `model_logistics_hgb.pkl`, `logistics_tree_baseline_comparison.csv`,
   `logistics_tree_per_item_mae.csv`.
3. Merge the new tables into the thesis yourself; keep segmentation
   (Dice/IoU) and classification (Accuracy/F1/AUC) results in separate tables.

## 4. Known limitations (read before running)

- Classification vs segmentation is **task-shifted**: shared data/splits do
  not make the metrics commensurable. Report side-by-side, no ranking claim.
- Pair-level split means the same event can appear in train and test
  (pre-existing thesis limitation); single `seed 42`, no significance test.
- ViT preset/API must be confirmed against your `keras-hub` version.
- ConvNeXt fine-tune phase unfreezes the stem: slower and more VRAM than the
  frozen phase; reduce `BATCH_SIZE` if OOM.
- RF (`n_estimators=300`) on 32k x 7 is CPU-heavy but fits RAM; HGB trains
  one estimator per each of the 17 targets.
- `VGG16(weights=None)` + frozen encoder in the old notebook is a
  frozen-random baseline, not true transfer learning — do not describe it as
  ImageNet-pretrained.
