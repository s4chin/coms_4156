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
from clint.textui import puts, colored
import models as m
from utils import clear_screen, get_paginated_entries
import crypto as Crypto
import upload_to_drive
import download_from_drive

PATH = os.getenv('HOME', os.path.expanduser('~')) + '/.notes'
DB = SqliteDatabase(PATH + '/diary.db')
m.proxy.initialize(DB)
FINISH_KEY = "ctrl+Z" if os.name == 'nt' else "ctrl+D"
crypto = Crypto.Crypto()                          #pylint disable=invalid-name
profile = None                                    #pylint disable=invalid-name


def reset_profile():
    """Reset the password"""
    global profile           #pylint disable=global-statement, invalid-name
    profile = None


def set_profile():
    """Use one password for all notes"""
    while True:
        password = getpass.getpass("Password for this session: ")
        if not password:
            print("Please input a valid password")
        else:
            break
    global profile        #pylint disable=global-statement, invalid-name
    profile = {
        'password': password
    }


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


def add_entry(data, title, password, tags=None, sync=False):
    m.Note.create(content=data, tags=tags, title=title, password=password, sync=sync)
    m.Versions.create(content=data, title='1_' + title)


def get_input():
    title = sys.stdin.read().strip()
    return title


def upload_drive(title, data):
    try:
        print("Syncing with Google Drive....\n")
        dir1 = os.getcwd()
        f = open(os.path.join(os.path.join(dir1, "sync"), title+".txt"), "w+")  # pylint: disable=invalid-name
        f.write(data)
        f.close()
        upload_to_drive.main()
        os.remove(os.path.join(os.path.join(dir1, "sync"), title+".txt"))
        puts(colored.green("Sync successful\n"))
        return True
    except:
        puts(colored.red("Oops!", sys.exc_info()[0], "occured.\n"))
        puts(colored.red("Sync Unsuccessful"))
        return False


#For Download Sync
def download_drive(entry, title, data, password):
    try:
        download_from_drive.main()
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
                    entry.content = crypto.encrypt(data_new, password)
                    entry.save()
        files = glob.glob(folder+"/*")
        for f in files:  # pylint: disable=invalid-name
            os.remove(f)
        return True
    except:
        puts(colored.red("Oops!", sys.exc_info()[0], "occured.\n"))
        return False


def process_tags(tag):
    tag_list = tag.split(',')
    new_tag_list = [tag.strip() for tag in tag_list if tag] + ['all']
    return ','.join(sorted(set(new_tag_list)))


def add_entry_ui():
    """Add a new note"""
    global profile            # pylint: disable=global statement, invalid-name, bad-option-value
    title_string = "Title (press {} when finished)".format(FINISH_KEY)
    puts(colored.yellow(title_string))
    puts(colored.blue("=" * len(title_string)))
    title = get_input()
    exist_entry = m.Note.select().where(m.Note.title == title)         #pylint: disable=assignment-from-no-return
    flag = exist_entry.exists()
    if not flag and title:                   #pylint: disable=too-many-nested-blocks
        entry_string = "\nEnter your entry: (press {} when finished)".format(FINISH_KEY)
        puts(colored.yellow(entry_string))
        data = get_input()
        if data:
            tag_string = "\nEnter comma separated tags(optional): (press {} when finished) : ".format(FINISH_KEY) # pylint disable=line-too-long
            puts(colored.yellow(tag_string))
            tags = get_input().strip()
            tags = process_tags(tags)
            if input("\nSave entry (y/n) : ").lower() != 'n':
                if not profile:
                    while True:
                        password = getpass.getpass("Password To protect data: ")
                        if not password:
                            print("Please input a valid password")
                        else:
                            break
                else:
                    password = profile['password']
                password_to_store = crypto.key_to_store(password)
                encryped_data = crypto.encrypt(data, password)
                text_to_print = "\nDo you want this file to be also synced"
                text_to_print += " with Google Drive? (y/n) : "
                if input(text_to_print).lower() != 'n':
                    add_entry(encryped_data, title, password_to_store, tags, True)
                    puts(colored.green("Saved successfully"))
                    upload_drive(title, data)
                else:
                    add_entry(encryped_data, title, password_to_store, tags, False)
                    puts(colored.green("Saved successfully"))
                print("Press Enter to return to main menu")
                input()

    elif flag:
        puts(colored.red("Note with this title already exists! Press Enter to return to main menu to view the note")) # pylint disable=line-too-long
        input()
        clear_screen()
        return
    else:
        puts(colored.red("No title entered! Press Enter to return to main menu"))
        input()
        clear_screen()
        return


def search_entries():
    """Search notes"""
    while 1:
        clear_screen()
        puts(colored.blue("What do you want to search for?"))
        puts(colored.cyan("c) Content"))
        puts(colored.cyan("t) Tags"))
        puts(colored.cyan("q) Return to the main menu"))
        print("Action [c/t/q] : ", end="")
        query_selector = input("").lower()
        if query_selector == "t":
            view_entries(input("Enter a search Query: "), search_content=False)
            break
        elif query_selector == "c":
            view_entries(input("Enter a search Query: "), search_content=True)
            break
        elif query_selector == "q":
            break
        else:
            print("Your input was not recognized, please try again!\n")
            input('')


