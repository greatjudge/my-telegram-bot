from dotenv import load_dotenv
from telebot import types
from time import time
import os
import shutil


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


def write_file(photopath, bstr_file):
    with open(photopath, 'wb') as file:
        file.write(bstr_file)
    return photopath


def create_filename(user_id, extension):
    return f'image-{user_id}-{int(time())}.{extension}'


def get_photopath(user_id):
    extension = 'jpg' # FIX png ...
    # FIX relocate in init proj
    if not os.path.isdir('photos/'):
        os.mkdir('photos')
    if not os.path.isdir(f'/photos/{user_id}'):
        os.mkdir(f'photos/{user_id}')
    photopath = f'photos/{user_id}/{create_filename(user_id, extension)}'
    return photopath


def get_photo(photopath):
    if os.path.exists(photopath):
        with open(photopath, 'br') as file:
            return file.read()


def delete_photo(photopath):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), photopath)
    os.remove(path)


def delete_photos(id):
    dirphotopath = f'photos/{id}'
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), dirphotopath)
    if os.path.isdir(dirphotopath):
        shutil.rmtree(path)
