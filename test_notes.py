import os
from peewee import *  # pylint: disable=redefined-builtin,wildcard-import
import models as m
from crypto_utils import encrypt, key_to_store
import notes

DB_TEMP = SqliteDatabase(':memory:')

m.proxy.initialize(DB_TEMP)
DB_TEMP.connect()
DB_TEMP.create_tables([m.Note, m.Versions], safe=True)


def test_add_entry():
    title = "avi"
    content = "How are you doing today?"
    password = "masterpassword"
    sync = True
    notes.add_entry(content, title, password, sync)
    entry = m.Note.get(m.Note.title == title)
    print(entry)
    assert entry.content == content


def test_delete_entry():
    title = "yo"
    content = "Hello Lol"
    m.Note.create(content=content, tags=None, title=title)
    entry = m.Note.select().where(m.Note.title == title)  # pylint: disable=assignment-from-no-return
    if entry.exists():
        flag1 = 1
        entry = m.Note.get(m.Note.title == title)  # pylint: disable=assignment-from-no-return
    notes.delete_entry(entry)
    entry = m.Note.select().where(m.Note.title == title)  # pylint: disable=assignment-from-no-return
    flag2 = 1
    if entry.exists():
        flag2 = 0
    assert flag1 == flag2


def test_edit_entry():
    title = "lost in this world"
    content = "Batman is forever lost!!!"
    password = "masterpassword"
    password_to_store = key_to_store(password)
    # Need to encrypt before storing
    m.Note.create(content=content, tags=None, title=title, password=password_to_store)
    m.Versions.create(content=content, title='1_' + title)
    entry = m.Note.get(m.Note.title == title)
    new_title = "Superhero Found"
    new_content = "Robin to the rescue!!!"
    encryped_data = encrypt(new_content, password)
    notes.edit_entry(entry, new_title, new_content, password)
    entry = m.Note.select().where(m.Note.title == title) # pylint: disable=assignment-from-no-return
    flag = 1
    if entry.exists():
        flag = 0
    entry = m.Note.get(m.Note.title == new_title)
    assert (entry.title, entry.content, entry.password, flag) ==\
           (new_title, encryped_data, password_to_store, 1)


def test_menu_loop_q():
    notes.input = lambda t: 'q'
    notes.menu_loop()


def test_view_entries():
    notes.input = lambda t: 'q'
    notes.view_entries()


def test_main():
    exit_code_1 = os.system("python notes.py")
    exit_code_2 = os.system("python3 notes.py")
    assert exit_code_1 and exit_code_2
