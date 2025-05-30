# utils/route_calculator.py

# Ya no necesitamos haversine_distance aquí si usamos la API de Google Maps para distancias
# from utils.map_utils import haversine_distance

def find_best_routes(origin_lat, origin_lon, daily_budget, turistic_places, gmaps_client):
    """
    Encuentra las mejores rutas de lugares turísticos basadas en el presupuesto, la ubicación,
    el tiempo de viaje y priorizando calificación.
    """
    print(f"DEBUG(route_calculator): find_best_routes called with budget {daily_budget} and {len(turistic_places)} places.")

    origin_coords = f"{origin_lat},{origin_lon}"
    recommended_places_with_details = []

    # Constantes para el cálculo de costos (ejemplo, ajusta según necesidad real)
    COSTO_POR_KM_GASOLINA = 1.21 # Precio de gasolina por km en Q (referencia de Guatemala)
    COSTO_ESTACIONAMIENTO_POR_HORA = 15.0 # Costo de estacionamiento en Q/hora en Antigua
    TIEMPO_ESTIMADO_VISITA_MIN = 1 # Consideramos al menos 1 hora de estacionamiento si hay visita

    for place in turistic_places:
        destination_coords = f"{place.latitude},{place.longitude}"
        try:
            # Obtener direcciones y tiempo de viaje usando Google Maps API
            directions_result = gmaps_client.directions(
                origin=origin_coords,
                destination=destination_coords,
                mode="driving" # Puedes cambiar a "walking", "bicycling", "transit"
            )

            travel_duration_text = "N/A"
            travel_distance_text = "N/A"
            travel_duration_seconds = 0
            travel_distance_meters = 0

            if directions_result and len(directions_result) > 0 and 'legs' in directions_result[0]:
                leg = directions_result[0]['legs'][0]
                travel_duration_text = leg['duration']['text']
                travel_duration_seconds = leg['duration']['value']
                travel_distance_text = leg['distance']['text']
                travel_distance_meters = leg['distance']['value']

                # Calcular costo estimado de viaje
                # Convertir metros a km
                distance_km = travel_distance_meters / 1000
                travel_cost = distance_km * COSTO_POR_KM_GASOLINA

                # Estacionamiento: asumimos una hora de estacionamiento si el lugar es visitable y tiene precio
                # Esto es una simplificación, puedes ajustarlo.
                if place.price > 0 or place.estimated_stay_hours > 0:
                     travel_cost += COSTO_ESTACIONAMIENTO_POR_HORA * max(TIEMPO_ESTIMADO_VISITA_MIN, place.estimated_stay_hours)


                total_estimated_cost = place.price + travel_cost

                if total_estimated_cost <= daily_budget:
                    recommended_places_with_details.append({
                        'place': place,
                        'travel_duration_text': travel_duration_text,
                        'travel_duration_seconds': travel_duration_seconds,
                        'travel_distance_text': travel_distance_text,
                        'travel_distance_meters': travel_distance_meters,
                        'travel_cost': travel_cost,
                        'total_estimated_cost': total_estimated_cost # Nuevo: costo total (entrada + viaje)
                    })
                    print(f"DEBUG(route_calculator): Added {place.name}. Total cost: {total_estimated_cost}. Travel time: {travel_duration_text}")
                else:
                    print(f"DEBUG(route_calculator): Skipping {place.name}. Total cost ({total_estimated_cost}) exceeds budget ({daily_budget}).")

            else:
                print(f"DEBUG(route_calculator): Could not get directions for {place.name} from origin.")

        except Exception as e:
            print(f"ERROR getting directions for {place.name}: {e}")
            continue # Continúa con el siguiente lugar si hay un error con la API

    if not recommended_places_with_details:
        print("DEBUG(route_calculator): No places found within budget or reachable.")
        return []

    # Ordenar: primero por calificación (descendente), luego por costo total (ascendente), luego por tiempo de viaje (ascendente)
    # Cambiado el orden para que la calificación sea el primer criterio de ordenación principal
    recommended_places_with_details.sort(
        key=lambda x: (-x['place'].average_rating, x['total_estimated_cost'], x['travel_duration_seconds'])
    )

    # Seleccionar los top 3, o todos si hay menos
    final_recommendations = []
    count = 0
    for item in recommended_places_with_details:
        if count < 3: # Limita a un máximo de 3 recomendaciones
            place_dict = item['place'].to_dict() # Asegúrate de que to_dict() existe y es completo
            place_dict['travel_duration'] = item['travel_duration_text']
            place_dict['travel_distance'] = item['travel_distance_text']
            place_dict['estimated_travel_cost'] = round(item['travel_cost'], 2) # Redondear para mejor visualización
            place_dict['total_cost_for_visit'] = round(item['total_estimated_cost'], 2) # Redondear
            final_recommendations.append(place_dict)
            count += 1
        else:
            break

    print(f"DEBUG(route_calculator): Final recommendations count: {len(final_recommendations)}")
    return final_recommendations