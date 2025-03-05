from app.schemas.api import (
    ApiMethodDescription,
    ApiV1MethodDescription,
)
from typing import List


METHOD_DESCRIPTION: List[ApiMethodDescription] = [
    ApiV1MethodDescription(
        name='search',
        description="поиск",
        http_method="GET",
        path='/search?q=&t=&p=&mm=&l=',
        parameters=[
            {'name': 'q', 'description': 'строка запроса'},
            {'name': 't', 'description': 'таблица'},
            {'name': 'p', 'description': 'порция'},
            {'name': 'mm', 'description': 'срез'},
            {'name': 'l', 'description': 'размер порции'}
        ],
        responses=[
            {
              'error': False,
              'data': {
                'took': "<int: время выполнения в мс>",
                'timed_out': False,
                'hits': {
                  'total': "<int: общее число найденных по запросу>",
                  'total_relation': "eq",
                  'hits': [
                    {
                      '_id': "<int: идентификатор записи>",
                      '_score': "<int: ранг строки в общем рейтинге>",
                      '_source': {
                        '<str: наименование поля>': "<str|int|bool: данные поля>",
                      }
                    },
                  ]
                }
              }
            },
            {
                'error': True,
                'data': "Описание ошибки"
            }
        ]
    ),
    ApiV1MethodDescription(
        name='unloading_start',
        description="запуск задачи на выгрузку в фоновом режиме",
        http_method="GET",
        path='/unloading/start?t=&q=',
        parameters=[
            {'name': 'q', 'description': 'строка запроса'},
            {'name': 't', 'description': 'таблица'}
        ],
        responses=[
            {
                "error": False,
                "data": {
                    "task_id": "<str: hash/id задачи>",
                    "status": "<str: статус задачи>"
                },
            },
            {
                'error': True,
                'data': "Описание ошибки"
            }
        ]
    ),
    ApiV1MethodDescription(
        name='unloading_start_pack',
        description="пакетный запрос на выгрузку в фоновом режиме",
        http_method="POST",
        path='/unloading/start?t=',
        parameters=[
            {'name': 't', 'description': 'таблица'},
            {'name': 'file', 'description': 'файл формата .txt в теле запроса'}
        ],
        responses=[
            {
                "error": False,
                "data": {
                    "tasks": [
                        {
                            "error": False,
                            "data": {
                                "task_id": "<str: идентификатор задачи для 1 строки>",
                                "status": "started"
                            }
                        },
                        {
                            "error": False,
                            "data": {
                                "task_id": "<str: идентификатор задачи для 2 строки>",
                                "status": "started"
                            }
                        },
                        {
                            "error": True,
                            "data": "<str: описание ошибки связанной с 3 строкой>"
                        },
                    ]
                }
            },
            {
                'error': True,
                'data': "Описание ошибки"
            },
        ]
    ),
    ApiV1MethodDescription(
        name='unloading_status',
        description="Проверка статуса задачи",
        http_method="GET",
        path='/unloading/status/{task_id}',
        parameters=[
            {'name': 'task_id', 'description': 'идентификатор задачи'}
        ],
        responses=[
            {
                "error": False,
                "data": {
                    "start_time": "<str: iso формат начала>",
                    "timestamp": "<str: iso формат временной метки запроса статуса>",
                    "result": {
                        "error": False,
                        "data": {
                            "total_pure": "<int: количество выгруженных>",
                            "total": "<str: представление total_pure с суффиксом>"
                        }
                    }
                }
            },
            {
                "error": False,
                "data": {
                    "start_time": "<str: iso формат начала>",
                    "timestamp": "<str: iso формат временной метки запроса статуса>",
                    "result": {
                        'error': True,
                        'data': "Описание ошибки"
                    }
                }
            },
            {
                "error": False,
                "data": {
                    "start_time": "<str: iso формат начала>",
                    "timestamp": "<str: iso формат временной метки запроса статуса>",
                    "result": "<null: задача все еще выполняется>"
                }
            },
            {
                'error': True,
                'data': "Описание ошибки"
            }
        ]
    ),
    ApiV1MethodDescription(
        name='unloading_data',
        description="Выгрузка готовых задач",
        http_method="GET",
        path='/unloading/data/{task_id}.{ext}',
        parameters=[
            {'name': 'task_id', 'description': 'идентификатор задачи'},
            {'name': 'ext',
             'description': 'формат выгружаемого файла (json|csv)'}
        ],
        responses=[
            {"error": False, "data": "<raw file: выгружаемый файл>"},
            {
                'error': True,
                'data': "Описание ошибки"
            }
        ]
    )
]
