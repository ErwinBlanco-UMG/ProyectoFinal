// static/js/script.js

let map;
let markers = [];
let polylines = [];

function initMap() {
    const guatemala = { lat: 14.6349, lng: -90.5069 }; 
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 7,
        center: guatemala,
    });
    console.log("Google Map initialized.");
}

function toggleEstimatedStay() {
    const placeType = document.getElementById('add_place_type').value;
    const estimatedStayDiv = document.getElementById('estimated_stay_div');
    if (placeType === 'Turistico') {
        estimatedStayDiv.style.display = 'block';
        document.getElementById('estimated_stay_hours').setAttribute('required', 'required');
    } else {
        estimatedStayDiv.style.display = 'none';
        document.getElementById('estimated_stay_hours').removeAttribute('required');
    }
}

function toggleSearchFields() {
    const searchType = document.getElementById('search_type').value;
    const nameFields = document.getElementById('search_by_name_fields');
    const coordsFields = document.getElementById('search_by_coords_fields');

    if (searchType === 'name') {
        nameFields.style.display = 'block';
        coordsFields.style.display = 'none';
        document.getElementById('search_name').setAttribute('required', 'required');
        document.getElementById('search_latitude').removeAttribute('required');
        document.getElementById('search_longitude').removeAttribute('required');
        document.getElementById('search_tolerance').removeAttribute('required'); // No requerido para nombre
    } else { // coords
        nameFields.style.display = 'none';
        coordsFields.style.display = 'block';
        document.getElementById('search_name').removeAttribute('required');
        document.getElementById('search_latitude').setAttribute('required', 'required');
        document.getElementById('search_longitude').setAttribute('required', 'required');
        document.getElementById('search_tolerance').setAttribute('required', 'required');
    }
}

async function searchPlace(event) {
    event.preventDefault();

    const searchType = document.getElementById('search_type').value;
    const searchResultsDiv = document.getElementById('search_results');
    searchResultsDiv.innerHTML = ''; // Clear previous results
    clearMapElements(); // Clear existing markers/polylines from map

    let formData = new FormData();
    formData.append('search_type', searchType);

    if (searchType === 'name') {
        const nameQuery = document.getElementById('search_name').value;
        if (!nameQuery) {
            alert("Por favor, ingresa un nombre para buscar.");
            return;
        }
        formData.append('query', nameQuery);
    } else { // coords
        const latQuery = document.getElementById('search_latitude').value;
        const lonQuery = document.getElementById('search_longitude').value;
        const tolerance = document.getElementById('search_tolerance').value;
        if (!latQuery || !lonQuery || !tolerance) {
            alert("Por favor, ingresa latitud, longitud y tolerancia para buscar por coordenadas.");
            return;
        }
        formData.append('lat_query', latQuery);
        formData.append('lon_query', lonQuery);
        formData.append('tolerance', tolerance);
    }

    try {
        const response = await fetch('/search_place', {
            method: 'POST',
            body: formData
        });
        const results = await response.json();
        
        if (results.length === 0) {
            searchResultsDiv.innerHTML = '<p>No se encontraron lugares turísticos que coincidan.</p>';
        } else {
            const ul = document.createElement('ul');
            results.forEach(place => {
                const li = document.createElement('li');
                li.textContent = `${place.name} (ID: ${place.id}, Lat: ${place.latitude}, Lon: ${place.longitude}, Calificación: ${place.average_rating})`;
                ul.appendChild(li);

                // Add marker for found place
                addMarker({ lat: place.latitude, lng: place.longitude }, place.name, "🔍");
            });
            searchResultsDiv.appendChild(ul);
            if (results.length > 0) {
                // Centrar el mapa en el primer resultado encontrado
                map.setCenter({ lat: results[0].latitude, lng: results[0].longitude });
                map.setZoom(10); // Zoom in on the found place(s)
            }
        }
    } catch (error) {
        console.error('Error searching place:', error);
        searchResultsDiv.innerHTML = '<p>Hubo un error al buscar el lugar.</p>';
    }
}


