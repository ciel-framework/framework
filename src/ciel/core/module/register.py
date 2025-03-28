from collections import defaultdict
from .module import Module, ModuleManifest

class ModuleRegister:

    def __init__(self, modules: list[Module]) -> None:
        indexed = {m.manifest: m for m in modules}

        in_edges = defaultdict(set)
        out_edges = defaultdict(set)

        roots: list[ModuleManifest] = []

        for m in indexed.keys():
            if len(m.dependencies):
                for dep in m.dependencies:
                    if dep not in indexed:
                        raise ValueError(f"Missing dependency {dep}")
                    in_edges[m].add(dep)
                    out_edges[dep].add(m)
            else:
                roots.append(m)

        self.modules: list[Module] = []
        while len(roots) > 0:
            n = roots.pop(0)
            self.modules.append(indexed[n])
            for m in list(out_edges[n]):
                out_edges[n].remove(m)
                in_edges[m].remove(n)
                if len(in_edges[m]) == 0:
                    roots.append(m)

        if any((len(in_edges[m]) > 0 or len(out_edges[m]) > 0) for m in indexed.keys()):
            raise RuntimeError("Cycle in module dependencies")
