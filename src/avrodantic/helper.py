from collections import defaultdict


def concat_imports(imports: list[dict[str, list[str]]]) -> defaultdict[str, set[str]]:
    dd: defaultdict[str, set[str]] = defaultdict(set)
    for i in imports:
        for k, vl in i.items():
            for v in vl:
                dd[k].add(v)
    return dd
