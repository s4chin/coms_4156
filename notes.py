#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import traceback
from collections import OrderedDict
import readline
import getpass
import glob
from pathlib import Path
import hashlib
import difflib
from peewee import *  # pylint: disable=redefined-builtin,wildcard-import

import models as m
from utils import clear_screen, get_paginated_entries
from crypto_utils import *  # pylint: disable=wildcard-import
from gdriveDownload.download_from_drive import main as drive_download
from gdriveUpload.upload_to_drive import main as drive_upload

PATH = os.getenv('HOME', os.path.expanduser('~')) + '/.notes'
DB = SqliteDatabase(PATH + '/diary.db')
m.proxy.initialize(DB)
FINISH_KEY = "ctrl+Z" if os.name == 'nt' else "ctrl+D"


def init():
    """
    Initialize and create database
    :return: void
    """
    if not os.path.exists(PATH):
        os.makedirs(PATH)
    try:
        DB.connect()
        DB.create_tables([m.Note, m.Versions], safe=True)
    except DatabaseError as err:
        traceback.print_tb(err.__traceback__)
        exit(0)


def add_entry(data, title, password, sync):
    m.Note.create(content=data, tags=None, title=title, password=password, sync=sync)
    m.Versions.create(content=data, title='1_' + title)


def get_input():
    title = sys.stdin.read().strip()
    return title

#For Upload Sync
def upload_drive(title, data):
    try:
        print("Syncing with Google Drive....\n")
        dir1 = os.getcwd()
        f = open(os.path.join(os.path.join(dir1, "sync"), title+".txt"), "w+")  # pylint: disable=invalid-name
        f.write(data)
        f.close()
        drive_upload()
        os.remove(os.path.join(os.path.join(dir1, "sync"), title+".txt"))
        print("Sync successful\n")
    except:
        print("Oops!", sys.exc_info()[0], "occured.\n")
        print("Sync Unsuccessful")

#For Download Sync
def download_drive(entry, title, data, password):
    try:
        drive_download()
    except:
        print("Oops!", sys.exc_info()[0], "occured.\n")
        print("Press Enter to return")
        input()
        return
    dir1 = os.getcwd()
    folder = os.path.join(dir1, "sync")
    path = os.path.join(folder, title+".txt")
    myfile = Path(path)
    if myfile.is_file():
        h_1 = hashlib.md5(open(myfile, 'rb').read()).hexdigest()
        data = data.encode('utf-8')
        h_2 = hashlib.md5(data).hexdigest()
        text_to_print = "\nThe data of the note doesn't match with the sync on Google Drive"
        text_to_print += " do you want to update local copy? (y/n) : "
        if h_1 != h_2:
            print(text_to_print)
            if input(text_to_print).lower() != 'n':
                with open(myfile, 'r') as ufile:
                    data_new = ufile.read()
                entry.content = encrypt(data_new, password)
                entry.save()
    files = glob.glob(folder+"/*")
    for f in files:  # pylint: disable=invalid-name
        os.remove(f)


def add_entry_ui():
    """Add a new note"""
    title_string = "Title (press {} when finished)".format(FINISH_KEY)
    print(title_string)
    print("=" * len(title_string))
    title = get_input()
    if title:
        entry_string = "\nEnter your entry: (press {} when finished)".format(FINISH_KEY)
        print(entry_string)
        data = get_input()
        if data:
            if input("\nSave entry (y/n) : ").lower() != 'n':
                while True:
                    password = getpass.getpass("Password To protect data: ")
                    if not password:
                        print("Please input a valid password")
                    else:
                        break
                password_to_store = key_to_store(password)
                encryped_data = encrypt(data, password)
                text_to_print = "\nDo you want this file to be also synced"
                text_to_print += " with Google Drive? (y/n) : "
                if input(text_to_print).lower() != 'n':
                    add_entry(encryped_data, title, password_to_store, True)
                    print("Saved successfully")
                    upload_drive(title, data)
                else:
                    add_entry(encryped_data, title, password_to_store, False)
                    print("Saved successfully")
                print("Press Enter to return to main menu")
                input()
                clear_screen()

    else:
        print("No title entered! Press Enter to return to main menu")
        input()
        clear_screen()
        return


