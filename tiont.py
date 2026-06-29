import json
import win32com.client
from pathlib import Path


def get_autocad():
    return win32com.client.GetActiveObject("AutoCAD.Application")


def get_model_space(acad):
    return acad.ActiveDocument.ModelSpace


def lister_entites(model_space):
    entites = {}
    for entity in model_space:
        t = entity.EntityName
        entites[t] = entites.get(t, 0) + 1
    return entites


def get_attributs(bloc):
    attributs = {}
    if bloc.HasAttributes:
        for att in bloc.GetAttributes():
            attributs[att.TagString] = att.TextString
    return attributs


def get_parametres_dynamiques(bloc):
    parametres = {}
    try:
        for p in bloc.GetDynamicBlockProperties():
            parametres[p.PropertyName] = p.Value
    except Exception:
        pass
    return parametres


def pt3(p):
    return {"x": round(p[0], 4), "y": round(p[1], 4), "z": round(p[2], 4)}


def get_lignes_bloc(acad, bloc_name):
    """Retourne toutes les AcDbLine dans la définition du bloc."""
    lignes = []
    try:
        block_def = acad.ActiveDocument.Blocks.Item(bloc_name)
        for entity in block_def:
            if entity.EntityName == "AcDbLine":
                lignes.append({
                    "debut": pt3(entity.StartPoint),
                    "fin":   pt3(entity.EndPoint),
                    "layer": entity.Layer,
                })
    except Exception:
        pass
    return lignes


def collecter_blocs_dynamiques(model_space, acad):
    blocs = []
    for entity in model_space:
        if entity.EntityName != "AcDbBlockReference":
            continue
        try:
            props = entity.GetDynamicBlockProperties()
            if len(props) == 0:
                continue
        except Exception:
            continue

        nom = entity.EffectiveName
        pt  = entity.InsertionPoint
        blocs.append({
            "nom":       nom,
            "layer":     entity.Layer,
            "insertion": pt3(pt),
            "lignes":    get_lignes_bloc(acad, nom),
            "attributs": get_attributs(entity),
            "parametres": get_parametres_dynamiques(entity),
        })
    return blocs


def sauvegarder_json(entites, blocs, chemin: str | Path, filename: str = "Default"):
    chemin = Path(chemin)
    filename_stem = Path(filename).stem

    if chemin.suffix.lower() == ".json":
        fichier = chemin
        fichier.parent.mkdir(parents=True, exist_ok=True)
    else:
        if chemin.exists() and not chemin.is_dir():
            chemin.unlink()
        chemin.mkdir(parents=True, exist_ok=True)
        fichier = chemin / f"{filename_stem}.json"

    data = {"resume_entites": entites, "blocs_dynamiques": blocs}
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nFichier JSON enregistré : {fichier}")
    return fichier


def afficher(entites):
    print(f"\n{'Entité':<30} {'Nombre':>6}")
    print("-" * 38)
    for nom, count in sorted(entites.items()):
        print(f"{nom:<30} {count:>6}")
    print("-" * 38)
    print(f"{'TOTAL':<30} {sum(entites.values()):>6}")


def afficher_blocs(blocs):
    print("\n" + "=" * 60)
    print("BLOCS DYNAMIQUES — Coordonnées lignes, Attributs & Paramètres")
    print("=" * 60)
    if not blocs:
        print("  Aucun bloc dynamique trouvé.")
    for i, b in enumerate(blocs, 1):
        ins = b["insertion"]
        print(f"\n[{i}] Bloc : {b['nom']}  (Layer: {b['layer']})")
        print(f"  Insertion : x={ins['x']}  y={ins['y']}  z={ins['z']}")
        if b["lignes"]:
            print(f"  Lignes ({len(b['lignes'])}) :")
            for j, l in enumerate(b["lignes"], 1):
                d, f = l["debut"], l["fin"]
                print(f"    [{j}] ({d['x']}, {d['y']}, {d['z']}) → ({f['x']}, {f['y']}, {f['z']})  layer={l['layer']}")
        if b["attributs"]:
            print("  Attributs :")
            for tag, val in b["attributs"].items():
                print(f"    {tag:<25} = {val}")
        if b["parametres"]:
            print("  Paramètres dynamiques :")
            for nom, val in b["parametres"].items():
                print(f"    {nom:<25} = {val}")
    print("=" * 60)


if __name__ == "__main__":
    acad = get_autocad()
    ms   = get_model_space(acad)
    entites = lister_entites(ms)
    blocs   = collecter_blocs_dynamiques(ms, acad)
    afficher(entites)
    afficher_blocs(blocs)
    sauvegarder_json(
        entites=entites,
        blocs=blocs,
        chemin=Path(acad.ActiveDocument.FullName).parent / "Autocad Export",
        filename=Path(acad.ActiveDocument.FullName).stem,
    )