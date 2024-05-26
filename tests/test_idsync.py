from typing import *
from objectbox import *
from objectbox.model import *
from objectbox.model.entity import _Entity
from objectbox.model.idsync import sync_model
from objectbox.c import CoreException
import json
from pprint import pprint
import os
import tests.model
import pytest

class _TestEnv:
    """
    Test setup/tear-down of model json files, db store and utils.
    Starts "fresh" on construction: deletes the model json file and the db files.
    """
    def __init__(self):
        self.model_path = 'test.json'
        if os.path.exists(self.model_path):
            os.remove(self.model_path)
        self.model = None
        self.db_path = 'testdb'
        Store.remove_db_files(self.db_path)

    def sync(self, model: Model) -> bool:
        self.model = model
        return sync_model(self.model, self.model_path)

    def json(self):
        return json.load(open(self.model_path))

    def store(self):
        assert self.model is not None
        return Store(model=self.model, directory=self.db_path)


def reset_ids(entity: _Entity):
    entity.iduid = IdUid(0, 0)
    entity.last_property_iduid = IdUid(0, 0)
    for prop in entity.properties:
        prop.iduid = IdUid(0, 0)
        if prop.index:
            prop.index.iduid = IdUid(0, 0)

@pytest.fixture
def env():
    return _TestEnv()

def test_empty(env):
    model = Model()
    env.sync(model)
    doc = env.json()
    assert doc['_note1']
    assert doc['_note2']
    assert doc['_note3']
    assert len(doc['entities']) == 0
    assert doc['lastEntityId'] == '0:0'
    assert doc['lastIndexId'] == '0:0' # NOTE: objectbox-generator outputs ""
    assert doc['modelVersionParserMinimum'] >= 5
    # debug: pprint(doc)
    #
    # TODO: sync with objectbox-generator empty fbs
    # assert doc['modelVersion'] == 5 
    # assert doc['lastIndex'] == ""
    # assert doc['lastRelationId'] == ""
    # assert len(doc['retiredEntityUids']) == 0
    # assert len(doc['retiredIndexUids']) == 0
    # assert len(doc['retiredPropertyUids']) == 0
    # assert len(doc['retiredRelationUids']) == 0
    # assert len(doc['version']) == 1


def test_json(env):
    @Entity()
    class MyEntity:
        id = Id()
        my_string = String()
        my_string_indexed = String(index=Index())

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    doc = env.json()
    # debug: pprint(doc)

    json_e0 = doc['entities'][0]
    e0_id = json_e0['id']
    assert e0_id == str(MyEntity.iduid)
    assert e0_id.startswith("1:")
    assert json_e0['name'] == "MyEntity"

    json_p0 = json_e0['properties'][0]
    p0_id = json_p0['id']
    assert p0_id == str(MyEntity.get_property('id').iduid)
    assert p0_id.startswith("1:")
    assert json_p0['name'] == "id"
    assert json_p0['flags'] == 1
    assert json_p0.get('indexId') is None

    json_p1 = json_e0['properties'][1]
    assert json_p1['id'] == str(MyEntity.get_property('my_string').iduid)
    assert json_p1['name'] == "my_string"
    assert json_p1.get('flags') is None
    assert json_p1.get('indexId') is None

    json_p2 = json_e0['properties'][2]
    assert json_p2['id'] == str(MyEntity.get_property('my_string_indexed').iduid)
    assert json_p2['name'] == "my_string_indexed"
    assert json_p2['flags'] == 8
    assert json_p2['indexId'] == str(MyEntity.get_property('my_string_indexed').index.iduid)
    assert json_e0['lastPropertyId'] == json_p2['id']

    assert doc['lastEntityId'] == e0_id
    assert doc['lastIndexId'] == json_p2['indexId']


def test_basics(env):
    @Entity()
    class MyEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    assert MyEntity.id == 1
    assert MyEntity.uid != 0
    entity_ids = str(MyEntity.iduid)

    # create new database and populate with two objects
    store = env.store()
    entityBox = store.box(MyEntity)
    entityBox.put(MyEntity(name="foo"),MyEntity(name="bar"))
    assert entityBox.count() == 2
    del entityBox
    store.close()
    del store

    # recreate model using existing model json and open existing database 
    model = Model()
    @Entity()
    class MyEntity:
        id = Id()
        name = String()
    model.entity(MyEntity)
    assert str(model.entities[0].iduid) == "0:0"
    env.sync(model)
    assert str(model.entities[0].iduid) == entity_ids

    # open existing database 
    store = env.store()
    entityBox = store.box(MyEntity)
    assert entityBox.count() == 2

def test_entity_add(env):
    @Entity()
    class MyEntity1:
        id = Id()
        name = String()
    model = Model()
    model.entity(MyEntity1)
    env.sync(model)
    e0_iduid = IdUid(MyEntity1.id, MyEntity1.uid)
    store = env.store()
    box = store.box(MyEntity1)
    box.put( MyEntity1(name="foo"), MyEntity1(name="bar"))
    assert box.count() == 2
    store.close()
    del store

    @Entity()
    class MyEntity2:
        id = Id()
        name = String()
        value = Int64()
    model = Model()
    reset_ids(MyEntity1)
    model.entity(MyEntity1)
    model.entity(MyEntity2)
    assert str(model.entities[0].iduid) == "0:0"
    env.sync(model)
    assert model.entities[0].iduid == e0_iduid
    store = env.store()
    box1 = store.box(MyEntity1)
    assert box1.count() == 2
    box2 = store.box(MyEntity2)
    box2.put( MyEntity2(name="foo"), MyEntity2(name="bar"))
    assert box2.count() == 2

