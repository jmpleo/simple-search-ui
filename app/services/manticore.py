import json
import asyncio
import manticoresearch
from loguru import logger
from datetime import datetime
from manticoresearch.rest import ApiException
from typing import List, Optional, Dict, Any

from app.config import settings
from app.schemas.response import ResponseData


configuration = manticoresearch.Configuration(host=settings.manticore_url)


class ManticoreService:
    def __init__(self):
        self.manticore_api_client = manticoresearch.ApiClient(configuration)

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

        searchApi = manticoresearch.SearchApi(self.manticore_api_client)

        try:
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

            search_response = await asyncio.to_thread(
                searchApi.search,
                search_request
            )

            return ResponseData(
                data=search_response.to_dict()
            )

        except ApiException as e:
            error = json.loads(e.body)['error']

        except Exception as e:
            error = e

        return ResponseData(
            error=True,
            data=error
        )

    async def unload(self, t: str, q: str) -> ResponseData:

        searchApi = manticoresearch.SearchApi(self.manticore_api_client)
        try:
            search_query = manticoresearch.SearchQuery(query_string=q)

            search_request = manticoresearch.SearchRequest(
                table=t,
                index=t,
                query=search_query,
                limit=1,
                options={'max_matches': 1, 'ranker': 'none'}
            )

            search_response = await asyncio.to_thread(
                searchApi.search,
                search_request
            )

            total = search_response.to_dict()['hits']['total']

            if total > settings.limit_unloading:
                return ResponseData(
                    error=True,
                    data=(
                        f"Too many unloading: total: "
                        f"{total} > {settings.limit_unloading}"
                    )
                )

            search_request.limit = total
            search_request.options['max_matches'] = total

            search_response = await asyncio.to_thread(
                searchApi.search,
                search_request
            )

            return ResponseData(
                data=search_response.to_dict()
            )

        except ApiException as e:
            error = json.loads(e.body)['error']
        except Exception as e:
            error = str(e)

        return ResponseData(
            error=True,
            data=error
        )

    async def status(self) -> ResponseData:
        utilsApi = manticoresearch.UtilsApi(self.manticore_api_client)
        try:
            res = await asyncio.to_thread(
                utilsApi.sql,
                'show tables'
            )
            tables = {
                obj['Table']: {
                    'count': 0,
                    'fields': []
                }
                for obj in res.to_dict()[0].get('data', {})
                if obj['Table'] in settings.manticore_tables
            }

            for t in tables:
                res = await asyncio.to_thread(
                    utilsApi.sql,
                    f'select count(*) as c from {t}'
                )

                tables[t]['count'] = res.to_dict()[0]['data'][0]['c']

                if tables[t]['count'] < 0:

                    res = await asyncio.to_thread(
                        utilsApi.sql,
                        f'show table {t} status'
                    )

                    for o in res.to_dict()[0].get("data", []):
                        if o.get('Variable_name') == 'indexed_documents':
                            tables[t]['count'] = int(o.get('Value', 0))

                res = await asyncio.to_thread(utilsApi.sql, f'desc {t}')

                tables[t]['fields'] = {
                    obj['Field']: {
                        'type': obj['Type'],
                        'properties': obj['Properties'],
                    }
                    for obj in res.to_dict()[0].get('data', [])
                    if obj['Field'] != 'id'
                }

            return ResponseData(data=tables)

        except ApiException as e:
            error = json.loads(e.body)['error']

        except Exception as e:
            error = str(e)

        return ResponseData(
            error=True,
            data=error
        )

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
