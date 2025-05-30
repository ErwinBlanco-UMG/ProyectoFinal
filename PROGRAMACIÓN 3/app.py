# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from utils.data_loader import load_data_from_csv, load_user_ratings_from_csv, export_b_tree_to_csv, export_user_ratings_to_csv
from classes.b_tree import BTree
from classes.place import Hospedaje, LugarTuristico
from utils.route_calculator import find_best_routes
from utils.map_utils import haversine_distance # Aunque haversine ya no se usa para rutas, es buena práctica tenerla
from config import Maps_API_KEY
import os
import graphviz
import googlemaps # Asegúrate de tener 'google-maps-services-python' instalado (pip install google-maps-services-python)

app = Flask(__name__)

# Initialize your B-trees globally
hospedajes_b_tree = BTree(order=3)
turisticos_b_tree = BTree(order=3)

# Define data paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
HOSPEDAJE_CSV = os.path.join(DATA_DIR, 'hospedajes.csv')
TURISTICOS_CSV = os.path.join(DATA_DIR, 'turisticos.csv')
CALIFICACIONES_CSV = os.path.join(DATA_DIR, 'calificaciones.csv')

# Crea la carpeta 'data' si no existe
os.makedirs(DATA_DIR, exist_ok=True)

# Crea archivos CSV vacíos con encabezados si no existen.
for filename in [HOSPEDAJE_CSV, TURISTICOS_CSV, CALIFICACIONES_CSV]:
    if not os.path.exists(filename):
        print(f"Creating empty CSV file with headers: {filename}")
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if 'hospedajes' in filename:
                f.write('id,name,latitude,longitude,price,average_rating\n')
            elif 'turisticos' in filename:
                f.write('id,name,latitude,longitude,price,average_rating,estimated_stay_hours\n')
            elif 'calificaciones' in filename:
                f.write('place_id,user_id,rating,comment\n')


# Inicializa el cliente de Google Maps API
gmaps = googlemaps.Client(key=Maps_API_KEY)


@app.route('/')
def index():
    turistic_places = turisticos_b_tree.get_all_elements()
    return render_template('index.html',
                           Maps_api_key=Maps_API_KEY,
                           turistic_places=turistic_places)

@app.route('/upload_data', methods=['POST'])
def upload_data():
    print("Received request to /upload_data")

    if 'hospedajes_file' in request.files and request.files['hospedajes_file'].filename != '':
        file = request.files['hospedajes_file']
        print(f"Hospedajes file received: {file.filename}")
        try:
            file.save(HOSPEDAJE_CSV)
            print(f"Hospedajes file saved to {HOSPEDAJE_CSV}")
            hospedajes_b_tree.__init__(order=3)
            load_data_from_csv(HOSPEDAJE_CSV, "Hospedaje", hospedajes_b_tree)
            print(f"Hospedajes data reloaded from {HOSPEDAJE_CSV}")
        except Exception as e:
            print(f"Error saving/loading hospedajes file: {e}")
    else:
        print("No Hospedajes file provided or filename was empty.")

    if 'turisticos_file' in request.files and request.files['turisticos_file'].filename != '':
        file = request.files['turisticos_file']
        print(f"Turisticos file received: {file.filename}")
        try:
            file.save(TURISTICOS_CSV)
            print(f"Turisticos file saved to {TURISTICOS_CSV}")
            turisticos_b_tree.__init__(order=3)
            load_data_from_csv(TURISTICOS_CSV, "Turistico", turisticos_b_tree)
            print(f"Turisticos data reloaded from {TURISTICOS_CSV}")
        except Exception as e:
            print(f"Error saving/loading turisticos file: {e}")
    else:
        print("No Turisticos file provided or filename was empty.")

    if 'ratings_file' in request.files and request.files['ratings_file'].filename != '':
        file = request.files['ratings_file']
        print(f"Ratings file received: {file.filename}")
        try:
            file.save(CALIFICACIONES_CSV)
            print(f"Ratings file saved to {CALIFICACIONES_CSV}")
            load_user_ratings_from_csv(CALIFICACIONES_CSV, turisticos_b_tree)
            print(f"User ratings reloaded from {CALIFICACIONES_CSV}")
        except Exception as e:
            print(f"Error saving/loading ratings file: {e}")
    else:
        print("No Ratings file provided or filename was empty.")

    export_b_tree_to_csv(hospedajes_b_tree, HOSPEDAJE_CSV, "Hospedaje")
    export_b_tree_to_csv(turisticos_b_tree, TURISTICOS_CSV, "Turistico")
    export_user_ratings_to_csv(turisticos_b_tree, CALIFICACIONES_CSV)

    return redirect(url_for('index'))

