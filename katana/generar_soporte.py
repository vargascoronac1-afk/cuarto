"""Genera el STL del soporte de pared para katana (usar 2 piezas iguales).

Perfil en el plano (y = hacia afuera de la pared, z = hacia arriba), extruido
a lo ancho (x). Se imprime acostado sobre una cara lateral: sin soportes y con
las capas siguiendo el perfil, que es lo más resistente.
Medidas en mm.
"""
import math
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

# ---- Parámetros (ajusta a tu katana) ----
ANCHO = 40.0          # ancho de la pieza (x)
PLACA_T = 6.0         # grosor de la placa de pared
PLACA_ALTO = 115.0    # alto total de la placa
HUECO = 38.0          # espacio interior de la cuna (saya ~30 mm + holgura/fieltro)
LABIO_T = 8.0         # grosor del labio frontal
CUNA_BASE = 20.0      # altura (z) donde empieza la cuna
PISO = 7.0            # grosor del piso de la cuna
LABIO_ALTO = 22.0     # cuánto sube el labio por encima del fondo de la cuna
TORNILLO_D = 4.5      # tornillo #8 / 4 mm
CABEZA_D = 9.0        # avellanado
TORNILLOS_Z = [72.0, 98.0]

r = HUECO / 2
y_in0 = PLACA_T
y_in1 = PLACA_T + HUECO
y_out = y_in1 + LABIO_T
z_fondo = CUNA_BASE + PISO
z_c = z_fondo + r
z_top = z_fondo + LABIO_ALTO

placa = box(0, 0, PLACA_T, PLACA_ALTO)
cuerpo = box(0, CUNA_BASE, y_out, z_top)
labio_redondo = Point(y_in1 + LABIO_T / 2, z_top).buffer(LABIO_T / 2, 48)
refuerzo = Polygon([(0, 2), (0, CUNA_BASE + 0.01), (y_out - 6, CUNA_BASE + 0.01)])
hueco = unary_union([Point(y_in0 + r, z_c).buffer(r, 96), box(y_in0, z_c, y_in1, z_top + 50)])
perfil = unary_union([placa, cuerpo, labio_redondo, refuerzo]).difference(hueco)
perfil = perfil.buffer(0.8, 24).buffer(-0.8, 24)          # suaviza aristas
perfil = perfil.buffer(-0.6, 24).buffer(0.6, 24)          # redondea esquinas convexas

# Extruir a lo ancho: el polígono (y,z) se extruye en su eje normal y luego se rota
m = trimesh.creation.extrude_polygon(perfil, ANCHO)       # coords (y, z, x)
m.vertices = m.vertices[:, [2, 0, 1]]                     # -> (x, y, z)
if m.volume < 0:
    m.invert()

# Agujeros avellanados (eje y, entrando por la cara frontal y = PLACA_T)
def agujero(xc, zc):
    largo = PLACA_T + 2
    c = trimesh.creation.cylinder(radius=TORNILLO_D / 2, height=largo, sections=48)
    cono = trimesh.creation.cone(radius=CABEZA_D / 2 + 1, height=CABEZA_D / 2 + 1, sections=48)
    # cono a 90°: base de Ø11 a 1 mm fuera de la cara frontal; en la cara mide Ø9
    rot = trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])
    c.apply_transform(rot); c.apply_translation([xc, PLACA_T / 2, zc])
    cono.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))  # punta hacia la pared
    cono.apply_translation([xc, PLACA_T + 1, zc])
    return trimesh.boolean.union([c, cono], engine="manifold")

cortes = [agujero(ANCHO / 2, z) for z in TORNILLOS_Z]
pieza = trimesh.boolean.difference([m] + cortes, engine="manifold")

# Orientación de impresión: cara lateral (x = 0) sobre la cama
pieza.apply_translation(-pieza.bounds[0])
pieza_imp = pieza.copy()
pieza_imp.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))
pieza_imp.apply_translation(-pieza_imp.bounds[0])

out = sys.argv[1] if len(sys.argv) > 1 else "."
pieza.export(f"{out}/soporte_katana_vista.stl")
pieza_imp.export(f"{out}/soporte_katana.stl")
par = pieza_imp.copy(); par2 = pieza_imp.copy(); par2.apply_translation([0, pieza_imp.extents[1] + 10, 0])
trimesh.util.concatenate([par, par2]).export(f"{out}/soporte_katana_par.stl")
print("estanco:", pieza.is_watertight, "| volumen cm3:", round(pieza.volume / 1000, 1),
      "| medidas mm (x,y,z):", np.round(pieza.extents, 1), "| cama:", np.round(pieza_imp.extents, 1))
