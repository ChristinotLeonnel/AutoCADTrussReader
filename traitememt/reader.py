import json 

with open('AutoCADExport/2DTruss.json', 'r') as file:
    data = json.load(file) 

Filaire = data["blocs_dynamiques"] 

ElementSupporteur = [elmt for elmt in Filaire if elmt["nom"] == "Element Filaire"]