async function getRecommendations(event) {
    event.preventDefault();

    const originLat = document.getElementById('origin_lat').value;
    const originLon = document.getElementById('origin_lon').value;
    const dailyBudget = document.getElementById('daily_budget').value;

    if (!originLat || !originLon || !dailyBudget) {
        alert("Por favor, ingresa todos los campos para las recomendaciones.");
        return;
    }

    const formData = new FormData();
    formData.append('origin_lat', originLat);
    formData.append('origin_lon', originLon);
    formData.append('daily_budget', dailyBudget);

    try {
        const response = await fetch('/get_recommendations', {
            method: 'POST',
            body: formData
        });
        const recommendations = await response.json();
        displayRecommendations(recommendations, { lat: parseFloat(originLat), lng: parseFloat(originLon) });
    } catch (error) {
        console.error('Error fetching recommendations:', error);
        alert('Hubo un error al obtener las recomendaciones. Consulta la consola para más detalles.');
    }
}

function displayRecommendations(recommendations, originPoint) {
    const recommendationsListDiv = document.getElementById('recommendations_list');
    recommendationsListDiv.innerHTML = ''; // Clear previous recommendations

    // Clear existing markers and polylines on the map
    clearMapElements();

    if (recommendations.length === 0) {
        recommendationsListDiv.innerHTML = '<p>No se encontraron recomendaciones que se ajusten a tus criterios.</p>';
        return;
    }

    const ul = document.createElement('ul');
    let routeCounter = 1;

    // Add an origin marker
    addMarker(originPoint, "Origen", "📍");

    recommendations.forEach(route => {
        const li = document.createElement('li');
        li.innerHTML = `<h3>Ruta Recomendada ${routeCounter} (Score: ${route.score}, Costo: Q${route.total_cost}, Tiempo: ${route.total_time_hours} hrs)</h3>`;
        
        const routeDetails = document.createElement('ul');
        let pathCoordinates = [];
        let previousPlace = originPoint;

        route.places.forEach(place => {
            const placeLi = document.createElement('li');
            placeLi.textContent = `- ${place.name} (Calificación: ${place.average_rating}, Precio: Q${place.price}, Estadía: ${place.estimated_stay_hours} hrs)`;
            routeDetails.appendChild(placeLi);

            const placeLocation = { lat: place.latitude, lng: place.longitude };
            addMarker(placeLocation, place.name, place.entity_type === 'Turistico' ? "🗺️" : "🏨"); // Add marker for each place

            // Add segment for polyline
            pathCoordinates.push(previousPlace);
            pathCoordinates.push(placeLocation);
            previousPlace = placeLocation;
        });

        // Draw polyline for the current route
        drawPolyline(pathCoordinates);

        li.appendChild(routeDetails);
        ul.appendChild(li);
        routeCounter++;
    });

    recommendationsListDiv.appendChild(ul);
    map.setCenter(originPoint); 
    map.setZoom(8); 
}

function addMarker(location, title, iconText) {
    const marker = new google.maps.Marker({
        position: location,
        map: map,
        title: title,
        icon: {
            url: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='24' height='24'%3E%3Ctext x='0' y='20' font-size='20'%3E${iconText}%3C/text%3E%3C/svg%3E`,
            scaledSize: new google.maps.Size(24, 24)
        }
    });
    markers.push(marker);
}

function drawPolyline(pathCoordinates) {
    const polyline = new google.maps.Polyline({
        path: pathCoordinates,
        geodesic: true,
        strokeColor: '#FF0000',
        strokeOpacity: 0.8,
        strokeWeight: 3,
        map: map
    });
    polylines.push(polyline);
}

function clearMapElements() {
    markers.forEach(marker => marker.setMap(null));
    markers = [];
    polylines.forEach(polyline => polyline.setMap(null));
    polylines = [];
}


// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar el estado de los campos de agregar y buscar
    toggleEstimatedStay(); 
    toggleSearchFields(); 

    const recommendationForm = document.getElementById('recommendationForm');
    if (recommendationForm) {
        recommendationForm.addEventListener('submit', getRecommendations);
    }

    const searchPlaceForm = document.getElementById('searchPlaceForm');
    if (searchPlaceForm) {
        searchPlaceForm.addEventListener('submit', searchPlace);
    }
});