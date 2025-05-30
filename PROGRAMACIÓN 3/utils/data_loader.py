# utils/data_loader.py
import csv
from classes.place import Hospedaje, LugarTuristico, UserRating # Asegúrate que esta ruta sea correcta

def load_data_from_csv(filepath, entity_type, b_tree_instance):
    """
    Carga datos de un archivo CSV en un B-tree.
    """
    # Reinicia el B-tree si ya tiene elementos para asegurar una carga limpia
    # Pequeña corrección aquí, la condición estaba incorrecta.
    if b_tree_instance.root is not None:
        b_tree_instance.__init__(order=b_tree_instance.order)

    print(f"--- Attempting to load {entity_type} data from {filepath} ---")

    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                print(f"Warning: {filepath} is empty or has no headers.")
                return

            print(f"Detected headers for {filepath}: {reader.fieldnames}")

            for row in reader:
                try:
                    # Intenta convertir la primera columna a un número para ver si es un ID válido
                    # Este chequeo puede ser más robusto si los IDs no son numéricos
                    _ = row[reader.fieldnames[0]] # Solo para ver si el campo existe

                    if entity_type == "Hospedaje":
                        hospedaje = Hospedaje(
                            id=row['id'],
                            name=row['name'],
                            latitude=float(row['latitude']),
                            longitude=float(row['longitude']),
                            price=float(row['price']),
                            rating=float(row['average_rating'])
                        )
                        b_tree_instance.insert(hospedaje.id, hospedaje)
                    elif entity_type == "Turistico":
                        turistico = LugarTuristico(
                            id=row['id'],
                            name=row['name'],
                            latitude=float(row['latitude']),
                            longitude=float(row['longitude']),
                            price=float(row['price']),
                            rating=float(row['average_rating']),
                            estimated_stay_hours=float(row.get('estimated_stay_hours', 0))
                        )
                        b_tree_instance.insert(turistico.id, turistico)
                    print(f"Successfully inserted {row['id']} ({row['name']}) into {entity_type} B-tree.")
                except KeyError as ke:
                    print(f"Skipping row due to missing column '{ke}' in {filepath}: {row}")
                except ValueError as ve:
                    print(f"Skipping row due to data type error in {filepath}: {ve} in row {row}")
                except Exception as e:
                    print(f"Skipping row due to unexpected error in {filepath}: {e} in row {row}")

        print(f"--- Finished loading {len(b_tree_instance.get_all_elements())} {entity_type} records from {filepath} ---")

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"An unexpected error occurred while loading {filepath}: {e}")

def load_user_ratings_from_csv(filepath, turisticos_b_tree_instance):
    """
    Carga las calificaciones de los usuarios y las asocia a los lugares turísticos.
    """
    print(f"--- Attempting to load User Ratings from {filepath} ---")
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                print(f"Warning: {filepath} is empty or has no headers.")
                return

            for row in reader:
                try:
                    place_id = row['place_id']
                    user_id = row['user_id']
                    rating = float(row['rating'])
                    comment = row.get('comment', '')

                    place = turisticos_b_tree_instance.search(place_id)
                    if place:
                        # Asegúrate de que place.ratings sea una lista de objetos UserRating
                        place.ratings.append(UserRating(place_id, user_id, rating, comment))
                        # Recalcular el average_rating
                        total_rating = sum(r.rating for r in place.ratings)
                        place.average_rating = total_rating / len(place.ratings)
                        # print(f"Loaded rating for {place.name}: {rating}")
                    else:
                        print(f"Warning: Place ID {place_id} not found in B-tree for rating: {row}")
                except KeyError as ke:
                    print(f"Skipping rating row due to missing column '{ke}': {row}")
                except ValueError as ve:
                    print(f"Skipping rating row due to data type error: {ve} in row {row}")
                except Exception as e:
                    print(f"Skipping rating row due to unexpected error: {e} in row {row}")

        print(f"--- Finished loading User Ratings from {filepath} ---")

    except FileNotFoundError:
        print(f"Error: User ratings file not found at {filepath}")
    except Exception as e:
        print(f"An unexpected error occurred while loading user ratings from {filepath}: {e}")


def export_b_tree_to_csv(b_tree_instance, filepath, entity_type):
    """
    Exporta los datos de un B-tree a un archivo CSV.
    """
    print(f"--- Attempting to export {entity_type} data to {filepath} ---")
    elements = b_tree_instance.get_all_elements()
    if not elements:
        print(f"No {entity_type} elements to export.")
        # Asegurarse de crear el archivo con encabezado si no hay datos
        if entity_type == "Hospedaje":
            fieldnames = ['id', 'name', 'latitude', 'longitude', 'price', 'average_rating']
        elif entity_type == "Turistico":
            fieldnames = ['id', 'name', 'latitude', 'longitude', 'price', 'average_rating', 'estimated_stay_hours']
        else:
            fieldnames = [] # No debería pasar
        if fieldnames:
             with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
        return

    # Define headers based on entity type
    if entity_type == "Hospedaje":
        fieldnames = ['id', 'name', 'latitude', 'longitude', 'price', 'average_rating']
    elif entity_type == "Turistico":
        fieldnames = ['id', 'name', 'latitude', 'longitude', 'price', 'average_rating', 'estimated_stay_hours']
    else:
        print(f"Unknown entity type: {entity_type}. Cannot export.")
        return

    try:
        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for element in elements:
                writer.writerow(element.to_dict())
        print(f"--- Successfully exported {len(elements)} {entity_type} records to {filepath} ---")
    except Exception as e:
        print(f"Error exporting {entity_type} to CSV: {e}")

def export_user_ratings_to_csv(turisticos_b_tree_instance, filepath):
    """
    Exporta todas las calificaciones de usuario asociadas a lugares turísticos a un archivo CSV.
    """
    print(f"--- Attempting to export User Ratings to {filepath} ---")
    all_ratings = []
    turisticos = turisticos_b_tree_instance.get_all_elements()
    for turistico in turisticos:
        for rating_obj in turistico.ratings:
            all_ratings.append(rating_obj.to_dict())

    if not all_ratings:
        print("No user ratings to export.")
        # Asegurarse de crear el archivo con encabezado si no hay datos
        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['place_id', 'user_id', 'rating', 'comment'])
            writer.writeheader()
        return

    fieldnames = ['place_id', 'user_id', 'rating', 'comment']
    try:
        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for rating_data in all_ratings:
                writer.writerow(rating_data)
        print(f"--- Successfully exported {len(all_ratings)} user ratings to {filepath} ---")
    except Exception as e:
        print(f"Error exporting user ratings to CSV: {e}")