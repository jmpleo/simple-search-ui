import json
import asyncio
import manticoresearch
from functools import wraps
from loguru import logger
from datetime import datetime
from manticoresearch.rest import ApiException
from manticoresearch.exceptions import ServiceException

from typing import List, Optional, Dict, Any

from app.config import settings
from app.schemas.response import ResponseData


configuration = manticoresearch.Configuration(host=settings.manticore_url)


def retry_attempts(max_attempts: int = 3, sleep: int = 0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = max_attempts
            while attempts > 0:
                attempts -= 1
                res = await func(*args, **kwargs)
                if not res.error:
                    return res

                if sleep:
                    await asyncio.sleep(sleep)

            return res
        return wrapper
    return decorator


def maybe_syntax_error(error: str):
    if 'syntax error' in error.lower() or 'query error' in error:
        return (
            "ошибка в составлении запроса, нажимай на '?', "
            "чтобы посмотреть на синтаксис. "
            f"подробнее: {error}"
        )

    return error


class ManticoreService:
    def __init__(self):
        self.manticore_api_client = manticoresearch.ApiClient(configuration)
        self.utilsApi = manticoresearch.UtilsApi(self.manticore_api_client)
        self.searchApi = manticoresearch.SearchApi(self.manticore_api_client)

    @retry_attempts(max_attempts=5, sleep=1)
    async def search(
        self,
        t: str,
        q: str,
        p: int = 0,
        highlight_fields: Optional[List[str]] = None,
        limit: int = settings.limit_records_on_page,
        max_matches: int = settings.manticore_max_matches,
        ranker: str = 'none'
    ) -> ResponseData:

        max_matches = min(max(max_matches, 1), settings.manticore_max_matches)
        limit = min(max(limit, 1), settings.limit_records_on_page, max_matches)

        query_highlight = None

        if highlight_fields:
            query_highlight = manticoresearch.Highlight()
            query_highlight.fields = {f: {} for f in highlight_fields}
            query_highlight.before_match = settings.highlight_start
            query_highlight.after_match = settings.highlight_end

        search_query = manticoresearch.SearchQuery(query_string=q)
        search_request = manticoresearch.SearchRequest(
            table=t,
            index=t,
            query=search_query,
            highlight=query_highlight,
            limit=limit,
            offset=p * limit,
            options={'max_matches': max_matches, 'ranker': ranker}
        )

        try:
            return ResponseData(
                data=(
                    await asyncio.to_thread(
                        self.searchApi.search,
                        search_request
                    )
                ).to_dict()
            )

        except ApiException as e:
            error = json.loads(e.body)['error']
            error = maybe_syntax_error(str(error))

        except Exception as e:
            logger.error(str(e))
            error = 'ошибка на стороне разраба - need bug report'

        return ResponseData(
            error=True,
            data=str(error)
        )

    @retry_attempts(max_attempts=5, sleep=1)
    async def unload(self, t: str, q: str) -> ResponseData:

        search_query = manticoresearch.SearchQuery(query_string=q)

        search_request = manticoresearch.SearchRequest(
            table=t,
            index=t,
            query=search_query,
            limit=1,
            options={'max_matches': 1, 'ranker': 'none'}
        )

        try:

            search_response = await asyncio.to_thread(
                self.searchApi.search,
                search_request
            )

            total = search_response.to_dict()['hits']['total']

            if total > settings.limit_unloading:
                return ResponseData(
                    error=True,
                    data=(
                        "слишком большая выборка"
                        f" (всего: {total}, max: {settings.limit_unloading}),"
                        " уточните запрос"
                    )
                )

            if total > 0:

                search_request.limit = total
                search_request.options['max_matches'] = total

                search_response = await asyncio.to_thread(
                    self.searchApi.search,
                    search_request
                )

            return ResponseData(
                data=search_response.to_dict()
            )

        except ApiException as e:
            error = json.loads(e.body)['error']
            error = maybe_syntax_error(str(error))

        except Exception as e:
            logger.error(str(e))
            error = 'ошибка на стороне разраба - need bug report'

        return ResponseData(
            error=True,
            data=str(error)
        )

    # в дальнейшем нужно оптимизация,
    # потому что это очень грузит загрузку страницы
    @retry_attempts(max_attempts=5, sleep=0)
    async def status(self) -> ResponseData:
        try:
            tables = await self._tables()

            for table_name in tables:
                tables[table_name]['count'] = await self.table_size(
                    table_name=table_name,
                    table_type=tables[table_name]['type']
                )
                tables[table_name]['fields'] = await self.table_fields(
                    table_name=table_name,
                    table_type=tables[table_name]['type']
                )

            return ResponseData(data=tables)

        except ApiException as e:
            error = json.loads(e.body)['error']
            error = maybe_syntax_error(str(error))

        except Exception as e:
            logger.error(str(e))
            error = 'ошибка на стороне разраба - need bug report'

        return ResponseData(error=True, data=error)

    async def table_fields(
        self, *, table_name: str,
        status: dict = None,
        table_type: str = None
    ) -> dict:
        if not table_type:
            if not status:
                status = await self._table_status(table_name)
            table_type = status['table_type']

        match table_type:
            case 'rt' | 'local':
                return await self._local_table_fields(table_name)
            case 'distributed':
                return await self._distributed_table_fields(table_name)

        return {}

    async def table_size(
        self, *, table_name: str,
        status: dict = None,
        table_type: str = None
    ) -> int:
        if not table_type:
            if not status:
                status = await self._table_status(table_name)
            table_type = status['table_type']

        match table_type:
            case 'rt' | 'local':
                return await self._local_table_size(
                    table_name=table_name,
                    status=status
                )
            case 'distributed':
                return await self._distributed_table_size(
                    table_name
                )

        return 0

    async def _tables(self) -> dict:
        res = await asyncio.to_thread(self.utilsApi.sql, 'show tables')
        return {
            obj['Table']: {
                'count': 0,
                'fields': {},
                'type': obj['Type'],
            }
            for obj in res.to_dict()[0]['data']
            if obj['Table'] in settings.manticore_tables
        }

    async def _table_status(self, table_name: str) -> dict:
        try:
            status_res = await asyncio.to_thread(
                self.utilsApi.sql,
                f'show table {table_name} status'
            )

            return dict(map(
                lambda o: (o['Variable_name'], o['Value']),
                status_res.to_dict()[0]['data']
            ))

        except ServiceException as e:
            logger.warning(
                f"таблица {table_name} недоступна"
                + str(json.loads(e.body)['error'])
            )

        return {}

    async def _local_table_size(
        self, *, table_name: str = None, status: dict = None
    ) -> int:
        if not status and table_name:
            status = await self._table_status(table_name)

        if status:
            match status['table_type']:
                case 'rt' | 'local':
                    return int(status['indexed_documents'])

        return 0

    async def _distributed_table_size(self, table_name: str) -> int:
        distrib_desc_res = await asyncio.to_thread(
            self.utilsApi.sql,
            f'desc {table_name}'
        )
        count = 0
        for o in distrib_desc_res.to_dict()[0]["data"]:
            count += await self._local_table_size(table_name=o['Agent'])

        return count

    async def _local_table_fields(self, table_name: str) -> dict:
        desc_res = await asyncio.to_thread(
            self.utilsApi.sql,
            f'desc {table_name}'
        )

        return {
            o["Field"]: {
                'type': o["Type"],
                'properties': o["Properties"]
            }
            for o in desc_res.to_dict()[0]["data"]
            if o["Field"] != 'id'
        }

    async def _distributed_table_fields(
        self, table_name: str
    ) -> dict:
        desc_res = await asyncio.to_thread(
            self.utilsApi.sql,
            f'desc {table_name}'
        )

        tables_fields = {}

        for o in desc_res.to_dict()[0]["data"]:
            if o['Type'] == 'local':
                fields = await self._local_table_fields(o['Agent'])
                tables_fields[o['Agent']] = fields

        common_fields = set.intersection(*(
            set(fields)
            for _, fields in tables_fields.items()
        ))

        fields = {}

        for field_name in common_fields:
            types = set(
                fields[field_name]['type']
                for _, fields in tables_fields.items()
            )
            properties = set(
                fields[field_name]['properties']
                for _, fields in tables_fields.items()
            )
            if len(types) == 1 and len(properties) == 1:
                fields[field_name] = {
                    'type': next(iter(types)),
                    'properties': next(iter(properties)),
                }

        return fields

    @staticmethod
    async def simple_format(
        search_returned: Dict[str, Any],
        table: Optional[Dict[str, Any]] = None
    ) -> ResponseData:
        simple_data = {}

        if (
            'hits' not in search_returned
            or 'total' not in search_returned['hits']
            or 'hits' not in search_returned['hits']
            or 'took' not in search_returned
        ):
            error = (
                f'search returned manticore format unknown: '
                f'{search_returned.keys()}'
            )
            logger.error(error)
            return ResponseData(
                error=True,
                data=error
            )

        if table and ('fields' not in table):
            error = f'table returned manticore format unknown: {str(table)}'
            logger.error(error)
            return ResponseData(
                error=True,
                data=error
            )

        simple_data['total'] = search_returned['hits']['total']
        simple_data['took'] = search_returned['took']
        simple_data['data'] = []

        for obj in search_returned['hits']['hits']:

            if '_source' not in obj:
                error = (
                    f"search returned manticore format unknown: table: {obj}"
                )
                logger.error(error)
                return ResponseData(
                    error=True,
                    data=error
                )

            row = []
            source = obj['_source']
            highlights = obj.get('highlight', {})

            for f, val in source.items():
                if table:
                    field_type = table['fields'].get(f, {}).get('type', 'text')

                    if field_type in ['text', 'string']:
                        if f in highlights and highlights[f]:
                            val = highlights[f][0]

                    elif field_type == 'timestamp':
                        val = datetime.fromtimestamp(val).isoformat(' ')

                row.append(val)

            simple_data['data'].append(row)

        return ResponseData(
            data=simple_data
        )
