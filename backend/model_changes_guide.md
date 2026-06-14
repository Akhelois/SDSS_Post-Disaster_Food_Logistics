# Panduan Perubahan Model: Pre+Post Disaster (6-Channel Input)

> **PENTING**: Perubahan ini **OPSIONAL**. Sistem saat ini sudah berfungsi dengan baik
> menggunakan NDVI change detection di GEE sebagai pre-filter + model post-disaster 3-channel.
>
> Terapkan perubahan ini **HANYA** jika Anda ingin meningkatkan akurasi model dengan
> memberikan referensi pre-disaster langsung ke neural network.

---

## Apa yang Berubah?

| Aspek | Sekarang (3-channel) | Setelah (6-channel) |
|-------|---------------------|---------------------|
| Input model | Post-disaster RGB (256,256,3) | Pre+Post concatenated (256,256,6) |
| Encoder | ResNet50 pretrained ImageNet | ResNet50 dengan custom first conv layer |
| Training | Model sudah trained | **Perlu re-training dari awal** |
| Data | Hanya `*_post_disaster.png` | `*_pre_disaster.png` + `*_post_disaster.png` |

---

## File yang Perlu Diubah

### 1. `pipeline.py` — Fungsi `build_resnet_unet()` (Line 109-155)

**Lokasi:** `backend/pipeline.py`, fungsi `build_resnet_unet`

**Sebelum:**
```python
def build_resnet_unet(input_shape=(256, 256, 3)):
    base_model = ResNet50(weights='imagenet', include_top=False, input_shape=input_shape)
    s1 = base_model.get_layer('conv1_relu').output
    # ... dst
```

**Sesudah:**
```python
def build_resnet_unet(input_shape=(256, 256, 6)):
    """
    ResNet50-UNet dengan 6-channel input (pre+post disaster).
    Channel 0-2: Pre-disaster RGB
    Channel 3-5: Post-disaster RGB
    """
    # Custom input layer untuk 6 channel
    inputs = layers.Input(shape=input_shape)
    
    # Split pre dan post
    pre_img = inputs[:, :, :, :3]   # Channel 0-2
    post_img = inputs[:, :, :, 3:]  # Channel 3-5
    
    # Gunakan ResNet50 pretrained untuk post-disaster (3 channel)
    base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(256, 256, 3))
    
    # Buat ResNet50 untuk pre-disaster (shared weights)
    pre_features = base_model(pre_img)
    
    # Buat ResNet50 terpisah untuk post-disaster
    post_base = ResNet50(weights='imagenet', include_top=False, input_shape=(256, 256, 3), name='resnet50_post')
    post_features = post_base(post_img)
    
    # Gabungkan features dari pre dan post di bridge level
    bridge = layers.concatenate([pre_features, post_features])
    bridge = layers.Conv2D(2048, (1,1), activation='relu', padding='same')(bridge)
    bridge = layers.BatchNormalization()(bridge)
    
    # Decoder tetap sama seperti sebelumnya...
    # Catatan: Anda perlu mengambil skip connections dari post_base
    s1 = post_base.get_layer('conv1_relu').output
    s2 = post_base.get_layer('conv2_block3_out').output
    s3 = post_base.get_layer('conv3_block4_out').output
    s4 = post_base.get_layer('conv4_block6_out').output
    
    # U-Net decoder (sama seperti sebelumnya)
    u4 = layers.Conv2DTranspose(512, (2,2), strides=(2,2), padding='same')(bridge)
    u4 = layers.concatenate([u4, s4])
    u4 = layers.Conv2D(512, (3,3), activation='relu', padding='same')(u4)
    u4 = layers.BatchNormalization()(u4)
    u4 = layers.Conv2D(512, (3,3), activation='relu', padding='same')(u4)
    u4 = layers.BatchNormalization()(u4)
    
    # ... (sisanya sama persis seperti decoder yang ada)
    
    outputs = layers.Conv2D(1, (1,1), activation='sigmoid')(u0)
    return models.Model(inputs=inputs, outputs=outputs)
```

---

### 2. `pipeline.py` — Fungsi `predict_mask()` (Line 286-290)

**Lokasi:** `backend/pipeline.py`, fungsi `predict_mask`

**Sebelum:**
```python
def predict_mask(model, img_path):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, IMG_SIZE) / 255.0
    return model.predict(np.expand_dims(img, 0), verbose=0)[0, :, :, 0]
```

