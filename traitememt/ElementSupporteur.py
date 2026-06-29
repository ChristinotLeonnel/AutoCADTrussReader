from reader import ElementSupporteur
from Inertie import Inertia 

def get_section(element):
    """
    This function retrieves the section parameters of a given element.

    Args:
        element (dict): A dictionary representing an element.

    Returns:
        dict: A dictionary containing the section type of the element.
    """
    return element.get("parametres", {}).get("Section", {})

def get_section_parametre(element):
    """
    This function retrieves the section parameters of a given element based on its section type.    

    Args:
        element (dict): A dictionary representing an element.

    Returns:
        dict: A dictionary containing the section parameters of the element.
    """
    section_type = get_section(element) 
    keys = element["parametres"].keys()
    dico = {}
    dico["section"] = section_type
    for key in keys:
        if key.endswith(section_type): 
            dico[key] = element["parametres"][key]
        if key.endswith(section_type + " "):
            # Remove trailing whitespace from the key and add it to the dictionary
            dico[key.rstrip()] = element["parametres"][key]

    return dico

def get_complieted_info(element):
    sect_param = get_section_parametre(element) 
    Info = {}
    Info["L"] = element["parametres"]["Longueur"] 
    Info["E"] = element["attributs"]["E"] 
    Info["I"] = Inertia(sect_param)  # A faire 
    Info 


for i in ElementSupporteur:
    print(get_section_parametre(i))