def menu_loop():
    """To display the diary menu"""
    choice = None
    while choice != 'q':
        clear_screen()
        banner = r"""
         _   _       _            
        | \ | |     | |           
        |  \| | ___ | |_ ___  ___ 
        | . ` |/ _ \| __/ _ \/ __|
        | |\  | (_) | ||  __/\__ \
        \_| \_/\___/ \__\___||___/
        """
        puts(colored.green(banner))
        puts(colored.blue("Enter 'q' to quit"))
        for key, value in MENU.items():
            puts(colored.cyan('{}) {}'.format(key, value.__doc__)))
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
    entry.content = crypto.encrypt(data, password)
    entry.save()
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
    m.Versions.create(content=crypto.encrypt(data, password), title=title_to_save)
    return True


def edit_entry_view(entry, password):  # pylint: disable=inconsistent-return-statements
    clear_screen()
    title_string = "Title (press {} when finished)".format(FINISH_KEY)
    puts(colored.blue(title_string))
    puts(colored.yellow("=" * len(title_string)))
    readline.set_startup_hook(lambda: readline.insert_text(entry.title))
    try:
        title = sys.stdin.read().strip()
    finally:
        readline.set_startup_hook()
    if title:
        entry_string = "\nEnter your new entry: (press {} when finished)".format(FINISH_KEY)
        puts(colored.blue(entry_string))
        readline.set_startup_hook(lambda: readline.insert_text(entry.content))
        try:
            data = sys.stdin.read().strip()
        finally:
            readline.set_startup_hook()
        if data:
            if input("\nSave entry (y/n) : ").lower() != 'n':
                edit_entry(entry, title, data, password)
    else:
        puts(colored.red("No title entered! Press Enter to return to main menu"))
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
                content_1 = crypto.decrypt(versions[int(first)].content, password)
                content_2 = crypto.decrypt(versions[int(second)].content, password)
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
            print(crypto.decrypt(versions[int(next_action)].content, password))
            print('\nPress enter to return to view entries')
            input()
        else:
            print("Invalid Input")


def view_entry(entry, password):  # pylint: disable=inconsistent-return-statements
    title = entry.title
    data = crypto.decrypt(entry.content, password)
    if entry.sync:
        clear_screen()
        print("Checking for updates on note with Google Drive......")
        download_drive(entry, title, data, password)
        # entry = m.Note.get(m.Note.title == title)
        # data = decrypt(entry.content, password)

    clear_screen()
    puts(colored.yellow(title))
    puts(colored.blue("=" * len(title)))
    puts(colored.yellow(data))

    puts(colored.cyan('e) edit entry'))
    puts(colored.cyan('d) delete entry'))
    puts(colored.cyan('v) view previous versions'))
    puts(colored.cyan('q) to return to view entries'))

    next_action = input('Action: [e/d/v/q] : ').lower().strip()
    if next_action == 'd':
        return delete_entry(entry)
    if next_action == 'e':
        return edit_entry_view(entry, password)
    if next_action == 'v':
        return view_previous_versions(entry, password)
    if next_action == 'q':
        return False


def view_entries(search_query=None, search_content=None):
    """View all the notes"""
    global profile        # pylint: disable=global statement, invalid-name
    page_size = 2
    index = 0
    reset_flag = True

    while 1:
        clear_screen()
        if reset_flag:
            # Get entries if reset_flag is True
            # Will be True initially and on delete/edit entry
            entries = m.Note.select().order_by(m.Note.timestamp.desc())  # pylint: disable=assignment-from-no-return

            if search_query and search_content:
                entries = entries.where(m.Note.content.contains(search_query))
            elif search_query and not search_content:
                entries = entries.where(m.Note.tags.contains(search_query))

            entries = list(entries)
            if not entries:
                puts(colored.red("Your search had no results. Press enter to return to the main menu!")) #pylint disable=line-too-long
                input()
                clear_screen()
                return
            index = 0
            reset_flag = False
        paginated_entries = get_paginated_entries(entries, index, page_size)
        for i, entry in enumerate(paginated_entries):
            timestamp = entry.timestamp.strftime("%A %B %d, %Y %I:%M%p")
            head = "\"{title}\" on \"{timestamp}\" Tags: {tags}".format(
                title=entry.title, timestamp=timestamp, tags=entry.tags)
            puts(colored.blue(str(i) + ") " + head))
        puts(colored.cyan('n) next page'))
        puts(colored.cyan('p) previous page'))
        puts(colored.cyan('q) to return to main menu'))

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
                if not profile:
                    password = getpass.getpass('Password To Retrieve Content: ')
                elif crypto.key_to_store(profile['password']) != entry.password:       # pylint: disable=undefined-loop-variable
                    password = getpass.getpass('Password To Retrieve Content: ')
                else:
                    password = profile['password']
                entry = paginated_entries[int(next_action)]
                if crypto.key_to_store(password) != entry.password:
                    if input("Password is incorrect. Do you want to retry? (y/n): ").lower() != 'y':
                        break
                else:
                    reset_flag = view_entry(paginated_entries[int(next_action)], password)
                    break


MENU = OrderedDict([
    ('a', add_entry_ui),
    ('v', view_entries),
    ('s', search_entries),
    ('p', set_profile),
    ('r', reset_profile),
])

if __name__ == "__main__":
    init()
    try:
        menu_loop()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)
