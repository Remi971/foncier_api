#!/usr/bin/env python3
import requests
from enum import Enum
from fastapi.testclient import TestClient
from main  import app
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

# DATABASE_URL = "sqlite:///:memory:"

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={
#         "check_same_thread": False,
#     },
#     poolclass=StaticPool,
#     )
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
client = TestClient(app)

class Method(Enum):
    """METHODS"""
    def __str__(self):
        return str(self.value)
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

def testRequest(
    label : str,
    params: dict | None,
    id: int | None,
    route: str,
    method: Method
    ):
    '''
    Function for testing http request of APIs
    
    '''
    data = {
        "base_url": "http://127.0.0.1:8080" + route,
        "url_params" : "",
        "complete_url": "",
    }
    if params :
        params_list = [f'{x}={y}' for x, y in params.items()]
        data["url_params"] = "?" + "&".join(params_list)

    if id:
        data["complete_url"] = f"{id}{data["url_params"]}"
    else:
        data["complete_url"] = data["url_params"]
    response = ""
    match method:
        case Method.GET:
            try:
                response = client.get(f"{data["base_url"]}{data["complete_url"]}")
            except Exception as error:
                print(error)
        case Method.POST:
            try:
                client.post("")
            except Exception as error:
                print(error)
        case Method.PUT:
            ...
        case Method.DELETE:
            ...
        case _:
            print(f"Bad method : {method}")
            raise NameError(f"Bad method : {method}. Use only {Method}")
    # try:
    #     print("response", response)
    #     print(
    #         label,
    #         response.text,
    #         sep='\n'
    #     )
    # except Exception as error:
    #     print(error)
    print(response.text)
    
if __name__ == "__main__": 
    # Test GET requests /onlyparams
    testRequest(
        label="GET /onlyparams",
        params={
            "param1": 23, 
            "param2": "Bonjour"}, 
        id=None, 
        route="/onlyparams",
        method=Method.GET),
    
    # testRequest(
    #     label="Test Add Data",
    #     params=None,
    #     id=None,
    #     route="/data/add/13010",
    #     method=Method.GET.value
    # )

    # testRequest(
    #     label="get_data",
    #     params=None,
    #     id="84056",
    #     route="/data/add/sqlite/",
    #     method=Method.GET
    #     )
    testRequest(
        label="Test sql query",
        params=None,
        id=None,
        route="/process/potentiel",
        method=Method.GET
        
    )
    
    