def test_entity_remove(env):
    @Entity()
    class MyEntity1:
        id = Id()
        name = String()
    @Entity()
    class MyEntity2:
        id = Id()
        name = String()
        value = Int64()
    model = Model()
    model.entity(MyEntity1)
    model.entity(MyEntity2)
    env.sync(model)
    store = env.store()
    box1 = store.box(MyEntity1)
    box1.put( MyEntity1(name="foo"), MyEntity1(name="bar"))
    box2 = store.box(MyEntity2)
    box2.put( MyEntity2(name="foo"), MyEntity2(name="bar"))
    assert box1.count() == 2
    assert box2.count() == 2

    store.close()
    del store

    # Re-create a model without MyEntity2 

    model = Model()
    reset_ids(MyEntity1)
    model.entity(MyEntity1)
    env.sync(model)
    store = env.store()
    box1 = store.box(MyEntity1)
    assert box1.count() == 2

    # MyEntity2 is gone and should raise CoreException
    with pytest.raises(CoreException):
        box2 = store.box(MyEntity2)

def test_entity_rename(env):
    model = Model()
    @Entity()
    class MyEntity:
        id = Id()
        name = String()
    model.entity(MyEntity)
    env.sync(model)

    # Save uid of entity for renaming purposes..
    uid = MyEntity.uid # iduid.uid
    assert uid != 0
    # Debug: print("UID: "+ str(uid))

    store = env.store()
    box = store.box(MyEntity)
    box.put(MyEntity(name="foo"),MyEntity(name="bar"))
    assert box.count() == 2
    del box
    store.close()
    del store

    @Entity(uid=uid)
    class MyRenamedEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyRenamedEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyRenamedEntity)
    assert box.count() == 2


def test_prop_add(env):

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)
    box.put( MyEntity(name="foo"), MyEntity(name="bar"))
    del box
    store.close()
    del store

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        value = Property(int, type=PropertyType.int)

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)

    assert box.count() == 2

def test_prop_remove(env):

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        value = Property(int, type=PropertyType.int)

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)
    box.put( MyEntity(name="foo"), MyEntity(name="bar"))
    del box
    store.close()
    del store

    @Entity()
    class MyEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)
    assert box.count() == 2


def test_prop_rename(env):
    @Entity()
    class EntityA:
        id = Id()
        name = String()

    model = Model()
    model.entity(EntityA)
    env.sync(model)
    store = env.store()
    box = store.box(EntityA)
    box.put(EntityA(name="Luca"))
    assert box.count() == 1
    assert box.get(1).name == "Luca"
    assert not hasattr(box.get(1), "renamed_name")

    entity1_iduid = EntityA.iduid
    name = EntityA.get_property("name")
    name_iduid = name.iduid
    print(f"Entity.name ID/UID: {name.iduid}")

    del box  # Close store
    store.close()
    del store

    # *** Rename ***

    @Entity()
    class EntityA:
        id = Id()
        renamed_name = Property(str, uid=name.uid)  # Renamed property (same UID as "name")

    model = Model()
    model.entity(EntityA)
    env.sync(model)
    store = env.store()

    # Check ID/UID(s) are preserved after renaming
    entity2_iduid = EntityA.iduid
    renamed_name = EntityA.get_property("renamed_name")
    renamed_name_iduid = renamed_name.iduid
    print(f"Entity.renamed_name ID/UID: {renamed_name_iduid}")
    assert entity1_iduid == entity2_iduid
    assert name_iduid == renamed_name_iduid

    # Check property value is preserved after renaming
    box = store.box(EntityA)
    assert box.count() == 1
    assert not hasattr(box.get(1), "name")
    assert box.get(1).renamed_name == "Luca"


def test_model_json_updates(env):
    """ Tests situations where the model JSON should be written/should not be written. """

    def assert_model_json_written(value: bool, *entities: _Entity):
        model = Model()
        for entity in entities:
            model.entity(entity)
        assert env.sync(model) == value

    # Init
    @Entity()
    class EntityA:
        id = Id()
        name = String()
    assert_model_json_written(True, EntityA)

    # Add entity
    @Entity()
    class EntityB:
        id = Id()
        name = String()
    assert_model_json_written(True, EntityB)

    entityb_uid = EntityB.uid

    # Rename entity
    @Entity(uid=entityb_uid)
    class EntityC:
        id = Id()
        name = String()
    assert_model_json_written(True, EntityC)

    # Noop
    model = Model()
    model.entity(EntityC)
    assert not env.sync(model)

    # Add entity
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
    assert_model_json_written(True, EntityC, EntityD)

    # Noop
    assert_model_json_written(False, EntityC, EntityD)

    # Replace entity
    @Entity()
    class EntityE:
        id = Id()
    assert_model_json_written(True, EntityD, EntityE)

    # Noop
    assert_model_json_written(False, EntityD, EntityE)

    # Remove entity
    assert_model_json_written(True, EntityD)

    # Noop
    assert_model_json_written(False, EntityD)

    # Add property
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
        my_prop = String()
    assert_model_json_written(True, EntityD)

    my_prop_uid = EntityD.get_property("my_prop").uid

    # Rename property
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
        my_prop_renamed = String(uid=my_prop_uid)
    assert_model_json_written(True, EntityD)

    # Noop
    assert_model_json_written(False, EntityD)

    # Remove property
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
    assert_model_json_written(True, EntityD)
