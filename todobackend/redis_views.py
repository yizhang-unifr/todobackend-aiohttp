from logging import getLogger

from aiohttp.web import Response, View, json_response
from aiohttp_cors import CorsViewMixin

from .redis_models import TodoTask, TagTask

logger = getLogger(__name__)


class IndexView(View, CorsViewMixin):
    async def get(self):
        return json_response(await TodoTask.all_objects())

    async def post(self):
        content = await self.request.json()
        return json_response(
            await TodoTask.create_object(content, self.request.app.router['todo'].url_for)
        )

    async def delete(self):
        await TodoTask.delete_all_objects()
        res = await TodoTask.all_objects()
        return json_response(res)


class TodoView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def get(self):
        uuid = 'todos:'+self.uuid
        return json_response(await TodoTask.get_object(uuid))

    async def patch(self):
        content = await self.request.json()
        uuid = 'todos:' + self.uuid
        return json_response(
            await TodoTask.update_object(uuid, content))

    async def delete(self):
        uuid = 'todos:' + self.uuid
        TodoTask.delete_object(uuid)
        return Response()


class TagIndexView(View, CorsViewMixin):
    async def get(self):
        return json_response(await TagTask.all_objects())

    async def post(self):
        content = await self.request.json()
        return json_response(
            await TagTask.create_object(content, self.request.app.router['tag'].url_for)
        )

    async def delete(self):
        await TagTask.delete_all_objects()
        res = await TagTask.all_objects()
        return json_response(res)


class TagView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def get(self):
        uuid = 'tags:'+self.uuid
        return json_response(await TagTask.get_object(uuid))

    async def patch(self):
        content = await self.request.json()
        uuid = 'tags:' + self.uuid
        return json_response(
            await TagTask.update_object(uuid, content))

    async def delete(self):
        uuid = 'tags:' + self.uuid
        TagTask.delete_object(uuid)
        return Response()


class TodoTagsIndexView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def post(self):
        content = await self.request.json()
        uuid = 'todos:'+self.uuid
        if len(content) > 1:
            res = TodoTask.associate_more_tags(uuid, content)
        else:
            res = TodoTask.associate_one_tag(uuid, content)
        return json_response(await res)

    async def get(self):
        uuid = 'todos:' + self.uuid
        return json_response(await TodoTask.find_tags(uuid))

    async def patch(self):
        return self.post()

    async def delete(self):
        uuid = 'todos:' + self.uuid
        todoObj = await TodoTask.get_object(uuid)
        todoObj['tags'] = []
        await TodoTask.update_object(uuid, todoObj)
        return Response()


class TodoTagsView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.todos_uuid = request.match_info.get('uuid_todos')
        self.tags_uuid = request.match_info.get('uuid_tags')

    async def delete(self):
        todos_uuid = 'todos:'+self.todos_uuid
        tags_uuid = 'tags:'+self.tags_uuid
        await TodoTask.decouple_one_tag(todos_uuid, tags_uuid)

        return Response()


class TagsTodoIndexView(View, CorsViewMixin):
    def __init__(self, request):
        super().__init__(request)
        self.uuid = request.match_info.get('uuid')

    async def get(self):
        uuid = 'tags:'+self.uuid
        return json_response(await TagTask.find_associated_todos(uuid))
