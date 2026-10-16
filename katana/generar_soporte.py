"""Soporte de pared para katana, diseñado a juego con la katana roja y dorada.

Dos piezas en espejo (izquierda y derecha). Perfil en (y = hacia afuera de la
pared, z = hacia arriba) extruido a lo ancho (x). Lleva:
  - un mon (escudo) de tres hojas en relieve en el frente del labio,
    inspirado en los de la saya, para pintar de dorado;
  - el remate de la placa cortado en diagonal, como la punta (kissaki).
Se imprime acostado sobre un costado: sin soportes. Medidas en mm.

Medidas de la katana tomadas de la foto con la regla (aprox.):
  largo total ~105 cm · tsuka ~33 cm, Ø ~34 mm · saya ~72 cm, Ø ~28 mm
"""
import math
import sys
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, box
from shapely.affinity import rotate, scale, translate
from shapely.ops import unary_union

# ---- Parámetros ----
ANCHO = 40.0          # ancho de la pieza (x)
PLACA_T = 6.0         # grosor de la placa
PLACA_ALTO = 115.0    # alto en el lado alto del corte diagonal
CORTE = 16.0          # cuánto baja el corte diagonal (punta tipo kissaki)
HUECO = 40.0          # tsuka ~34 mm + fieltro y holgura (la saya ~28 mm también cabe)
LABIO_T = 8.0
CUNA_BASE = 20.0
PISO = 7.0
LABIO_ALTO = 24.0
TORNILLO_D = 4.5
CABEZA_D = 9.0
TORNILLOS_Z = [70.0, 92.0]
MON_D = 24.0          # diámetro del mon
MON_RELIEVE = 1.2

r = HUECO / 2
y_in0, y_in1 = PLACA_T, PLACA_T + HUECO
y_out = y_in1 + LABIO_T
z_fondo = CUNA_BASE + PISO
z_c = z_fondo + r
z_top = z_fondo + LABIO_ALTO

def perfil():
    placa = box(0, 0, PLACA_T, PLACA_ALTO)
    cuerpo = box(0, CUNA_BASE, y_out, z_top)
    labio = Point(y_in1 + LABIO_T / 2, z_top).buffer(LABIO_T / 2, 48)
    refuerzo = Polygon([(0, 2), (0, CUNA_BASE + 0.01), (y_out - 6, CUNA_BASE + 0.01)])
    hueco = unary_union([Point(y_in0 + r, z_c).buffer(r, 96), box(y_in0, z_c, y_in1, z_top + 50)])
    p = unary_union([placa, cuerpo, labio, refuerzo]).difference(hueco)
    return p.buffer(0.8, 24).buffer(-0.8, 24).buffer(-0.6, 24).buffer(0.6, 24)

def mon(cx, cz):
    """Mon original de tres hojas dentro de un anillo (en el plano x-z)."""
    R = MON_D / 2
    anillo = Point(0, 0).buffer(R, 96).difference(Point(0, 0).buffer(R - 1.6, 96))
    hojas = []
    for k in range(3):
        hoja = scale(Point(0, 0).buffer(1, 48), 3.0, 4.6)          # elipse
        hoja = hoja.union(Polygon([(-1.2, 4.0), (1.2, 4.0), (0, 6.2)]))  # punta
        hoja = hoja.difference(box(-0.35, -3.6, 0.35, 4.6))         # nervio central
        hoja = translate(hoja, 0, 4.4)
        tallo = box(-0.45, 0, 0.45, 1.6)
        hojas.append(rotate(unary_union([hoja, tallo]), 120 * k, origin=(0, 0)))
    centro = Point(0, 0).buffer(1.4, 32)
    m = unary_union([anillo, centro] + hojas)
    return translate(m, cx, cz)

def a_xyz(mesh_yz_x):
    m = mesh_yz_x
    m.vertices = m.vertices[:, [2, 0, 1]]
    if m.volume < 0:
        m.invert()
    return m

def agujero(xc, zc):
    c = trimesh.creation.cylinder(radius=TORNILLO_D / 2, height=PLACA_T + 2, sections=48)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    c.apply_translation([xc, PLACA_T / 2, zc])
    # cono a 90°: base de Ø11 a 1 mm fuera de la cara frontal; en la cara mide Ø9
    cono = trimesh.creation.cone(radius=CABEZA_D / 2 + 1, height=CABEZA_D / 2 + 1, sections=48)
    cono.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    cono.apply_translation([xc, PLACA_T + 1, zc])
    return trimesh.boolean.union([c, cono], engine="manifold")

def pieza(lado):
    cuerpo = a_xyz(trimesh.creation.extrude_polygon(perfil(), ANCHO))
    # corte diagonal del remate: baja hacia el lado exterior
    alto_int, alto_ext = PLACA_ALTO, PLACA_ALTO - CORTE
    zx0, zx1 = (alto_int, alto_ext) if lado == "izq" else (alto_ext, alto_int)
    cuña2d = Polygon([(-1, zx0 - (zx1 - zx0) / ANCHO), (ANCHO + 1, zx1 + (zx1 - zx0) / ANCHO), (ANCHO + 1, 300), (-1, 300)])
    cuña = trimesh.creation.extrude_polygon(cuña2d, 60)           # (x, z, y)
    cuña.vertices = cuña.vertices[:, [0, 2, 1]]; cuña.vertices[:, 1] -= 5
    if cuña.volume < 0: cuña.invert()
    # mon en relieve en el frente del labio
    mz = (CUNA_BASE + z_top) / 2 + 1
    mm = trimesh.creation.extrude_polygon(mon(ANCHO / 2, mz), MON_RELIEVE + 0.3)
    mm.vertices = mm.vertices[:, [0, 2, 1]]; mm.vertices[:, 1] += y_out - 0.3
    if mm.volume < 0: mm.invert()
    out = trimesh.boolean.union([cuerpo, mm], engine="manifold")
    out = trimesh.boolean.difference([out, cuña] + [agujero(ANCHO / 2, z) for z in TORNILLOS_Z], engine="manifold")
    out.apply_translation(-out.bounds[0])
    pieza.mon = mm  # solo para las vistas renderizadas
    return out

def para_imprimir(m):
    p = m.copy()
    p.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))
    p.apply_translation(-p.bounds[0])
    return p

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    imp = {}
    for lado in ("izq", "der"):
        m = pieza(lado)
        m.export(f"{out}/vista_{lado}.stl")
        pieza.mon.export(f"{out}/vista_mon_{lado}.stl")
        imp[lado] = para_imprimir(m)
        imp[lado].export(f"{out}/soporte_katana_{lado}.stl")
        print(lado, "estanco:", m.is_watertight, "| vol cm3:", round(m.volume / 1000, 1), "| mm:", np.round(m.extents, 1))
    b = imp["der"].copy(); b.apply_translation([0, imp["izq"].extents[1] + 10, 0])
    trimesh.util.concatenate([imp["izq"], b]).export(f"{out}/soporte_katana_par.stl")
