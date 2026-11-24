import os
import shutil
import numpy as np
import tensorflow as tf
from datetime import datetime

from config import MODEL_PATH, MODEL_BACKUP_DIR, INCREMENTAL_LR, INCREMENTAL_EPOCHS
from pipeline.model import bce_dice_loss, dice_coef


def now():
    return datetime.now().strftime("%H:%M:%S")


def backup_model():
    if not os.path.exists(MODEL_PATH):
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(MODEL_BACKUP_DIR, f"model_sdss_{timestamp}.h5")
    try:
        shutil.copy2(MODEL_PATH, backup_path)
        print(f"[{now()}] Backup model: {backup_path}")

        backups = sorted(
            [f for f in os.listdir(MODEL_BACKUP_DIR) if f.endswith('.h5')],
            reverse=True
        )
        for old in backups[5:]:
            os.remove(os.path.join(MODEL_BACKUP_DIR, old))
    except Exception as e:
        print(f"[{now()}] Gagal backup: {e}")


def incremental_train(model, processed_images, processed_masks):
    if not processed_images or len(processed_images) == 0:
        return

    print(f"[{now()}] === Incremental Learning: {len(processed_images)} citra baru ===")

    backup_model()

    X = np.array(processed_images, dtype=np.float32)
    Y = np.expand_dims(np.array(processed_masks, dtype=np.float32), axis=-1)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=INCREMENTAL_LR),
        loss=bce_dice_loss,
        metrics=['accuracy', dice_coef]
    )

    history = model.fit(
        X, Y,
        epochs=INCREMENTAL_EPOCHS,
        batch_size=min(4, len(X)),
        verbose=1
    )

    model.save(MODEL_PATH)
    final_loss = history.history['loss'][-1]
    final_dice = history.history['dice_coef'][-1]
    print(f"[{now()}] Model updated: loss={final_loss:.4f}, dice={final_dice:.4f}")
    print(f"[{now()}] Tersimpan: {MODEL_PATH}")
