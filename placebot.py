import telebot

from functions import *
from place import Place
from state import State


state = State()
bot = telebot.TeleBot(get_token())


def send_add_dilog(message):
    text = 'You can record more about this location or end the recording (confirm)'
    keyboard = get_keyboard([(elem,elem) for elem in state.buttons_add])
    bot.send_message(message.chat.id, text=text, reply_markup=keyboard)


# BOT HANDLERS..................................................................


# START
@bot.message_handler(commands=['start', 'help'])
def start(message):
    text_for_new_user = ("  Hi, I am PlaceBot and I can help you save place\n"
                        + "/add <address> - add a new place\n"
                        + "/list - display added places\n"
                        + "/reset - delete all place\n"
                        + "/dest <count> - show nearest places")
    state.set_place(message.chat.id)
    state.set_state(message.chat.id, state.START)
    bot.send_message(message.chat.id, text_for_new_user)


# STATUS
@bot.message_handler(commands=['status'])
def status(message):
    bot.send_message(message.chat.id, state.get_state(message.chat.id))


# /ADD
@bot.message_handler(commands=['add'])
def add(message):
    state.set_state(message.chat.id, state.ADD)
    address = message.text.replace('/add', '').strip()
    state.set_place(message.chat.id, {'address': address})
    send_add_dilog(message)


# BUTTONS ADD HANDLER
@bot.callback_query_handler(func=lambda query: state.in_stateadd(query.message.chat.id) and not state.in_save(query.data))
def add_buttons_handler(callback_query):
    message = callback_query.message
    state.set_state(message.chat.id, callback_query.data)
    text = f'Send {callback_query.data}'
    bot.send_message(message.chat.id, text=text)


# Save
@bot.callback_query_handler(func=lambda query: state.in_stateadd(query.message.chat.id) and state.in_save(query.data))
def confirm_button_handler(callback_query):
    message = callback_query.message
    state.set_state(message.chat.id, state.SAVE)
    place = state.places(message.chat.id)
    description = "\n\n" + place.description if place.description else ""
    place_text = f'address: {place.address}{description}\n'
    text = f'Do you want to save this place?: \n{place_text}'
    bot.send_message(message.chat.id,
                     text,
                     reply_markup=get_keyboard([(elem,elem) for elem in state.buttons_confirm]))


# YES ADD
@bot.callback_query_handler(func=lambda query: query.data == state.YES and state.check(query.message.chat.id, state.SAVE))
def add_yes(callback_query):
    try:
        message = callback_query.message
        # add excepltions handler
        state.save_place(message.chat.id)
        bot.send_message(message.chat.id, 'Bot have saved it')
    except ValueError as er:
        bot.send_message(message.chat.id, 'Place must contains address or location')
        send_add_dilog(message)


# NO ADD
@bot.callback_query_handler(func=lambda query: query.data == state.NO and state.check(query.message.chat.id, state.SAVE))
def add_no(callback_query):
    message = callback_query.message
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# ADDR
@bot.message_handler(func=lambda m: state.check(m.chat.id, state.ADDR))
def add_address(message):
    state.places(message.chat.id).address = message.text
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# LOCATION
@bot.message_handler(func=lambda m: state.check(m.chat.id, state.LOC), content_types=['location'])
def add_location(message):
    state.places(message.chat.id).location = message.location
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# DESCRIPTION
@bot.message_handler(func=lambda m: state.check(m.chat.id, state.DES))
def add_description(message):
    state.places(message.chat.id).description = message.text
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# PHOTO
@bot.message_handler(content_types=['photo'], func=lambda m: state.check(m.chat.id, state.PHOTO))
def add_photo(message):
    photopath = get_photopath(message.chat.id)
    state.places(message.chat.id).photopath = photopath
    write_file(photopath, photo_from_tg(message, bot))
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# LIST
@bot.message_handler(commands=['list'])
def list_places(message):
    state.set_state(message.chat.id, state.LIST)
    str_count = message.text.replace('/list', '').strip()
    if str_count.isdigit():
        count = int(str_count)
    else:
        count = 5
    place_list = state.base.list(message.chat.id, count)
    if place_list:
        sended_list = list()
        for index, place in enumerate(place_list):
            if place.address:
                des = place.address
            elif place.description:
                des = place.description
            else:
                des = ''
            sended_list.append(f'{index+1}: {des}')
        sended_str = '\n'.join(sended_list)
    else:
        sended_str = 'You haven`t save places yet'
    bot.send_message(message.chat.id, sended_str)
    state.set_state(message.chat.id, state.START)


# RESET
@bot.message_handler(commands=['reset'])
def reset(message):
    state.set_state(message.chat.id, state.RESET)
    text = 'Are you sure?'
    bot.send_message(message.chat.id, text, reply_markup=get_keyboard([(elem,elem) for elem in state.buttons_confirm]))


# YES RESET
@bot.callback_query_handler(func=lambda query: query.data == state.YES and state.check(query.message.chat.id, state.RESET))
def yes_reset(callback_query):
    message = callback_query.message
    state.set_state(message.chat.id, state.START)
    state.base.reset(message.chat.id)
    text = 'All data has been deleted'
    bot.send_message(message.chat.id, text)


# NO RESET
@bot.callback_query_handler(func=lambda query: query.data == state.NO and state.check(query.message.chat.id, state.RESET))
def no_reset(callback_query):
    message = callback_query.message
    state.set_state(message.chat.id, state.START)
    text = 'Ok good'
    bot.send_message(message.chat.id, text)


# DEST
@bot.message_handler(commands=['dest'])
def shortest_destination(message):
    state.set_state(message.chat.id, state.DEST)
    count = message.text.replace('/dest', '').strip()
    count = int(count) if count.isdigit() else 5
    state.set_count(message.chat.id, count)
    text = 'send your location'
    bot.send_message(message.chat.id, text)


# DEST HANDLER
@bot.message_handler(func=lambda mes: state.check(mes.chat.id, state.DEST), content_types=['location'])
def description_handel(message):
    location = message.location
    loc_values = state.shortest_places(message.chat.id, location, state.count(message.chat.id))
    if not loc_values:
        text = 'You haven`t save places yet'
        keyboard = []
    else:
        text = 'Choose a place'
        buttons = [(val[0], str(loc)) for loc, val in loc_values] + [(state.EXIT, state.EXIT)]
        keyboard = get_keyboard(buttons, 1)
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda q: state.check(q.message.chat.id, state.DEST) and q.data != state.EXIT)
def desc_button(query):
    message = query.message
    location = tuple(map(float, query.data.strip('()').split(',')))
    bot.send_location(query.message.chat.id, location[0], location[1])


@bot.callback_query_handler(func=lambda q: state.check(q.message.chat.id, state.DEST) and q.data == state.EXIT)
def desc_button(query):
    state.set_state(query.message.chat.id, state.START)
    bot.send_message(query.message.chat.id, 'ok')


def main():
    bot.polling()


if __name__ == '__main__':
    main()
