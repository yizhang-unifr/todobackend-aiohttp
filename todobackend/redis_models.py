#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created on 15:19 2019-09-29, by Yi Zhang

' a ... module of todo-backend-python '

__author__ = 'Yi Zhang'

import aioredis
import json
from os import getenv
from uuid import uuid4


def withIn(a, list):
    res = False
    for item in list:
        if a == item:
            res = True
            break

    return res


class Task:
    _redis = None

    @classmethod
    async def get_connection_pool(cls, loop=None, recreate=False) -> aioredis.Redis:
        host = getenv('REDIS_HOST', '127.0.0.1')
        port = getenv('REDIS_PORT', 6379)
        db = getenv('REDIS_DB', 0)
        kwargs = {}
        kwargs['address'] = host, port
        kwargs['db'] = db
        if not cls._redis or recreate:
            cls._redis = await aioredis.create_pool(loop=loop, **kwargs)
        return cls._redis

    @classmethod
    async def close_connection(cls):
        print('Redis is closing...')
        cls._redis.close()
        await cls._redis.wait_closed()


class ObjTask:
    _task = Task()

    @classmethod
    async def create_object(cls, content, url_for=None, obj_str=None):

        Task._redis = await Task.get_connection_pool()

        uuid = str(uuid4())
        HOST = getenv('HOST', 'localhost:8000')
        obj = {
            'id': uuid,
            'completed': False,
            'url': 'http://{HOST}{}'.format(
                url_for(uuid=uuid).path, **locals())
        }
        obj.update(content)
        if obj_str is not None:
            obj_str = obj_str + ':'
        await cls.set_object(obj_str + uuid, obj)
        return obj

    @classmethod
    async def set_object(cls, uuid, obj):
        await Task._redis.execute('set', uuid, json.dumps(obj))

    @classmethod
    async def get_object(cls, uuid):
        data = await Task._redis.execute('get', uuid)
        return json.loads(data)

    @classmethod
    def delete_object(cls, uuid):
        Task._redis.execute('del', uuid)

    @classmethod
    async def update_object(cls, uuid, value):
        obj = await cls.get_object(uuid)
        obj.update(value)
        await cls.set_object(uuid, obj)
        return obj

    @classmethod
    async def all_objects(cls, pattern=None):
        keys = await Task._redis.execute('keys', pattern + '*')
        values = []
        for key in keys:
            values.append(await cls.get_object(key))
        return values

    @classmethod
    async def delete_all_objects(cls, pattern=None):
        if pattern is None:
            keys = await Task._redis.execute('keys', '*')
        else:
            keys = await Task._redis.execute('keys', pattern)
        for key in keys:
            await Task._redis.execute('del', key)


class TodoTask(ObjTask):

    @classmethod
    async def create_object(cls, content, url_for=None, obj_str='todos'):
        cls._redis = await Task.get_connection_pool()

        uuid = str(uuid4())
        HOST = getenv('HOST', 'localhost:8000')
        obj = {
            'id': uuid,
            'completed': False,
            'tags': [],
            'url': 'http://{HOST}{}'.format(
                url_for(uuid=uuid).path, **locals())
        }
        obj.update(content)
        todos_uuid = obj_str + ':' + uuid
        await cls.set_object(todos_uuid, obj)
        return obj

    @classmethod
    async def get_object(cls, uuid):
        data = await Task._redis.execute('get', uuid)
        return json.loads(data)

    @classmethod
    async def update_object(cls, uuid, value):
        obj = await cls.get_object(uuid)
        obj.update(value)
        await cls.set_object(uuid, obj)
        return obj

    @classmethod
    async def associate_one_tag(cls, uuid, content):
        obj = await cls.get_object(uuid)
        tagId = content['id']
        prefixed_tagId = 'tags:' + tagId
        tagObj = await TagTask.get_object(prefixed_tagId)
        tags_id_list =[x['id'] for x in obj['tags']]
        if not withIn(tagId, tags_id_list):
            obj['tags'].append({'id': tagObj['id'], 'title': tagObj['title']})
            print('not withIn!!!!')
        suffix_uuid = uuid.split(':')[1]
        tagObj['todos'].append({'id': suffix_uuid, 'title': obj['title']})
        await cls.update_object(uuid, obj)
        await TagTask.update_object(prefixed_tagId, tagObj)
        return await cls.get_object(uuid)

    @classmethod
    async def associate_more_tags(cls, uuid, content):
        obj = await cls.get_object(uuid)
        for item in content:
            tagId = item['id']
            prefixed_tagId = 'tags:' + tagId
            tagObj = await TagTask.get_object(prefixed_tagId)
            obj['tags'].append(tagObj)
            suffix_uuid = uuid.split(':')[1]
            tagObj['todos'].append({'id': suffix_uuid})
            await TagTask.update_object(prefixed_tagId, tagObj)
        await cls.update_object(uuid, obj)
        return obj

    @classmethod
    async def find_tags(cls, uuid):
        obj = await cls.get_object(uuid)
        return obj['tags']

    @classmethod
    async def decouple_one_tag(cls, todos_uuid, tag_uuid):
        suffix_tag_uuid = tag_uuid.split(':')[1]
        todosObj = await TodoTask.get_object(todos_uuid)
        tagObjList = [tag for tag in todosObj['tags'] if tag['id'] != suffix_tag_uuid]
        await cls.update_object(todos_uuid, {'tags': tagObjList})

    @classmethod
    def all_objects(cls, pattern=None):
        return super().all_objects(pattern='todos')

    @classmethod
    def delete_all_objects(cls, pattern=None):
        return super().delete_all_objects(pattern='todos*')


class TagTask(ObjTask):

    @classmethod
    async def create_object(cls, content, url_for=None, obj_str='tags'):
        cls._redis = await Task.get_connection_pool()

        uuid = str(uuid4())
        HOST = getenv('HOST', 'localhost:8000')
        obj = {
            'id': uuid,
            'todos': [],
            'url': 'http://{HOST}{}'.format(
                url_for(uuid=uuid).path, **locals())
        }
        obj.update(content)
        tag_uuid = obj_str + ':' + uuid
        await cls.set_object(tag_uuid, obj)

        # cls._redis.close()
        # await cls._redis.wait_closed()
        return obj

    @classmethod
    async def get_object(cls, uuid):
        # if uuid is bytes:
        #     uuid = uuid.decode()
        # tags_uuid = 'tags:'+ uuid
        data = await Task._redis.execute('get', uuid)
        return json.loads(data)

    @classmethod
    def all_objects(cls, pattern=None):
        return super().all_objects(pattern='tags')

    @classmethod
    async def associate_one_todo(cls, uuid, content):
        obj = await cls.get_object(uuid)
        obj['todos'].append(content)
        await cls.set_object(uuid, obj)
        return obj

    @classmethod
    async def find_associated_todos(cls, uuid):
        obj = await cls.get_object(uuid)
        res = []
        for todo in obj['todos']:

            res.append(await TodoTask.get_object('todos:'+todo['id']))
        return res

    @classmethod
    def delete_all_objects(cls, pattern=None):
        return super().delete_all_objects(pattern='tags*')
