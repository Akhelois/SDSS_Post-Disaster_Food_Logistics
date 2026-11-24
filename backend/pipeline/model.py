import os
import shutil
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import ResNet50
from datetime import datetime

from config import MODEL_PATH, MODEL_BACKUP_DIR, INCREMENTAL_LR, INCREMENTAL_EPOCHS, IMG_SIZE

os.makedirs(MODEL_BACKUP_DIR, exist_ok=True)


def now():
    return datetime.now().strftime("%H:%M:%S")


def build_resnet_unet(input_shape=(256, 256, 6)):
    _base = ResNet50(weights='imagenet', include_top=False, input_shape=(256, 256, 3))
    skip_names = ['conv1_relu', 'conv2_block3_out', 'conv3_block4_out',
                  'conv4_block6_out', 'conv5_block3_out']
    encoder_model = models.Model(
        inputs=_base.input,
        outputs=[_base.get_layer(n).output for n in skip_names],
        name='shared_resnet50'
    )

    inputs = layers.Input(shape=input_shape, name='input_6ch')
    pre_img  = inputs[:, :, :, :3]
    post_img = inputs[:, :, :, 3:]

    pre_s1, pre_s2, pre_s3, pre_s4, pre_bridge    = encoder_model(pre_img)
    post_s1, post_s2, post_s3, post_s4, post_bridge = encoder_model(post_img)

    bridge = layers.concatenate([post_bridge, pre_bridge], name='bridge_fusion')
    bridge = layers.Conv2D(2048, (1, 1), activation='relu', padding='same', name='bridge_reduce')(bridge)
    bridge = layers.BatchNormalization(name='bridge_bn')(bridge)

    u4 = layers.Conv2DTranspose(512, (2, 2), strides=(2, 2), padding='same')(bridge)
    u4 = layers.concatenate([u4, post_s4])
    u4 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(u4)
    u4 = layers.BatchNormalization()(u4)
    u4 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(u4)
    u4 = layers.BatchNormalization()(u4)

    u3 = layers.Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same')(u4)
    u3 = layers.concatenate([u3, post_s3])
    u3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(u3)
    u3 = layers.BatchNormalization()(u3)
    u3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(u3)
    u3 = layers.BatchNormalization()(u3)

    u2 = layers.Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(u3)
    u2 = layers.concatenate([u2, post_s2])
    u2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(u2)
    u2 = layers.BatchNormalization()(u2)
    u2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(u2)
    u2 = layers.BatchNormalization()(u2)

    u1 = layers.Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(u2)
    u1 = layers.concatenate([u1, post_s1])
    u1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(u1)
    u1 = layers.BatchNormalization()(u1)
    u1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(u1)
    u1 = layers.BatchNormalization()(u1)

    u0 = layers.Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(u1)
    u0 = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(u0)
    u0 = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(u0)

    outputs = layers.Conv2D(1, (1, 1), activation='sigmoid', name='output_mask')(u0)
    return models.Model(inputs=inputs, outputs=outputs, name='DualResNet50_UNet_6ch')


def bce_dice_loss(y_true, y_pred):
    bce = tf.keras.losses.binary_crossentropy(y_true, y_pred)
    y_true_f = tf.cast(tf.reshape(y_true, [-1]), tf.float32)
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    dice = 1 - (2. * intersection + 1.0) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + 1.0)
    return bce + dice


def weighted_bce_dice_loss(y_true, y_pred):
    y_pred_clipped = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
    logits = tf.math.log(y_pred_clipped / (1 - y_pred_clipped))
    bce = tf.nn.weighted_cross_entropy_with_logits(
        labels=tf.cast(y_true, tf.float32),
        logits=logits,
        pos_weight=15.0
    )
    bce = tf.reduce_mean(bce)
    y_true_f = tf.cast(tf.reshape(y_true, [-1]), tf.float32)
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    dice = 1 - (2. * intersection + 1.0) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + 1.0)
    return bce + dice


def dice_coef(y_true, y_pred):
    y_true_f = tf.cast(tf.reshape(y_true, [-1]), tf.float32)
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    return (2. * intersection + 1.0) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + 1.0)


def load_model():
    print(f"[{now()}] Loading model dari {MODEL_PATH}")

    if os.path.exists(MODEL_PATH):
        try:
            model = tf.keras.models.load_model(
                MODEL_PATH,
                compile=False,
                custom_objects={
                    'bce_dice_loss': bce_dice_loss,
                    'weighted_bce_dice_loss': weighted_bce_dice_loss,
                    'dice_coef': dice_coef
                }
            )
            print(f"[{now()}] Model berhasil dimuat ({os.path.getsize(MODEL_PATH) / 1e6:.1f} MB)")
            return model
        except Exception as e:
            print(f"[{now()}] Gagal load model: {e}")

    print(f"[{now()}] Model .h5 tidak ditemukan. Membangun ResNet50-UNet baru...")
    model = build_resnet_unet()
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=INCREMENTAL_LR),
        loss=weighted_bce_dice_loss,
        metrics=['accuracy', dice_coef]
    )
    model.save(MODEL_PATH)
    print(f"[{now()}] Model awal tersimpan ke {MODEL_PATH}")
    return model
