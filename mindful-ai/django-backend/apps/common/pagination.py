
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardPagination(PageNumberPagination):
    
    page_size: int = 20
    page_size_query_param: str = 'page_size'
    max_page_size: int = 100
    page_query_param: str = 'page'

    def get_paginated_response(self, data: Any) -> Response:
        
        return Response({
            'success': True,
            'message': 'Success',
            'data': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
            },
        })

    def get_paginated_response_schema(self, schema: Any) -> Any:
        
        return {
            'type': 'object',
            'properties': {
                'success': {
                    'type': 'boolean',
                    'example': True,
                },
                'message': {
                    'type': 'string',
                    'example': 'Success',
                },
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'description': 'Total number of items across all pages.',
                            'example': 100,
                        },
                        'total_pages': {
                            'type': 'integer',
                            'description': 'Total number of pages.',
                            'example': 5,
                        },
                        'current_page': {
                            'type': 'integer',
                            'description': 'The current page number (1-indexed).',
                            'example': 1,
                        },
                        'next': {
                            'type': 'string',
                            'nullable': True,
                            'description': 'URL to the next page, or null if on the last page.',
                        },
                        'previous': {
                            'type': 'string',
                            'nullable': True,
                            'description': 'URL to the previous page, or null if on the first page.',
                        },
                        'results': schema,
                    },
                    'required': [
                        'count',
                        'total_pages',
                        'current_page',
                        'next',
                        'previous',
                        'results',
                    ],
                },
            },
            'required': ['success', 'message', 'data'],
        }
