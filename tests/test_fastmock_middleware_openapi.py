import pytest

from tests.clients import (decorator_client, decorator_initialization_client,
                           middleware_client, header_client)

swagger_json = ""

@pytest.mark.parametrize("get_client", [
    middleware_client.get_client,
    decorator_client.get_client,
    decorator_initialization_client.get_client,
    header_client.get_client
])
def test_fastmock_openapi_working(get_client):
    response = get_client().get("/openapi.json")
    assert response.status_code == 200
    assert (response.json() ==
            {
                'openapi': '3.1.0',
                'info': {
                    'title': 'FastAPI',
                    'version': '0.1.0'
                },
                'paths': {
                    '/list': {
                        'get': {
                            'summary': 'Get Device List',
                            'operationId': 'get_device_list_list_get',
                            'responses': {
                                '200': {
                                    'description': 'Successful Response',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'items': {
                                                    '$ref': '#/components/schemas/Device'
                                                },
                                                'type': 'array',
                                                'title': 'Response 200 Get Device List List Get'
                                            }
                                        }
                                    }
                                },
                                '404': {
                                    'description': 'Not Found',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                '$ref': '#/components/schemas/DeviceNotFoundResponse'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    '/dict': {
                        'get': {
                            'summary': 'Get Device',
                            'operationId': 'get_device_dict_get',
                            'responses': {
                                '200': {
                                    'description': 'Successful Response',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'additionalProperties': {
                                                    '$ref': '#/components/schemas/Device'
                                                },
                                                'type': 'object',
                                                'title': 'Response 200 Get Device Dict Get'
                                            }
                                        }
                                    }
                                },
                                '404': {
                                    'description': 'Not Found',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                '$ref': '#/components/schemas/DeviceNotFoundResponse'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    '/device': {
                        'get': {
                            'summary': 'Get Device',
                            'operationId': 'get_device_device_get',
                            'responses': {
                                '200': {
                                    'description': 'Successful Response',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                '$ref': '#/components/schemas/Device'
                                            }
                                        }
                                    }
                                },
                                '404': {
                                    'description': 'Not Found',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                '$ref': '#/components/schemas/DeviceNotFoundResponse'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    '/str': {
                        'get': {
                            'summary': 'Get Str',
                            'operationId': 'get_str_str_get',
                            'responses': {
                                '200': {
                                    'description': 'Successful Response',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'type': 'string',
                                                'title': 'Response 200 Get Str Str Get'
                                            }
                                        }
                                    }
                                },
                                '404': {
                                    'description': 'Not Found',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                '$ref': '#/components/schemas/DeviceNotFoundResponse'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    '/int': {
                        'get': {
                            'summary': 'Get Int',
                            'operationId': 'get_int_int_get',
                            'responses': {
                                '200': {
                                    'description': 'Successful Response',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'type': 'integer',
                                                'title': 'Response 200 Get Int Int Get'
                                            }
                                        }
                                    }
                                },
                                '404': {
                                    'description': 'Not Found',
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                '$ref': '#/components/schemas/DeviceNotFoundResponse'
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                'components': {
                    'schemas': {
                        'Coordinate': {
                            'properties': {
                                'latitude': {
                                    'type': 'number',
                                    'title': 'Latitude',
                                    'description': 'Latitude in decimal degrees. Must be between -90 and 90.'
                                },
                                'longitude': {
                                    'type': 'number',
                                    'title': 'Longitude',
                                    'description': 'Longitude in decimal degrees. Must be between -180 and 180.'
                                }
                            },
                            'type': 'object',
                            'required': [
                                'latitude',
                                'longitude'
                            ],
                            'title': 'Coordinate',
                            'description': 'Represents a geographical coordinate with latitude and longitude.\n\nAttributes:\n- latitude (float): The latitude in decimal degrees, must be between -90 and 90.\n- longitude (float): The longitude in decimal degrees, must be between -180 and 180.',
                            'example': {
                                'latitude': 35.6582,
                                'longitude': 139.8752
                            }
                        },
                        'Device': {
                            'properties': {
                                'device_uuid': {
                                    'type': 'string',
                                    'title': 'Device Uuid',
                                    'description': 'The UUID of the device. It should start with the prefix (DEV), a single uppercase letter, and six digits (e.g., DEVX000001)'
                                },
                                'localisation': {
                                    'allOf': [
                                        {
                                            '$ref': '#/components/schemas/Coordinate'
                                        }
                                    ],
                                    'description': 'The geographical location of the device as latitude and longitude coordinates'
                                },
                                'deployment_date': {
                                    'type': 'string',
                                    'format': 'date',
                                    'title': 'Deployment Date',
                                    'description': 'The deployment date of the device in the format YYYY-MM-DD'
                                },
                                'owner': {
                                    'type': 'string',
                                    'format': 'email',
                                    'title': 'Owner',
                                    'description': 'The email address of the owner of the device'
                                }
                            },
                            'type': 'object',
                            'required': [
                                'device_uuid',
                                'owner'
                            ],
                            'title': 'Device',
                            'description': 'Represents a device with unique identifiers and location information.\n\nAttributes:\n- device_uuid (str): The UUID of the device. It should start with the prefix (DEV),\n  followed by a single uppercase letter and six digits (e.g., DEVX000001).\n- localisation (Coordinate): Geographical location of the device as coordinates.\n- deployment_date (date): The deployment date of the device in the format YYYY-MM-DD.\n- owner (EmailStr): The email address of the owner of the device.',
                            'example': {
                                'deployment_date': '2024-03-14',
                                'device_uuid': 'DEVX000001',
                                'localisation': {
                                    'latitude': 35.6582,
                                    'longitude': 139.8752
                                },
                                'owner': 'tanguy.pemeja@gmail.com'
                            }
                        },
                        'DeviceNotFoundResponse': {
                            'properties': {
                                'message': {
                                    'type': 'string',
                                    'title': 'Message',
                                    'default': 'Device not found'
                                }
                            },
                            'type': 'object',
                            'title': 'DeviceNotFoundResponse',
                            'description': 'Represents a response indicating that the device was not found.'
                        }
                    }
                }
            })
