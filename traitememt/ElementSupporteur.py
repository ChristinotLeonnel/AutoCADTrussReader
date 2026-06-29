from reader import ElementSupporteur
from Inertie import Inertia 
from utils import local_to_global, To_SI

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
    Info["L"] = To_SI("m", float(element["parametres"]["Longueur"]))
    Info["E"] = To_SI("MPa", float(element["attributs"]["E"]))
    Info["I"] = Inertia(sect_param)  # A faire

    Info["Local_Position"] = {
        "end_point" : [round(element["parametres"]["End_Point X"],4), round(element["parametres"]["End_Point Y"],4), 0],
        "base_point" : [round(element["parametres"]["Base_Point X"],4), round(element["parametres"]["Base_Point Y"],4), 0]
    }

    base_point = (element["insertion"]["x"], element["insertion"]["y"], element["insertion"]["z"])
    end_point = (element["parametres"]["End_Point X"], element["parametres"]["End_Point Y"], 0)  # Default to 0 if the key is not present  

    Info["Globale_Position"] = {
        "end_point" : local_to_global(base_point, end_point, element["rotation"]),
        "base_point" : list(base_point) 
    }



    return Info

for i in ElementSupporteur:
    print(get_complieted_info(i))