def menu_loop():
    """To display the diary menu"""
    choice = None
    while choice != 'q':
        clear_screen()
        print(PATH)
        banner = r"""
         _   _       _            
        | \ | |     | |           
        |  \| | ___ | |_ ___  ___ 
        | . ` |/ _ \| __/ _ \/ __|
        | |\  | (_) | ||  __/\__ \
        \_| \_/\___/ \__\___||___/
        """
        print(banner)
        print("Enter 'q' to quit")
        for key, value in MENU.items():
            print('{}) {} : '.format(key, value.__doc__))
        choice = input('Action : ').lower().strip()

        if choice in MENU:
            clear_screen()
            MENU[choice]()
    clear_screen()


def delete_entry(entry):
    versions = list(m.Versions.select().where(m.Versions.title.contains(entry.title)))
    for version in versions:
        version.delete_instance()
    return entry.delete_instance()


def edit_entry(entry, title, data, password):
    previous_title = entry.title
    entry.title = title
    entry.content = encrypt(data, password)
    entry.save()
    print("\nSaved successfully")
    if entry.sync:
        upload_drive(title, data)
    versions = list(m.Versions.select().where(m.Versions.title.contains(previous_title)) \
                    .order_by(m.Versions.timestamp.desc()))
    if previous_title != title:
        for version in versions:
            prev_version_title_number = version.title.split('_')[0]
            version.title = prev_version_title_number + '_' + title
            version.save()
    if len(versions) == 10:
        entry_to_delete = versions[-1]
        entry_to_delete.delete_instance()
        versions.pop()
    previous_version_number = int(versions[0].title.split('_')[0])
    title_to_save = str(previous_version_number + 1) + '_' + title
    m.Versions.create(content=encrypt(data, password), title=title_to_save)
    return True


def edit_entry_view(entry, password):  # pylint: disable=inconsistent-return-statements
    clear_screen()
    title_string = "Title (press {} when finished)".format(FINISH_KEY)
    print(title_string)
    print("=" * len(title_string))
    readline.set_startup_hook(lambda: readline.insert_text(entry.title))
    try:
        title = sys.stdin.read().strip()
    finally:
        readline.set_startup_hook()
    if title:
        entry_string = "\nEnter your entry: (press {} when finished)".format(FINISH_KEY)
        print(entry_string)
        readline.set_startup_hook(lambda: readline.insert_text(entry.content))
        try:
            data = sys.stdin.read().strip()
        finally:
            readline.set_startup_hook()
        if data:
            if input("\nSave entry (y/n) : ").lower() != 'n':
                edit_entry(entry, title, data, password)
            print("Press Enter to return to main menu")
            input()
            clear_screen()
    else:
        print("No title entered! Press Enter to return to main menu")
        input()
        clear_screen()
        return False


