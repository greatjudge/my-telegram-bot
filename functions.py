from dotenv import load_dotenv
from telebot import types
from time import time
import os
import shutil
import boto3


dirname = 'photos'


def get_token():
    """ get telebot token from environment """
    env_path = '.env'
    load_dotenv(env_path)
    return os.environ.get('TOKEN')


def get_keyboard(names_button_list_tuple, row_width=3):
    keyboard = types.InlineKeyboardMarkup(row_width=row_width)
    buttons = [types.InlineKeyboardButton(text=text, callback_data=value)
                for text, value in names_button_list_tuple]
    keyboard.add(*buttons)
    return keyboard


def photo_from_tg(message, bot):
    fileid = message.photo[-1].file_id
    fileinf = bot.get_file(fileid)
    bstr_file = bot.download_file(fileinf.file_path)
    return bstr_file


def make_dir(dirname):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)


def delete_all_photos():
    if os.path.isdir(dirname):
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), dirname)
        if os.path.isdir(path):
            shutil.rmtree(path)


def add_photo(uid, photopath, photo):
    make_dir(dirname)
    path = os.path.join(dirname, str(uid))
    make_dir(path)
    write_file(photopath, photo)


def write_file(photopath, bstr_file):
    with open(photopath, 'wb') as file:
        file.write(bstr_file)


def read_photo(photopath):
    with open(photopath, 'rb') as file:
        return file.read()


def filename(user_id, extension):
    return f'image-{user_id}-{int(time())}.{extension}'


def get_photo(photopath):
    if os.path.exists(photopath):
        with open(photopath, 'br') as file:
            return file.read()


def delete_photo(photopath):
    if os.path.exists(photopath):
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), photopath)
        os.remove(path)


def delete_photos(uid):
    uid = str(uid)
    dirphotopath = f'photos/{uid}'
    if os.path.exists(dirphotopath):
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), dirphotopath)
        if os.path.isdir(dirphotopath):
            shutil.rmtree(path)


def get_photopath(user_id):
    user_id = str(user_id)
    extension = 'jpg' # FIX png ...
    make_dir(dirname)
    path = os.path.join(dirname, user_id)
    make_dir(path)
    photopath = os.path.join(path, filename(user_id, extension))
    return photopath
