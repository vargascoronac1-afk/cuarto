import sys, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
m = trimesh.load(sys.argv[1])
fig = plt.figure(figsize=(12, 5), facecolor="white")
light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
for i, (el, az, t) in enumerate([(18, -55, "Vista 3/4"), (0, 0, "Perfil (lado)"), (0, -90, "Frente")]):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d")
    shade = 0.35 + 0.65 * np.clip(m.face_normals @ light, 0, 1)
    cols = np.c_[0.20 * shade + .05, 0.24 * shade + .07, 0.32 * shade + .1, np.ones_like(shade)]
    ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=cols, edgecolor="none"))
    b = m.bounds; c = b.mean(0); s = (b[1] - b[0]).max() / 2
    ax.set_xlim(c[0]-s, c[0]+s); ax.set_ylim(c[1]-s, c[1]+s); ax.set_zlim(c[2]-s, c[2]+s)
    ax.view_init(el, az); ax.set_box_aspect((1, 1, 1)); ax.set_axis_off(); ax.set_title(t)
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=110)