**Sesudah:**
```python
def predict_mask(model, img_path, pre_img_path=None):
    """Prediksi mask dengan opsional pre-disaster image."""
    post_img = cv2.imread(img_path)
    post_img = cv2.cvtColor(post_img, cv2.COLOR_BGR2RGB)
    post_img = cv2.resize(post_img, IMG_SIZE) / 255.0
    
    if pre_img_path and os.path.exists(pre_img_path):
        pre_img = cv2.imread(pre_img_path)
        pre_img = cv2.cvtColor(pre_img, cv2.COLOR_BGR2RGB)
        pre_img = cv2.resize(pre_img, IMG_SIZE) / 255.0
        # Concatenate: [pre_R, pre_G, pre_B, post_R, post_G, post_B]
        combined = np.concatenate([pre_img, post_img], axis=-1)  # (256, 256, 6)
    else:
        # Fallback: duplicate post as pre (jika pre tidak tersedia)
        combined = np.concatenate([post_img, post_img], axis=-1)
    
    return model.predict(np.expand_dims(combined, 0), verbose=0)[0, :, :, 0]
```

---

### 3. `pipeline.py` — Fungsi `run_pipeline()` (Line 387-388)

**Lokasi:** `backend/pipeline.py`, di dalam loop `for fname in png_files:` 

**Sebelum:**
```python
mask = predict_mask(model, img_path)
```

**Sesudah:**
```python
# Cari pre-disaster image dari label metadata
pre_img_path = None
try:
    with open(label_path, 'r') as f:
        label_data = json.load(f)
    pre_img_name = label_data.get('metadata', {}).get('pre_img_name')
    if pre_img_name:
        pre_img_path = os.path.join(INPUT_IMAGES, pre_img_name)
except Exception:
    pass

mask = predict_mask(model, img_path, pre_img_path=pre_img_path)
```

---

### 4. Training Notebook — `model/train_model.ipynb`

**Perubahan yang diperlukan di notebook training:**

```python
# Di bagian data loading, ubah dari:
X_train = load_images(post_disaster_paths)  # (N, 256, 256, 3)

# Menjadi:
X_pre = load_images(pre_disaster_paths)     # (N, 256, 256, 3) 
X_post = load_images(post_disaster_paths)   # (N, 256, 256, 3)
X_train = np.concatenate([X_pre, X_post], axis=-1)  # (N, 256, 256, 6)
```

---

## Cara Re-Training

1. Pastikan Anda punya pasangan citra pre+post disaster di folder `training/`
2. Ubah `build_resnet_unet()` seperti di atas
3. Jalankan training di notebook:
   ```python
   model = build_resnet_unet(input_shape=(256, 256, 6))
   model.compile(
       optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
       loss=weighted_bce_dice_loss,
       metrics=['accuracy', dice_coef]
   )
   model.fit(X_train, Y_train, epochs=50, batch_size=8, validation_split=0.2)
   model.save('model/model_sdss.h5')
   ```
4. Model baru akan otomatis dipakai oleh `pipeline.py`

---

## Alternatif: Siamese Network (Lebih Canggih)

Jika Anda ingin arsitektur yang lebih optimal untuk change detection:

```python
def build_siamese_unet(input_shape=(256, 256, 3)):
    """
    Siamese ResNet50-UNet: 2 encoder yang share weights,
    output difference map.
    """
    # Input pre dan post terpisah
    pre_input = layers.Input(shape=input_shape, name='pre_input')
    post_input = layers.Input(shape=input_shape, name='post_input')
    
    # Shared encoder
    encoder = ResNet50(weights='imagenet', include_top=False, input_shape=input_shape)
    
    pre_features = encoder(pre_input)
    post_features = encoder(post_input)
    
    # Difference features
    diff = layers.subtract([post_features, pre_features])
    abs_diff = layers.Lambda(lambda x: tf.abs(x))(diff)
    
    # Decoder dari abs_diff...
    # (implementasi decoder sama seperti U-Net biasa)
    
    return models.Model(inputs=[pre_input, post_input], outputs=outputs)
```

> **Catatan**: Siamese Network memerlukan dataset training yang berbeda format. 
> Setiap sample harus berisi tuple (pre_image, post_image, damage_mask).
