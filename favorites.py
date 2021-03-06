from nameko.web.handlers import http
from nameko.rpc import rpc, RpcProxy
from nameko.events import EventDispatcher
from nameko_mongodb import MongoDatabase
from werkzeug.wrappers import Request, Response
import json


class Favorites:
    # Vars

    name = "favorites"

    db = MongoDatabase()
    '''
        name of collection: 'favs';
        columns:
                '_id' - id of the user
                'favs_list' - the list:
                    [event_1_id, ..., event_m_id]
    '''

    logger_rpc = RpcProxy('logger')

    dispatch = EventDispatcher()
    '''
        calling for service 'uis' if new fav was made
    '''

    # Logic

    def _new_fav(self, fav_data) -> bool:
        '''
         fav_data is [user_id, event_id]
         Save info in database
         Returns True if new info is added, False otherwise
        '''
        user_id, event_id = fav_data
        collection = self.db["favs"]

        current_favs_list = collection.find_one(
            {"_id": user_id},
            {"favs_list": 1}
        )  # check whether this user is presented in db

        if current_favs_list:
            # this user is presented
            current_favs_list = current_favs_list["favs_list"]
            if event_id not in current_favs_list:
                # add event_id in the list
                current_favs_list.append(event_id)
                collection.update_one(
                    {'_id': user_id},
                    {'$set': {"favs_list": current_favs_list}}
                )
                return True
            # change nothing
            return False
        else:
            # this is the first fav
            collection.insert_one(
                {"_id": user_id, "favs_list": [event_id]}
            )
            return True

    def _cancel_fav(self, fav_data) -> bool:
        '''
         fav_data is [user_id, event_id]
         Delete info from database
         Returns True if some info is deleted, False otherwise
        '''
        user_id, event_id = fav_data
        collection = self.db["favs"]
        try:
            current_favs_list = collection.find_one(
                {"_id": user_id},
                {"favs_list": 1}
            )["favs_list"]
        except Exception:
            print(Exception)
            return False
        if event_id in current_favs_list:
            if len(current_favs_list) > 1:
                '''
                just delete one item in list
                '''
                current_favs_list.remove(event_id)
                collection.update_one(
                    {'_id': user_id},
                    {'$set': {"favs_list": current_favs_list}}
                )
            else:
                '''
                it was the last fav
                delete all record in db 
                '''
                collection.delete_one(
                    {"_id": user_id}
                )
            return True
        return False

    def _get_favs(self, user_id):
        collection = self.db["favs"]
        favs = collection.find_one(
            {"_id": user_id},
            {"favs_list": 1}
        )
        if favs:
            return favs["favs_list"]
        else:
            return None

    # API

    @rpc
    def new_fav(self, fav_data):
        '''
            Args: fav_data - [user_id, event_id] 
            dispatch to the uis - [user_id, event_id] 
        '''
        self.logger_rpc.log(self.name, self.new_fav.__name__,
                            fav_data, "Info", "Saving favorite")
        is_new_info = self._new_fav(fav_data)
        if is_new_info:
            self.dispatch("fav", fav_data)

    @rpc
    def cancel_fav(self, fav_data):
        '''
            Args: fav_data - [user_id, event_id] 
            dispatch to the uis - [user_id, event_id] 
        '''
        self.logger_rpc.log(self.name, self.cancel_fav.__name__,
                            fav_data, "Info", "Removing favorite")
        is_deleted_info = self._cancel_fav(fav_data)
        if is_deleted_info:
            self.dispatch("fav_cancel", fav_data)
        else:
            print('ERROR: we try to cancel a fav which we does not have gotten')

    @rpc
    def get_favs_by_id(self, user_id):
        '''
            Args: user_id
            Returns: [event_1_id, ..., event_n_id]
        '''
        return self._get_favs(user_id)

    @rpc
    def is_event_faved(self, user_id, event_id):
        '''
            Args: user_id, event_id
            Returns: bool
        '''
        favs = self._get_favs(user_id)
        if event_id in favs:
            return True
        return False

    @http("POST", "/new_fav")
    def new_fav_http(self, request: Request):
        '''
            POST http://localhost:8000/new_fav HTTP/1.1
            Content-Type: application/json

            [user_id, event_id]
        '''
        content = request.get_data(as_text=True)
        fav_data = json.loads(content)
        is_new_info = self._new_fav(fav_data)
        if is_new_info:
            self.dispatch("fav", fav_data)
        return Response(status=201)

    @http("POST", "/cancel_fav")
    def cancel_fav_http(self, request: Request):
        '''
            POST http://localhost:8000/cancel_fav HTTP/1.1
            Content-Type: application/json

            [user_id, event_id]
        '''
        content = request.get_data(as_text=True)
        fav_data = json.loads(content)
        is_deleted_info = self._cancel_fav(fav_data)
        if is_deleted_info:
            self.dispatch("fav_cancel", fav_data)
            return Response(status=201)
        '''
        else it turns out we try to cancel a fav which we does not have gotten
        '''
        return Response(status=404)

    @http("GET", "/get_favs/<id>")
    def get_favs_by_id_http(self, request: Request, id):
        '''
            GET http://localhost:8000/get_favs/<id> HTTP/1.1
            Content-Type: application/json
        '''
        favs = self._get_favs(id)
        return json.dumps(favs, ensure_ascii=False)

    @http("GET", "/is_faved/<user_id>/<event_id>")
    def is_event_faved_http(self, request: Request, user_id, event_id):
        '''
            GET http://localhost:8000/is_faved/<user_id>/<event_id> HTTP/1.1
            Content-Type: application/json
        '''
        favs = self._get_favs(user_id)
        if event_id in favs:
            return json.dumps(True, ensure_ascii=False)
        return json.dumps(False, ensure_ascii=False)
