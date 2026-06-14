# ==============================================================
# PANDUAN UPDATE train_model.ipynb → 6-Channel (Pre+Post)
# Ditulis dalam gaya inline notebook (tanpa function wrapper)
# ==============================================================
#
# PERUBAHAN DIPERLUKAN DI 2 CELL:
#   - Cell 11: Arsitektur model
#   - Cell 22: Data loading
#
# Setelah update → Run All Cells dari awal → Train ulang


# =========================================================
# CELL 11 — GANTI SELURUH ISI CELL INI:
# =========================================================

from keras.src.layers.core import activation

# Modelling -> DualResNet50-UNet (6-channel: pre+post disaster)
# ---- Shared Encoder ----
# Shared ResNet50 digunakan untuk KEDUA citra (pre & post) dengan bobot yang sama
_base = ResNet50(weights="imagenet", include_top=False, input_shape=(256, 256, 3))

encoder_model = Model(
    inputs=_base.input,
    outputs=[
        _base.get_layer("conv1_relu").output,       # skip1: 128x128, 64ch
        _base.get_layer("conv2_block3_out").output,  # skip2: 64x64,  256ch
        _base.get_layer("conv3_block4_out").output,  # skip3: 32x32,  512ch
        _base.get_layer("conv4_block6_out").output,  # skip4: 16x16, 1024ch
        _base.get_layer("conv5_block3_out").output,  # bridge: 8x8,  2048ch
    ],
    name="shared_resnet50"
)

# ---- Input 6-channel ----
inputs = Input(shape=(256, 256, 6), name="input_6ch")
pre_img  = inputs[:, :, :, :3]   # Channel 0-2: pre-disaster RGB
post_img = inputs[:, :, :, 3:]   # Channel 3-5: post-disaster RGB

# ---- Forward pass kedua cabang (bobot shared) ----
pre_s1,  pre_s2,  pre_s3,  pre_s4,  pre_bridge  = encoder_model(pre_img)
post_s1, post_s2, post_s3, post_s4, post_bridge = encoder_model(post_img)

# ---- Bridge Fusion: gabungkan pre+post → reduksi ke 2048 ----
x = concatenate([post_bridge, pre_bridge], name="bridge_fusion")  # (8,8,4096)
x = Conv2D(2048, (1, 1), activation="relu", padding="same", name="bridge_reduce")(x)
x = BatchNormalization(name="bridge_bn")(x)

# ---- Decoder U-Net (skip connections dari branch post-disaster) ----
# Level 4 → 16x16
x = Conv2DTranspose(512, (2, 2), strides=(2, 2), padding="same")(x)
x = concatenate([x, post_s4])
x = Conv2D(512, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)
x = Conv2D(512, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)

# Level 3 → 32x32
x = Conv2DTranspose(256, (2, 2), strides=(2, 2), padding="same")(x)
x = concatenate([x, post_s3])
x = Conv2D(256, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)
x = Conv2D(256, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)

# Level 2 → 64x64
x = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding="same")(x)
x = concatenate([x, post_s2])
x = Conv2D(128, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)
x = Conv2D(128, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)

# Level 1 → 128x128
x = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding="same")(x)
x = concatenate([x, post_s1])
x = Conv2D(64, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)
x = Conv2D(64, (3, 3), activation="relu", padding="same")(x)
x = BatchNormalization()(x)

# Level 0 → 256x256
x = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding="same")(x)
x = Conv2D(32, (3, 3), activation="relu", padding="same")(x)
x = Conv2D(32, (3, 3), activation="relu", padding="same")(x)

# Output mask
x = Conv2D(1, (1, 1), activation="sigmoid", name="output_mask")(x)


# =========================================================
# CELL 12 — GANTI DENGAN INI:
# =========================================================

model = Model(inputs=inputs, outputs=x, name="DualResNet50_UNet_6ch")
model.summary()


# =========================================================
# CELL 22 — GANTI BAGIAN DATA LOADING:
# =========================================================
#
# SEBELUMNYA:
#   post_images = sorted(glob.glob(os.path.join(IMAGES_DIR, "*_post_disaster.png")))
#   image_paths, target_paths = [], []
#
# GANTI DENGAN:

post_images  = sorted(glob.glob(os.path.join(IMAGES_DIR, "*_post_disaster.png")))
image_pairs  = []   # list of (pre_path, post_path)
target_paths = []

for post_path in post_images:
    pre_path   = post_path.replace("_post_disaster.png", "_pre_disaster.png")
    scene_id   = os.path.basename(post_path).replace("_post_disaster.png", "")
    label_path = os.path.join(LABELS_DIR, f"{scene_id}_post_disaster.json")

    if not os.path.exists(label_path):
        continue

    # Fallback: jika pre tidak ada, duplikasi post sebagai pre
    if not os.path.exists(pre_path):
        pre_path = post_path

    image_pairs.append((pre_path, post_path))
    target_paths.append(label_path)

print(f"Ditemukan {len(image_pairs)} pasangan citra pre+post")


# =========================================================
# CELL BARU (sisipkan setelah Cell 22) — LOAD GAMBAR:
# =========================================================
#
# Fungsi load_image dari notebook Anda biasanya seperti:
#   img = cv2.imread(path) → resize → normalize
#
# Ubah menjadi:

def load_image_pair(pre_path, post_path):
    """Load pre+post, return (256,256,6) float32 array."""
    post = cv2.imread(post_path)
    post = cv2.cvtColor(post, cv2.COLOR_BGR2RGB)
    post = cv2.resize(post, IMG_SIZE).astype(np.float32) / 255.0

    pre = cv2.imread(pre_path)
    pre = cv2.cvtColor(pre, cv2.COLOR_BGR2RGB)
    pre = cv2.resize(pre, IMG_SIZE).astype(np.float32) / 255.0

    # [pre_R, pre_G, pre_B, post_R, post_G, post_B]
    return np.concatenate([pre, post], axis=-1)  # (256, 256, 6)

# Ganti di bagian X loading:
# SEBELUM: X = np.array([cv2.imread(p) ...]) → shape (N, 256, 256, 3)
# SESUDAH:
X = np.array([load_image_pair(pre, post) for pre, post in image_pairs])
print(f"X shape: {X.shape}")   # harus (N, 256, 256, 6)
