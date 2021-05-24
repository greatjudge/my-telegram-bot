import telebot

from functions import *
from place import Place
from state import State


bot = telebot.TeleBot(get_token())
state = State()


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
    bot.answer_callback_query(c.id)


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
    bot.answer_callback_query(c.id)


# YES ADD
@bot.callback_query_handler(func=lambda query: query.data == state.YES and state.check(query.message.chat.id, state.SAVE))
def add_yes(callback_query):
    message = callback_query.message
    place = state.places(message.chat.id)
    try:
        # add excepltions handler
        state.save_place(message.chat.id)
        bot.send_message(message.chat.id, 'Bot have saved it')
        bot.answer_callback_query(c.id)
    except ValueError as er:
        bot.send_message(message.chat.id, 'Place must contains address or location')
        state.set_state(message.chat.id, state.ADD)
        send_add_dilog(message)
        bot.answer_callback_query(c.id)


# NO ADD
@bot.callback_query_handler(func=lambda query: query.data == state.NO and state.check(query.message.chat.id, state.SAVE))
def add_no(callback_query):
    message = callback_query.message
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# ADD ADDR
@bot.message_handler(func=lambda m: state.check(m.chat.id, state.ADDR), content_types=['text'])
def add_address(message):
    state.places(message.chat.id).address = message.text
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# ADD LOCATION
@bot.message_handler(func=lambda m: state.check(m.chat.id, state.LOC), content_types=['location'])
def add_location(message):
    state.places(message.chat.id).location = message.location
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# ADD DESCRIPTION
@bot.message_handler(func=lambda m: state.check(m.chat.id, state.DES), content_types=['text'])
def add_description(message):
    state.places(message.chat.id).description = message.text
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


# ADD PHOTO
@bot.message_handler(content_types=['photo'], func=lambda m: state.check(m.chat.id, state.PHOTO))
def add_photo(message):
    photopath = get_photopath(message.chat.id)
    state.places(message.chat.id).photopath = photopath
    write_file(photopath, photo_from_tg(message, bot))
    state.set_state(message.chat.id, state.ADD)
    send_add_dilog(message)


def places_buttons(state, uid):
    place_list = state.list_places(str(uid))
    place_num = [(place.address,str(num)) for num, place in enumerate(place_list)]
    place_num.append(('exit', state.EXIT))
    return place_num


def attr_buttons(state, place):
    buttons = [(key,key) for key in place.buttons]
    buttons.append(('<<', state.BACK))
    return buttons


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
        state.list_set_places(message.chat.id, place_list)
        bot.send_message(message.chat.id,
                         'places:',
                         reply_markup=get_keyboard(places_buttons(state,
                                                                  message.chat.id),
                                                   1))
    else:
        state.set_state(message.chat.id, state.START)
        sended_str = 'You haven`t save places yet'
        bot.send_message(message.chat.id, sended_str)


# LIST PLACE
@bot.callback_query_handler(func=lambda q: state.check(q.message.chat.id, state.LIST))
def list_place(call):
    bot.answer_callback_query(call.id)
    message = call.message
    if call.data == state.EXIT:
        state.set_state(message.chat.id, state.START)
        bot.send_message(message.chat.id, 'ok')
    elif call.data == state.BACK:
        bot.edit_message_reply_markup(chat_id=message.chat.id,
                                      message_id=message.id,
                                      reply_markup=get_keyboard(places_buttons(state,
                                                                               message.chat.id),
                                                                1))
    else:
        state.set_state(message.chat.id, state.LIST_PLACE)
        place = state.list_places(message.chat.id)[int(call.data)]
        state.set_place(message.chat.id, place)
        bot.edit_message_reply_markup(chat_id=message.chat.id,
                                      message_id=message.id,
                                      reply_markup=get_keyboard(attr_buttons(state,
                                                                             place)))
#FIX ALL

# LIST PLACE ATTR
@bot.callback_query_handler(func= lambda q: state.check(q.message.chat.id, state.LIST_PLACE))
def list_place_attr(call):
    bot.answer_callback_query(call.id)
    message = call.message
    place = state.places(message.chat.id)
    if call.data == state.BACK:
        state.set_state(message.chat.id, state.LIST)
        bot.edit_message_reply_markup(chat_id=message.chat.id,
                                      message_id=message.id,
                                      reply_markup=get_keyboard(places_buttons(state,
                                                                               message.chat.id),
                                                                1))
    else:
        if call.data == state.ADDR:
            bot.send_message(message.chat.id, place.address)
        elif call.data == state.DES:
            bot.send_message(message.chat.id, place.description)
        elif call.data == state.LOC:
            if place.location: bot.send_location(message.chat.id,
                                                 place.latitude,
                                                 place.longitude)
        elif call.data == state.PHOTO:
            if place.photopath:
                photo = get_photo(place.photopath)
                bot.send_photo(message.chat.id, photo)


# RESET
@bot.message_handler(commands=['reset'])
def reset(message):
    state.set_state(message.chat.id, state.RESET)
    text = 'Are you sure?'
    bot.send_message(message.chat.id, text, reply_markup=get_keyboard([(elem,elem) for elem in state.buttons_confirm]))


# YES RESET
@bot.callback_query_handler(func=lambda query: query.data == state.YES and state.check(query.message.chat.id, state.RESET))
def yes_reset(query):
    message = query.message
    state.set_state(message.chat.id, state.START)
    state.base.reset(message.chat.id)
    text = 'All data has been deleted'
    bot.send_message(message.chat.id, text)
    bot.answer_callback_query(query.id)


# NO RESET
@bot.callback_query_handler(func=lambda query: query.data == state.NO and state.check(query.message.chat.id, state.RESET))
def no_reset(query):
    message = query.message
    state.set_state(message.chat.id, state.START)
    text = 'Ok good'
    bot.send_message(message.chat.id, text)
    bot.answer_callback_query(query.id)



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
    bot.answer_callback_query(query.id)



@bot.callback_query_handler(func=lambda q: state.check(q.message.chat.id, state.DEST) and q.data == state.EXIT)
def desc_button(query):
    state.set_state(query.message.chat.id, state.START)
    bot.send_message(query.message.chat.id, 'ok')
    bot.answer_callback_query(query.id)


def main():
    bot.polling()


if __name__ == '__main__':
    main()
