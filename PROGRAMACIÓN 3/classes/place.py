# classes/place.py

class Place:
    def __init__(self, id, name, latitude, longitude, price, rating):
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.price = price
        self.average_rating = rating
        self.ratings = [] # Para almacenar objetos UserRating

    def update_rating(self, new_rating, comment=""):
        # Esto es una simplificación; en un sistema real, querrías una lista de UserRating
        # y recalcular el promedio. Por ahora, solo actualiza el promedio.
        # Asumiendo que 'ratings' es una lista de UserRating objetos
        self.ratings.append(UserRating(self.id, "some_user", new_rating, comment)) # 'some_user' es un placeholder
        total_rating = sum(r.rating for r in self.ratings)
        self.average_rating = total_rating / len(self.ratings) if self.ratings else 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'price': self.price,
            'average_rating': self.average_rating,
        }

class Hospedaje(Place):
    def __init__(self, id, name, latitude, longitude, price, rating):
        super().__init__(id, name, latitude, longitude, price, rating)

    def to_dict(self):
        return super().to_dict()

class LugarTuristico(Place):
    def __init__(self, id, name, latitude, longitude, price, rating, estimated_stay_hours=0):
        super().__init__(id, name, latitude, longitude, price, rating)
        self.estimated_stay_hours = estimated_stay_hours
        # Cargar calificaciones existentes si las hay, o inicializar lista vacía
        self.ratings = []

    def to_dict(self):
        data = super().to_dict()
        data['estimated_stay_hours'] = self.estimated_stay_hours
        return data

class UserRating:
    def __init__(self, place_id, user_id, rating, comment=""):
        self.place_id = place_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment

    def to_dict(self):
        return {
            'place_id': self.place_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment
        }