@app.route('/add_place', methods=['POST'])
def add_place():
    place_type = request.form['place_type']
    place_id = request.form['id']
    name = request.form['name']
    # Retrieve values from form, giving them clear local variable names
    # (e.g., latitude_from_form, longitude_from_form)
    # The form inputs are named 'latitude' and 'longitude', which is good.
    latitude_from_form = float(request.form['latitude'])
    longitude_from_form = float(request.form['longitude'])
    price = float(request.form['price'])
    rating = float(request.form['average_rating'])

    if place_type == 'Hospedaje':
        # Pass the values using the parameter names expected by Hospedaje's __init__
        new_place = Hospedaje(
            id=place_id,
            name=name,
            latitude=latitude_from_form,  # Changed from 'lat=lat'
            longitude=longitude_from_form, # Changed from 'lon=lon'
            price=price,
            rating=rating
        )
        hospedajes_b_tree.insert(new_place.id, new_place)
        export_b_tree_to_csv(hospedajes_b_tree, HOSPEDAJE_CSV, "Hospedaje")
    elif place_type == 'Turistico':
        estimated_stay = float(request.form['estimated_stay_hours'])
        # Pass the values using the parameter names expected by LugarTuristico's __init__
        new_place = LugarTuristico(
            id=place_id,
            name=name,
            latitude=latitude_from_form,  # Changed from 'lat=lat'
            longitude=longitude_from_form, # Changed from 'lon=lon'
            price=price,
            rating=rating,
            estimated_stay_hours=estimated_stay
        )
        turisticos_b_tree.insert(new_place.id, new_place)
        export_b_tree_to_csv(turisticos_b_tree, TURISTICOS_CSV, "Turistico")

    print(f"Added new {place_type}: {name} (ID: {place_id})")
    return redirect(url_for('index'))

@app.route('/rate_place', methods=['POST'])
def rate_place():
    place_id = request.form['place_id']
    user_rating = float(request.form['user_rating'])
    comment = request.form.get('comment', '')

    place = turisticos_b_tree.search(place_id)
    if place:
        place.update_rating(user_rating, comment)
        print(f"Updated rating for {place.name} (ID: {place.id}) with new rating: {user_rating}")

        export_b_tree_to_csv(turisticos_b_tree, TURISTICOS_CSV, "Turistico")
        export_user_ratings_to_csv(turisticos_b_tree, CALIFICACIONES_CSV)
    else:
        print(f"Place with ID {place_id} not found for rating.")

    return redirect(url_for('index'))

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    try:
        origin_lat = float(request.form['origin_lat'])
        origin_lon = float(request.form['origin_lon'])
        daily_budget = float(request.form['daily_budget'])

        print(f"DEBUG: Recommendation request - Origin: ({origin_lat}, {origin_lon}), Budget: {daily_budget}")

        turisticos_list = turisticos_b_tree.get_all_elements()
        print(f"DEBUG: Number of turistic places loaded in B-tree: {len(turisticos_list)}")

        if not turisticos_list:
            print("DEBUG: No turistic places found in B-tree for recommendations.")
            return jsonify({"message": "No hay lugares turísticos disponibles para generar recomendaciones."}), 200

        # Ahora pasamos el objeto gmaps a la función find_best_routes
        recommendations = find_best_routes(origin_lat, origin_lon, daily_budget, turisticos_list, gmaps)
        print(f"DEBUG: Generated recommendations: {recommendations}")

        return jsonify(recommendations)
    except Exception as e:
        print(f"ERROR in get_recommendations: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/export_entities')
def export_entities():
    export_b_tree_to_csv(hospedajes_b_tree, HOSPEDAJE_CSV, "Hospedaje")
    export_b_tree_to_csv(turisticos_b_tree, TURISTICOS_CSV, "Turistico")
    export_user_ratings_to_csv(turisticos_b_tree, CALIFICACIONES_CSV)
    return "All entity data exported to CSV files in the 'data/' directory. Check your server's 'data/' folder."

@app.route('/export_structure')
def export_structure():
    dot_source = turisticos_b_tree.to_dot()
    graph = graphviz.Source(dot_source)
    try:
        output_path = os.path.join(app.root_path, 'static', 'b_tree_structure')
        graph.render(output_path, view=False, format='png')
        print(f"B-tree structure exported to {output_path}.png")
        return send_file(output_path + '.png', mimetype='image/png', as_attachment=True, download_name='b_tree_structure.png')
    except Exception as e:
        print(f"Error exporting Graphviz: {e}")
        return f"Error generating B-tree structure: {e}. Make sure Graphviz is installed (e.g., 'brew install graphviz' on macOS, 'sudo apt-get install graphviz' on Debian/Ubuntu, or from graphviz.org/download/)."

if __name__ == '__main__':
    app.run(debug=True)