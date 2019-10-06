from json import dumps
from logging import getLogger

from aiohttp.web import Response, View, json_response
from aiohttp_cors import CorsViewMixin

from .models import TodoTask, TagTask

logger = getLogger(__name__)


class IndexView(View, CorsViewMixin):
    async def get(self):
        return json_response(TodoTask.all_objects())

    async def post(self):
        content = await self.request.json()
        return json_response(
            TodoTask.create_object(content, self.request.app.router['todo'].url_for)
        )

    async def delete(self):
        TodoTask.delete_all_objects()
        return Response()


class TodoView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def get(self):
        return json_response(TodoTask.get_object(self.uuid))

    async def patch(self):
        content = await self.request.json()
        return json_response(
            TodoTask.update_object(self.uuid, content))

    async def delete(self):
        TodoTask.delete_object(self.uuid)
        return Response()


class TagIndexView(View, CorsViewMixin):
    async def get(self):
        return json_response(TagTask.all_objects())

    async def post(self):
        content = await self.request.json()
        return json_response(
            TagTask.create_object(content, self.request.app.router['tag'].url_for)
        )

    async def delete(self):
        TagTask.delete_all_objects()
        return Response()


class TagView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def get(self):
        return json_response(TagTask.get_object(self.uuid))

    async def patch(self):
        content = await self.request.json()
        return json_response(
            TagTask.update_object(self.uuid, content))

    async def delete(self):
        TagTask.delete_object(self.uuid)
        return Response()


class TodoTagsIndexView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def post(self):
        content = await self.request.json()
        if len(content) > 1:
            res = TodoTask.associate_more_tags(self.uuid, content)
        else:
            res = TodoTask.associate_one_tag(self.uuid, content)
        return json_response(res)

    async def get(self):
        return json_response(TodoTask.find_tags(self.uuid))

    async def patch(self):
        return self.post()

    async def delete(self):
        todoObj = TodoTask.get_object(self.uuid)
        todoObj['tags'] = []
        TodoTask.update_object(self.uuid, todoObj)
        return Response()


class TodoTagsView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.todos_uuid = request.match_info.get('uuid_todos')
        self.tags_uuid = request.match_info.get('uuid_tags')

    async def delete(self):
        TodoTask.decouple_one_tag(self.todos_uuid, self.tags_uuid)

        return Response()


class TagsTodoIndexView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def get(self):
        return json_response(TagTask.find_associated_todos(self.uuid))
