from os import getenv
from uuid import uuid4


class Task:

    db = {}

    @classmethod
    def create_object(cls, content, url_for):
        uuid = str(uuid4())
        HOST = getenv('HOST', 'localhost:8000')
        obj = {
            'id': uuid,
            'completed': False,
            'url': 'http://{HOST}{}'.format(
                url_for(uuid=uuid).path, **locals())
        }
        obj.update(content)
        cls.set_object(uuid, obj)
        return obj

    @classmethod
    def all_objects(cls):
        return list(cls.db.values())

    @classmethod
    def delete_all_objects(cls):
        cls.db = {}

    @classmethod
    def get_object(cls, uuid):
        return cls.db[uuid]

    @classmethod
    def delete_object(cls, uuid):
        del cls.db[uuid]

    @classmethod
    def set_object(cls, uuid, value):
        cls.db[uuid] = value

    @classmethod
    def update_object(cls, uuid, value):
        obj = cls.db[uuid]
        obj.update(value)
        return obj

class TodoTask(Task):
    
    @classmethod
    def create_object(cls, content, url_for):
        uuid = str(uuid4())
        HOST = getenv('HOST', 'localhost:8000')
        obj = {
            'id': uuid,
            'completed': False,
            'tags':[],
            'url': 'http://{HOST}{}'.format(
                url_for(uuid=uuid).path, **locals())
        }
        obj.update(content)
        cls.set_object(uuid, obj)
        return obj

    @classmethod
    def update_object(cls, uuid, value):
        obj = super().update_object(uuid,value)
        if obj['tags'] is not None:
            for tag in obj['tags']:
                TagTask.associate_one_todo(tag['id'], {'id':uuid})
        return obj

    @classmethod
    def associate_one_tag(cls,uuid,content):
        obj = cls.get_object(uuid)
        tagId = content['id']
        tagObj = TagTask.get_object(tagId)
        obj['tags'].append(tagObj)
        tagObj['todos'].append({'id':uuid})  # add todos into tag
        TagTask.update_object(tagId,tagObj)
        cls.set_object(uuid,obj)
        return obj
    
    @classmethod
    def associate_more_tags(cls,uuid,content):
        obj = cls.get_object(uuid)
        for item in content:
            tagId = item['id']
            tagObj = TagTask.get_object(tagId)
            obj['tags'].append(tagObj)
            tagObj['todos'].append({'id': uuid})
            TagTask.update_object(tagId, tagObj)
        cls.set_object(uuid,obj)
        return obj

    @classmethod
    def find_tags(cls,uuid):
        obj = cls.get_object(uuid)
        return obj['tags']

    @classmethod
    def decouple_one_tag(cls,todos_uuid,tag_uuid):
        todosObj = TodoTask.get_object(todos_uuid)
        tagObjList = [tag for tag in todosObj['tags'] if tag['id'] != tag_uuid]
        cls.update_object(todos_uuid,{'tags':tagObjList})

class TagTask(Task):
    
    @classmethod
    def create_object(cls, content, url_for):
        uuid = str(uuid4())
        HOST = getenv('HOST', 'localhost:8000')
        obj = {
            'id': uuid,
            'todos': [],
            'url': 'http://{HOST}{}'.format(
                url_for(uuid=uuid).path, **locals())
        }
        obj.update(content)
        cls.set_object(uuid, obj)
        return obj

    @classmethod
    def associate_one_todo(cls,uuid,content):
        obj = cls.get_object(uuid)
        obj['todos'].append(content)
        cls.set_object(uuid, obj)
        return obj

    @classmethod
    def associate_more_todos(cls,uuid,content):
        obj = cls.get_object(uuid)
        for item in content:
            obj['todos'].append(item)
        cls.set_object(uuid, obj)
        return obj

    @classmethod
    def find_associated_todos(cls,uuid):
        obj = cls.get_object(uuid)
        res = []
        for todo in obj['todos']:
            res.append(TodoTask.get_object(todo['id']))
        return res




    

