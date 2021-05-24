import requests
import os

class Place:
    fields = ('address', 'description', 'latitude', 'longitude', 'photopath')

    def __init__(self, data=dict()):
        data = dict(data)
        self.__data = dict()
        for key, value in data.items():
            if key in self.fields:
                self.__data[key] = value
        self.clean()

    def get_addr_from_loc(self, location):
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {'latlng': f'{location[0]},{location[1]}', 'key': os.environ.get('GOOGLE_API')}
        res = requests.get(url, params=params)
        # FIX add error HANDLER
        data = res.json()
        return data['results'][0]['formatted_address']

    def clean(self):
        clean_data = {k: v for k, v in self.__data.items() if not v is None
                                                                and k in self.fields}
        self.clean_latlon()
        if not clean_data.get('address') and 'latitude' in clean_data and 'longitude' in clean_data:
            clean_data['address'] = self.get_addr_from_loc((clean_data['latitude'], clean_data['longitude']))
        self.__data = clean_data
        return clean_data.copy()

    def clean_latlon(self):
        if self.__data.get('latitude'):
            self.__data['latitude'] = float(self.__data['latitude'])
        if self.__data.get('longitude'):
            self.__data['longitude'] = float(self.__data['longitude'])

    @property
    def data(self):
        return self.clean().copy()

    @property
    def clean_data(self):
        clean_data = self.clean()
        if not clean_data.get('address') and not (self.latitude and self.longitude):
            raise ValueError('Place must contains address or location')
        return clean_data.copy()

    @property
    def buttons(self):
        data = self.data
        data.pop('longitude', None)
        data.pop('latitude', None)
        data.pop('photopath', None)
        if self.location:
            print(self.location)
            data['location'] = self.location
        if self.photopath:
            data['photo'] = self.photopath
        return tuple(data.keys())

    @property
    def latitude(self):
        return self.__data.get('latitude')

    @property
    def longitude(self):
        return self.__data.get("longitude")

    @property
    def location(self):
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))

    @property
    def photopath(self):
        return self.__data.get('photopath')

    @property
    def description(self):
        return self.__data.get('description', '')

    @property
    def address(self):
        self.clean()
        return self.__data.get('address', '')

    @location.setter
    def location(self, location):
        self.__data['latitude'] = float(location.latitude)
        self.__data['longitude'] = float(location.longitude)

    @photopath.setter
    def photopath(self, photopath):
        self.__data['photopath'] = photopath

    @description.setter
    def description(self, description):
        self.__data['description'] = description

    @address.setter
    def address(self, address):
        self.__data['address'] = address

    @latitude.setter
    def latitude(self, latitude):
        self.__data['latitude'] = float(latitude)

    @longitude.setter
    def longitude(self, longitude):
        self.__data['longitude'] = float(longitude)
