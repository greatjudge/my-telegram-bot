import requests
import os

from collections import defaultdict
from bases import MysqlBase
from place import Place

class State:

    START, ADD, LIST, RESET, DEST = 'start', 'add', 'list', 'reset', 'destination'
    YES, NO, EXIT = 'yes', 'no', 'exit'
    SAVE, ADDR, LOC, DES, PHOTO, PHOTOPATH = 'save', 'address', 'location', 'description', 'photo', 'photopath'
    BACK, EXIT = 'back', 'exit'
    LIST_PLACE = 'list_place'

    STATES = (START, SAVE, ADDR, LOC, ADD, DES, PHOTO, LIST, RESET, DEST, LIST_PLACE)
    state_add = (ADD, ADDR, LOC, DES, PHOTO)
    buttons_add = state_add[1:] + (SAVE, )
    buttons_confirm = (YES, NO)

    def __init__(self):
        self.__states = defaultdict(lambda : self.START)
        self.__user_place = defaultdict(lambda : Place())
        self.__user_places = dict()
        self.__user_count = dict()
        self.__base=MysqlBase()
        self.__base.create_tables()
        self.__base.init_photos()

    def list_places(self, uid):
        return self.__user_places.get(str(uid))

    def list_place(self, uid):
        return self.__user_places.get(str(uid))

    def list_set_places(self, uid, places):
        self.__user_places[str(uid)] = places

    def check(self, id, state):
        return self.__states[id] == state

    def in_stateadd(self, id):
        return self.get_state(id) in self.state_add

    def get_state(self, id):
        return self.__states[id]

    def set_state(self, id, state):
        if state in self.STATES:
            self.__states[id] = state
        else:
            raise ValueError('Unknown state')

    def in_save(self, state):
        return state == self.SAVE

    def save_place(self, user_id):
        self.__base.add(user_id, self.__user_place[str(user_id)])
        self.__user_place[user_id] = Place()
        self.set_state(user_id, self.START)

    def places(self, user_id):
        return self.__user_place[str(user_id)]

    def set_place(self, user_id, data=None):
        if isinstance(data, Place):
            print('in set place', data, user_id)
            self.__user_place[str(user_id)] = data
        else:
            self.__user_place[str(user_id)] = Place(data) if not data is None else Place()

    def count(self, user_id):
        return self.__user_count[user_id]

    def set_count(self, user_id, count):
        self.__user_count[user_id] = count

    def req_google(self, current_location, place_list):
        # FIX add error handler
        url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
        origin = f'{current_location[0]},{current_location[1]}'
        destinations = '|'.join([f'{place.latitude},{place.longitude}' for place in place_list])
        params = {'origins': origin, 'destinations': destinations, 'key': os.environ.get('GOOGLE_API')}
        res = requests.get(url, params=params)
        return res.json()

    def shortest_places(self, user_id, location, count=5):
        # FIX something... It`s unreadble
        place_list = self.__base.list(user_id, -1)
        if not place_list:
            return []
        else:
            cur_loc = (location.latitude, location.longitude)
            place_list = list([place for place in place_list if place.location])
            data_dict = self.req_google(cur_loc, place_list)
            if data_dict['status'].lower() == 'ok':
                all = (zip(place_list, zip(data_dict['destination_addresses'],
                                            data_dict['rows'][0]['elements'])))
                all = [(place.location, (place.address, element['distance']['value']))
                                    for place, (addr, element) in all if
                                                                      element['status'].lower() == 'ok'
                                                                      and addr
                                                                      and place.location]
                all.sort(key=lambda x: x[0][1])
                return all[:count]
            else:
                return []

    @property
    def base(self):
        return self.__base
