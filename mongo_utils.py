from utils.conexion_mongo import db

def insertar_propiedades(lista_propiedades, tipo):
    """
    Inserta una lista de propiedades en la colección correspondiente según el tipo ("venta" o "arriendo").
    """
    if tipo not in ["venta", "arriendo"]:
        raise ValueError("El tipo debe ser 'venta' o 'arriendo'")

    coleccion = db[f"{tipo}"]
    resultado = coleccion.insert_many(lista_propiedades)
    print(f"✅ {len(resultado.inserted_ids)} propiedades insertadas en la colección '{coleccion.name}'")
