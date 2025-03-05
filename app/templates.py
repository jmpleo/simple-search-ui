from fastapi.templating import Jinja2Templates

from app.filters import (
    min_filter, max_filter, reduce_large_number_filter,
    tag_filter, execution_time_filter, reduce_ms_filter
)

templates = Jinja2Templates(directory="app/templates")
templates.env.filters['min'] = min_filter
templates.env.filters['max'] = max_filter
templates.env.filters['tag'] = tag_filter
templates.env.filters['reduce_large_number'] = reduce_large_number_filter
templates.env.filters['execution_time'] = execution_time_filter
templates.env.filters['reduce_ms'] = reduce_ms_filter