def view_previous_versions(entry, password):
    flag = True
    while True:
        clear_screen()
        if flag:
            versions = m.Versions.select().where(m.Versions.title.contains(entry.title)) \
                            .order_by(m.Versions.timestamp.desc())
            versions = list(versions)
        flag = False
        for i, version_entry in enumerate(versions):
            timestamp = version_entry.timestamp.strftime("%A %B %d, %Y %I:%M%p")
            head = "\"{title}\" on \"{timestamp}\"".format(
                title=version_entry.title, timestamp=timestamp)
            print(str(i) + ") " + head)
        print('d) diffCheck')
        print('q) quit to return')
        next_action = input('Action:[n/d/q] : ').lower().strip()
        if next_action == 'q':  # pylint: disable=no-else-return
            return False
        elif next_action == 'd':
            first = input('\nInput first Version: ')
            second = input('Input Second Version: ')
            if first.isdigit() and second.isdigit() \
                    and 0 <= int(first) <= i and 0 <= int(second) <= i and int(first) != int(second):  # pylint: disable=undefined-loop-variable,line-too-long
                content_1 = decrypt(versions[int(first)].content, password)
                content_2 = decrypt(versions[int(second)].content, password)
                content_1_lines = content_1.splitlines()
                content_2_lines = content_2.splitlines()
                my_d = difflib.Differ()
                diff = my_d.compare(content_1_lines, content_2_lines)
                print('\n'.join(diff))
                print('\nPress enter to return to view versions')
                input()
            else:
                print("Invalid Input. Press Enter to continue.")
                input()
        elif next_action.isdigit() and 0 <= int(next_action) <= i:  # pylint: disable=undefined-loop-variable
            clear_screen()
            print(versions[int(next_action)].title)
            print("=" * len(versions[int(next_action)].title))
            print(decrypt(versions[int(next_action)].content, password))
            print('\nPress enter to return to view entries')
            input()
        else:
            print("Invalid Input")


def view_entry(entry, password):  # pylint: disable=inconsistent-return-statements
    title = entry.title
    data = decrypt(entry.content, password)
    if entry.sync:
        clear_screen()
        print("Checking for updates on note with Google Drive......")
        download_drive(entry, title, data, password)
        # entry = m.Note.get(m.Note.title == title)
        # data = decrypt(entry.content, password)

    clear_screen()
    print(title)
    print("=" * len(title))
    print(data)

    print('e) edit entry')
    print('d) delete entry')
    print('v) view previous versions')
    print('q) to return to view entries')

    next_action = input('Action: [e/d/v/q] : ').lower().strip()
    if next_action == 'd':
        return delete_entry(entry)
    if next_action == 'e':
        return edit_entry_view(entry, password)
    if next_action == 'v':
        return view_previous_versions(entry, password)
    if next_action == 'q':
        return False


def view_entries():
    """View all the notes"""
    page_size = 2
    index = 0
    reset_flag = True

    while 1:
        clear_screen()
        if reset_flag:
            # Get entries if reset_flag is True
            # Will be True initially and on delete/edit entry
            entries = m.Note.select().order_by(m.Note.timestamp.desc())  # pylint: disable=assignment-from-no-return
            entries = list(entries)
            if not entries:
                print("Your search had no results. Press enter to return to the main menu!")
                input()
                clear_screen()
                return
            index = 0
            reset_flag = False
        paginated_entries = get_paginated_entries(entries, index, page_size)
        for i, entry in enumerate(paginated_entries):
            timestamp = entry.timestamp.strftime("%A %B %d, %Y %I:%M%p")
            head = "\"{title}\" on \"{timestamp}\"".format(
                title=entry.title, timestamp=timestamp)
            print(str(i) + ") " + head)
        print('n) next page')
        print('p) previous page')
        print('q) to return to main menu')

        next_action = input('Action: [n/p/q] : ').lower().strip()
        if next_action == 'q':
            break
        elif next_action == 'n':
            if index + page_size < len(entries):
                index += page_size
        elif next_action == 'p':
            if index - page_size >= 0:
                index -= page_size
        elif next_action.isdigit() and 0 <= int(next_action) < len(paginated_entries):
            while 1:
                password = getpass.getpass('Password To Retrieve Content: ')
                entry = paginated_entries[int(next_action)]
                if key_to_store(password) != entry.password:
                    if input("Password is incorrect. Do you want to retry? (y/n): ").lower() != 'y':
                        break
                else:
                    reset_flag = view_entry(paginated_entries[int(next_action)], password)
                    break


MENU = OrderedDict([
    ('a', add_entry_ui),
    ('v', view_entries),
])

if __name__ == "__main__":
    init()
    try:
        menu_loop()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)
