# Demo file of tests
import os
import unittest
import mock
from peewee import *  # pylint: disable=redefined-builtin,wildcard-import
from notes import * #pylint: disable=wildcard-import
import models as m
import notes   # pylint: disable=ungrouped-imports
import crypto as Crypto


DB_TEMP = SqliteDatabase(':memory:')
m.proxy.initialize(DB_TEMP)
DB_TEMP.connect()
DB_TEMP.create_tables([m.Note, m.Versions], safe=True)


def test_add_entry():
    title = "avi"
    content = "How are you doing today?"
    password = "masterpassword"
    sync = True
    add_entry(content, title, password, sync)
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
    delete_entry(entry)
    entry = m.Note.select().where(m.Note.title == title)  # pylint: disable=assignment-from-no-return
    flag2 = 1
    if entry.exists():
        flag2 = 0
    assert flag1 == flag2


def test_edit_entry():
    crypto = Crypto.Crypto()     #pylint disable=redefined-outer-name
    title = "lost in this world"
    content = "Batman is forever lost!!!"
    password = "masterpassword"
    password_to_store = crypto.key_to_store(password)
    # Need to encrypt before storing
    m.Note.create(content=content, tags=None, title=title, password=password_to_store)
    m.Versions.create(content=content, title='1_' + title)
    entry = m.Note.get(m.Note.title == title)
    new_title = "Superhero Found"
    new_content = "Robin to the rescue!!!"
    encryped_data = crypto.encrypt(new_content, password)
    edit_entry(entry, new_title, new_content, password)
    entry = m.Note.select().where(m.Note.title == title) # pylint: disable=assignment-from-no-return
    flag = 1
    if entry.exists():
        flag = 0
    entry = m.Note.get(m.Note.title == new_title)
    assert (entry.title, entry.content, entry.password, flag) ==\
           (new_title, encryped_data, password_to_store, 1)


def simple_valid():
    return True


def invalid_error():
    raise Exception("Error")


class Testnotes(unittest.TestCase):
    @mock.patch('upload_to_drive.main', side_effect=simple_valid)
    def test_upload_drive_valid(self, upload_drive_function):
        title = "avi"
        content = "How are you doing today?"
        password = "masterpassword"
        sync = True
        add_entry(content, title, password, sync)
        entry = m.Note.get(m.Note.title == title)
        p_1 = upload_drive(entry.title, entry.content)
        assert p_1


    @mock.patch('upload_to_drive.main', side_effect=invalid_error)
    def test_upload_drive_invalid(self, upload_drive_function):
        title = "avi"
        content = "How are you doing today?"
        password = "masterpassword"
        sync = True
        add_entry(content, title, password, sync)
        entry = m.Note.get(m.Note.title == title)
        p_1 = upload_drive(entry.title, entry.content)
        assert not p_1


    @mock.patch('download_from_drive.main', side_effect=simple_valid)
    def test_download_drive_valid(self, upload_drive_function):
        title = "avi"
        content = "How are you doing today?"
        password = "masterpassword"
        sync = True
        add_entry(content, title, password, sync)
        entry = m.Note.get(m.Note.title == title)
        dir1 = os.getcwd()
        f = open(os.path.join(os.path.join(dir1, "sync"), title+".txt"), "w+")  # pylint: disable=invalid-name
        f.write(content)
        f.close()
        p_1 = download_drive(entry, entry.title, entry.content, password)
        assert p_1


    @mock.patch('download_from_drive.main', side_effect=invalid_error)
    def test_download_drive_invalid(self, upload_drive_function):
        title = "avi"
        content = "How are you doing today?"
        password = "masterpassword"
        sync = True
        add_entry(content, title, password, sync)
        entry = m.Note.get(m.Note.title == title)
        dir1 = os.getcwd()
        f = open(os.path.join(os.path.join(dir1, "sync"), title+".txt"), "w+")  # pylint: disable=invalid-name
        f.write(content)
        f.close()
        p_1 = download_drive(entry, entry.title, entry.content, password)
        assert not p_1


def test_search_entries_valid():
    tag_list = ['t']
    title = "avi"
    content = "How are you doing today?"
    password = "masterpassword"
    sync = True
    m.Note.create(content=content, tags=tag_list, title=title, password=password, sync=sync)
    mock_input = ['t', 't', 'q']
    notes.input = lambda t: mock_input.pop(0)
    val = search_entries()
    assert val == 1


def test_search_entries_quit():
    notes.input = lambda t: 'q'
    val = search_entries()
    assert val == 2


def test_menu_loop_q():
    notes.input = lambda t: 'q'     #pylint: disable=redefined-builtin
    notes.menu_loop()


def test_view_entries():
    notes.input = lambda t: 'q'
    notes.view_entries()


def test_main():
    exit_code_1 = os.system("python notes.py")
    exit_code_2 = os.system("python3 notes.py")
    assert exit_code_1 and exit_code_2
