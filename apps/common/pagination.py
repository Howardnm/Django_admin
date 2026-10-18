from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """
    默认分页器。
    默认每页 20 条数据，最大每页 100 条数据。
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
