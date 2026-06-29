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


def collecter_blocs_dynamiques(model_space):
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

        blocs.append({
            "nom": entity.EffectiveName,
            "layer": entity.Layer,
            "attributs": get_attributs(entity),
            "parametres": get_parametres_dynamiques(entity),
        })
    return blocs


def sauvegarder_json(entites, blocs, chemin: str | Path, filename: str = "Default"):
    """
    Sauvegarde les données dans chemin.
    - Si chemin est un dossier (ou se termine sans .json), écrit chemin/filename.json
    - Si chemin est un fichier .json, écrit directement dans ce fichier
    Retourne le Path du fichier écrit.
    """
    chemin = Path(chemin)
    filename_stem = Path(filename).stem

    if chemin.suffix.lower() == ".json":
        # chemin est un fichier cible direct
        fichier = chemin
        fichier.parent.mkdir(parents=True, exist_ok=True)
    else:
        # chemin est un dossier
        # Supprimer si c'est un fichier orphelin (ancien bug)
        if chemin.exists() and not chemin.is_dir():
            chemin.unlink()
        chemin.mkdir(parents=True, exist_ok=True)
        fichier = chemin / f"{filename_stem}.json"

    data = {
        "resume_entites": entites,
        "blocs_dynamiques": blocs,
    }
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
    print("BLOCS DYNAMIQUES — Attributs & Paramètres")
    print("=" * 60)
    if not blocs:
        print("  Aucun bloc dynamique trouvé.")
    for i, b in enumerate(blocs, 1):
        print(f"\n[{i}] Bloc : {b['nom']}  (Layer: {b['layer']})")
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
    ms = get_model_space(acad)
    entites = lister_entites(ms)
    blocs = collecter_blocs_dynamiques(ms)
    afficher(entites)
    afficher_blocs(blocs)
    sauvegarder_json(
        entites=entites,
        blocs=blocs,
        chemin=Path(acad.ActiveDocument.FullName).parent / "Autocad Export",
        filename=Path(acad.ActiveDocument.FullName).stem,
    )
