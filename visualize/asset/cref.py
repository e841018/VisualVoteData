# Generate an image for color reference.
# H and S visualize the ratio of 3 numbers, while V is set to maximum.
# Final output:  R
#               G B

import numpy as np
import imageio.v3 as iio

# meshgrid
w = 512
h = int(np.ceil((w - 1) / 2 * np.sqrt(3))) + 1
x = np.linspace(0, 2 / np.sqrt(3), w)
y = x[:h]
Y, X = np.meshgrid(y, x, indexing='ij')

# color channels
R = Y
G = - (1 / 2) * Y - (np.sqrt(3) / 2) * X + 1
B = - (1 / 2) * Y + (np.sqrt(3) / 2) * X
A = (G >= 0) & (B >= 0) # R >= 0 for all pixels
mask = ~A

# assemble
img = np.stack((R, G, B, A), 2)
img[:, :, :3] /= img[:, :, :3].max(axis=2, keepdims=True)
img = (img * 255).astype(np.uint8)
img[mask] = 0

# trim and flip
for i in range(h):
    if not np.all(mask[h-1-i]):
        break
img = np.flip(img[:h-i], axis=0)

# export
iio.imwrite('cref.png', img)
