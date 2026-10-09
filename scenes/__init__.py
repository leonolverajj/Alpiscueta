"""Scene registry. Each scene module registers draw functions with @scene("visual_name").

draw(ctx, t, T, seg): t = seconds into the segment, T = segment duration,
seg = timeline dict (seg["scene"] has the script entry: id, text, kw...).
"""
import importlib
import pkgutil

REGISTRY = {}


def scene(name):
    def deco(fn):
        REGISTRY[name] = fn
        return fn
    return deco


def _load():
    if REGISTRY.get("__loaded__"):
        return
    for m in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{m.name}")
    REGISTRY["__loaded__"] = True


def get_scene(name):
    _load()
    if name in REGISTRY:
        return REGISTRY[name]
    return REGISTRY["placeholder"]
