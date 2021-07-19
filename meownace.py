import sqlite3
from functools import wraps
import datetime, pytz, requests
from json import loads

import logging
import random
from telegram import ChatAction, ParseMode, ForceReply
from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.ext import MessageFilter
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from telegram.error import NetworkError, Unauthorized
from telegram.replykeyboardremove import ReplyKeyboardRemove

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def send_typing_action(func):
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


""" Starting bot """


@send_typing_action
def start(update, context):
    """Send a message when the command /start is issued."""

    text = '(oﾟvﾟ)ノ Welcome to Meownace, ' + str(
        update.message.from_user.first_name) + '!' + '\nUse /help for the list of commands.\n'

    context.bot.send_animation(chat_id=update.message.chat_id,
                               animation="https://drive.google.com/uc?id=1PJ4yPTXLp8QiCS7RWOiEJZnDLCC95Up8",
                               caption=text)

    # Connect to the SQL db.
    conn = sqlite3.connect('dbs/users.db')
    c = conn.cursor()

    chat_id = str(update.message.chat_id)

    username = update.message.from_user.username
    if username is None:
        username = update.message.from_user.first_name

    # Check existence of user in database.
    if c.execute("SELECT 1 FROM USERS WHERE CHATID='" + chat_id + "'").fetchone():
        print(username + " has already been added to user database")
    else:
        print("Adding user " + username + " to user database")
        c.execute("INSERT INTO USERS VALUES('" + chat_id + "','" + username + "'," + "75)")

    conn.commit()
    conn.close()


""" List of commands """


@send_typing_action
def help(update, context):
    """Send a message when the command /help is issued."""
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Meownace is here to help! ヾ(•ω•`)o\n'
                                  'Use the commands shown below to interact with me:\n\n'
                                  '⚙ BOT ⚙\n'
                                  '/start - view the start screen\n'
                                  '/about - about the developers\n\n'
                                  ' 📅 TODO 📅\n'
                                  '/add <name of task> - add a task \n'
                                  '/clear <name of task> or <index> - remove a finished task \n'
                                  '/clearall - remove all finished tasks \n'
                                  '/delete <name of task> or <index> - remove a task \n'
                                  '/deleteall - remove all tasks\n'
                                  '/list - show all your tasks \n\n'
                                  '🏫 STUDY 🏫\n'
                                  '/set - set a timer\n'
                                  '/unset - remove an existing timer \n'
                                  '/timer - choose your desired timer settings\n\n'
                                  ' 🧸 PET FUNCTIONS 🧸\n'
                                  '/health - how am i feeling right now? \n'
                                  '/feed - gimme food \n'
                                  '/pat - gimme head pats \n'
                                  '/walk - take me on a walk \n'
                                  '/inspirational - get inspired \n'
                                  '/catfact - learn more about my species \n'
                                  '/pic - get cute cat pics [WIP]\n')


""" About us """


@send_typing_action
def about(update, context):
    message = "Created by Team Meownace for NUS Orbital 2021 ( •̀ ω •́ )✧"

    context.bot.send_animation(chat_id=update.message.chat_id,
                               animation="https://drive.google.com/uc?id=1KphsQjQZz_rhgSb61K0rDmwpdmKvhc_J",
                               caption=message)


""" To-do functionality """


@send_typing_action
def addtask(update, context):
    input = update.message.text.lower().split()
    chat_id = str(update.message.chat_id)

    username = update.message.from_user.username
    if username is None:
        username = update.message.from_user.first_name

    if len(input) >= 2:
        input.remove('/add')

        if all([x.isnumeric() for x in input]):
            update.message.reply_text("The name of your task cannot consist of numbers only!")
            return

        task = " ".join(input)

        # Connect to the SQL db.
        conn = sqlite3.connect('dbs/todolist.db')
        c = conn.cursor()

        if c.execute("SELECT 1 FROM todolist WHERE chatid='" + chat_id + "' AND task = '" + task + "'").fetchone():
            message = "You already added this item into your to-do list!"
        else:
            c.execute("INSERT INTO TODOLIST VALUES('" + chat_id + "','" + task + "','" + username + "')")

            message = "Added to to-do list."

        conn.commit()
        conn.close()

        update.message.reply_text(message, disable_notification=True)
        show_list(update, context)
    else:
        update.message.reply_text("Format: /add <name of task>")


def get_arr_of_tasks(chat_id):
    conn = sqlite3.connect('dbs/todolist.db')
    c = conn.cursor()

    c.execute("SELECT task FROM todolist WHERE chatid='" + chat_id + "'")

    rows = [i[0] for i in c.fetchall()]
    conn.close()
    return rows


@send_typing_action
def cleartask(update, context):
    strings = update.message.text.lower().split()
    chat_id = str(update.message.chat_id)

    if len(strings) >= 2:
        strings.remove('/clear')
    else:
        update.message.reply_text("Format: /clear <name of task> or /clear <index of task>")
        return

    # user inputs /clear <int>
    if len(strings) == 1 and strings[0].isnumeric():
        # get the name of the task from rows and delete it from the todolist db

        rows = get_arr_of_tasks(chat_id)
        try:
            taskName = rows[int(strings[0]) - 1]
        except IndexError:
            update.message.reply_text("❗ Index is not in your to-do list.")
            return

    else:  # input is /clear <name of task>
        taskName = ' '.join(strings)

    conn = sqlite3.connect('dbs/todolist.db')
    c = conn.cursor()
    rc = c.execute("DELETE FROM todolist WHERE chatid='" + chat_id + "' AND task='" + taskName + "'").rowcount
    conn.commit()
    conn.close()

    if rc <= 0:
        update.message.reply_text("❌ Task was not found in your to-do list: " + taskName)
    else:
        update_health(chat_id, 10)
        update.message.reply_text("✔Task successfully cleared from your list: " + taskName + "\n+HP")

        show_list(update, context)


@send_typing_action
def clearall(update, context):
    conn = sqlite3.connect('dbs/todolist.db')
    c = conn.cursor()
    chat_id = str(update.message.chat_id)

    rc = c.execute("DELETE FROM todolist WHERE chatid='" + chat_id + "'").rowcount

    if rc != 0:
        conn.commit()
        update_health(chat_id, rc * 10)
        update.message.reply_text("To-do list has been cleared of all tasks. Meownace is proud of you!")
    else:
        update.message.reply_text("Your to-do list is empty!")
    conn.close()


@send_typing_action
def deletetask(update, context):
    strings = update.message.text.lower().split()
    chat_id = str(update.message.chat_id)

    if len(strings) >= 2:
        strings.remove('/delete')
    else:
        update.message.reply_text("Format: /delete <name of task> or /delete <index of task>")
        return

    # user inputs /delete <int>
    if len(strings) == 1 and strings[0].isnumeric():
        # get the name of the task from the rows and delete it from the todolist db

        rows = get_arr_of_tasks(chat_id)
        try:
            taskName = rows[int(strings[0]) - 1]
        except IndexError:
            update.message.reply_text("❌ Index is not in your to-do list.")
            return

    else:  # input is /delete <name of task>
        taskName = ' '.join(strings)

    conn = sqlite3.connect('dbs/todolist.db')
    c = conn.cursor()
    rc = c.execute("DELETE FROM todolist WHERE chatid='" + chat_id + "' AND task='" + taskName + "'").rowcount
    conn.commit()
    conn.close()

    if rc <= 0:
        update.message.reply_text("❌ Task was not found in your to-do list: " + taskName)
    else:
        update.message.reply_text("✔Task successfully deleted from your list: " + taskName)
        show_list(update, context)


@send_typing_action
def deleteall(update, context):
    conn = sqlite3.connect('dbs/todolist.db')
    c = conn.cursor()
    chat_id = str(update.message.chat_id)

    rc = c.execute("DELETE FROM todolist WHERE chatid='" + chat_id + "'").rowcount

    if rc != 0:
        update.message.reply_text("All tasks have been deleted.")

    else:
        update.message.reply_text("Your to-do list is empty.")

    conn.commit()
    conn.close()


def show_list(update, context):
    chat_id = str(update.message.chat_id)

    rows = get_arr_of_tasks(chat_id)

    if len(rows) != 0:
        items = ""
        for count, task in enumerate(rows, 1):
            items += "{0}. {1}\n".format(str(count), task)
        update.message.reply_text("📄 " + update.message.from_user.first_name + "'s tasks:\n" + items)
    else:
        update.message.reply_text("Your to-do list is empty! (´･ω･`)")


""" Pet interaction """


@send_typing_action
def pat(update, context):
    update_health(str(update.message.chat_id), 1)
    context.bot.send_animation(chat_id=update.message.chat_id,
                               animation="https://drive.google.com/uc?id=11WbSar89heMax-ppRtT8VkQ_e-zvnryz",
                               caption="You gave meownace a pat on the head! +HP")
    # update.message.reply_text()


@send_typing_action
def walk(update, context):
    update_health(str(update.message.chat_id), 1)
    context.bot.send_animation(chat_id=update.message.chat_id,
                               animation="https://drive.google.com/uc?id=1J3Di8WM5VhPQ-aVa48Lxeweci_qZL8x0",
                               caption="You took meownace on a walk! +HP")


def feed(update, context):
    chat_id = str(update.message.chat_id)

    update_health(str(update.message.chat_id), 1)
    stickers = {"Meownace steals your pancakes! +HP"
                : 'CAACAgUAAxkBAAIGH2Diesw7Pxzl4QABUDjvQsVce9mqOAACxQIAAnD6EFcshnCaDQ15cSAE',
                "You are what you eat?? +HP"
                : 'CAACAgUAAxkBAAIGIGDiewbyD63n7UL6hmOZQqY7ULIhAAKLAgACY3BIVrN-6y3Hce4eIAQ',
                "You hand Meownace cup noodles! +HP"
                : 'CAACAgUAAxkBAAIGIWDiezFutBJyu9bZLJY1LsqrRcLnAAKyBQACwP8RV_qdy9vdg_b1IAQ',
                "Purrfect pudding! +HP"
                : 'CAACAgUAAxkBAAIKomDtoU9nA3XHxaXa7nFGJoZ2C4hXAAKbAgACWppAV4rN0C_IFzsEIAQ',
                "Delicious dango! +HP"
                : 'CAACAgUAAxkBAAIKo2Dtoct2Oil7KTFEglS32euzPH69AAKzAwAC0tJAV7NyW4z0rXnpIAQ',
                "Mouth-watering macarons! +HP"
                : 'CAACAgUAAxkBAAIK02D1AzJ9iT6nyLENke0FfNfssR0LAAL4AgACssiAVzGe74Z0hgITIAQ'
    }

    text, sticker_url = random.choice(list(stickers.items()))

    context.bot.send_sticker(chat_id=chat_id, sticker=sticker_url, disable_notification=True)

    update.message.reply_text(text)


""" Pet's health """


def get_hp_sticker(hp):
    """ RANGES:
    0 Very upset
    1 - 29 Disappointed
    30 - 59 Sad
    60 - 89 Neutral
    90 - 119 Pleased
    120 - 149 Joyous
    150 Ecstatic
    """

    very_upset = ['CAACAgUAAxkBAAIDGGDIoZZSasZYD4_yGP8ZRxLEove7AAJ-AgACl2dAVmhgDWxdCb2CHwQ',
                  'CAACAgUAAxkBAAIGD2DieDNLQjNqKhHtociB4EVpsEWKAAJuAwACgCoQV-ROFcSaCxD9IAQ',
                  'CAACAgUAAxkBAAIGEGDieGMvgs-8Hnq7iMdNSMKy_2QtAALiAwACn7oRV_UcNch5tNKhIAQ']
    disappointed = ['CAACAgUAAxkBAAIIAmDlXNXdOYIzM6dVkFbLJguFcLlvAAKxAgACWp0pV3mOuTdcqCX9IAQ']
    sad = ['CAACAgUAAxkBAAIDAWDIoGjY0F3mLKqbNEPscAaAvq29AAIfBAACEwNJVpUZ2LvHB95yHwQ']
    neutral = ['CAACAgUAAxkBAAIDAAFgyKAPsMHCgcLTz_kKGr9hiD1GEwACQQQAAsagQFZvDPyy_eIjox8E',
               'CAACAgUAAxkBAAIIE2DlY9kWmoa4pet70SzL8brgFvUQAAKnAgACoXcpVzCFwQjfFP6bIAQ']
    pleased = ['CAACAgUAAxkBAAIC7mDInlmoxvXO3UsXy6PLzpyngPXQAALpAgACZk5JVq9UssuYYljOHwQ']
    joyous = ['CAACAgUAAxkBAAIIAWDlXLktls_J9Z2mk38EMz2zgOilAAIRAwAC9p8xV2FvIH-UrVdVIAQ']
    ecstatic = ['CAACAgUAAxkBAAIIcmDlZ2yVVMAVzN2Rlxhn4seroWR3AAJMAgACxRExVyn-qYg11FplIAQ',
                'CAACAgUAAxkBAAIIFGDlY_XfzjPs_L2BMPWJnYyx8RS3AAIJAwAC3PAxVzjLZzYahql5IAQ',
                'CAACAgUAAxkBAAIIFWDlZAG9gUvwb5cJcCcAAbSMkDrLgQAC-QIAAiwZKFeN8WKu-P1klSAE']

    if hp == 0:
        return random.choice(very_upset), "Very upset"
    elif hp in range(1, 30):
        return random.choice(disappointed), "Disappointed"
    elif hp in range(30, 60):
        return random.choice(sad), "Sad"
    elif hp in range(60, 90):
        return random.choice(neutral), "Neutral"
    elif hp in range(90, 120):
        return random.choice(pleased), "Pleased"
    elif hp in range(120, 150):
        return random.choice(joyous), "Joyous"
    elif hp == 150:
        return random.choice(ecstatic), "Ecstatic"
    else:
        print("Error in get_hp_sticker")
        return


@send_typing_action
def health(update, context):
    """ report current health of pet """
    conn = sqlite3.connect('dbs/users.db')
    c = conn.cursor()

    chat_id = update.message.chat_id
    chat_id = str(chat_id)

    hp = c.execute("SELECT hp FROM users WHERE chatid='" + chat_id + "'").fetchall()[0][0]

    sticker_url, text = get_hp_sticker(hp)

    context.bot.send_sticker(chat_id=chat_id, sticker=sticker_url, disable_notification=True)

    conn.close()

    update.message.reply_text(health_bar(hp) + "\nMood: " + text)


def health_bar(hp):
    maxHP = 150
    healthDashes = 15
    dashConvert = int(maxHP / healthDashes)
    currentDashes = int(hp / dashConvert)
    remainingHealth = healthDashes - currentDashes

    healthDisplay = '- ' * currentDashes
    remainingDisplay = '  ' * remainingHealth
    percent = str(int((hp / maxHP) * 100)) + "%"

    return "| " + healthDisplay + remainingDisplay + "| " + percent


def update_health(chat_id, hp):
    conn = sqlite3.connect('dbs/users.db')
    c = conn.cursor()

    # check range
    newhp = c.execute("SELECT hp FROM users WHERE chatid='" + chat_id + "'").fetchall()[0][0] + hp

    print(newhp)
    if newhp > 150:
        c.execute("UPDATE users SET hp = 150 WHERE chatid='" + chat_id + "'")
    elif newhp < 0:
        c.execute("UPDATE users SET hp = 0 WHERE chatid = '" + chat_id + "'")
    else:
        operator = "-" if hp < 0 else "+"
        c.execute("UPDATE users SET hp = hp " + operator + " " + str(abs(hp)) + " WHERE chatid = '" + chat_id + "'")

    conn.commit()
    conn.close()


""" Daily jobs """


# Gradual HP loss.
def loss(context):
    # Deduct for all users
    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT chatid FROM USERS")]

    # Send message to all users
    for chat_id in chat_ids:
        update_health(chat_id, -5)


# Morning message sent to every user.
def morning(context):
    sticker_url = 'CAACAgUAAxkBAAIGxmDipapfXSTyJed2Yz1G5XFRt_RgAAI0AwACDyIZVyCVvC54P3gfIAQ'
    message = "☀ Good morning! It's a brand new day."

    # Send to everybody in the users db
    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT chatid FROM users")]

    # Send message to all users
    for chat_id in chat_ids:
        context.bot.send_sticker(chat_id=chat_id, sticker=sticker_url, disable_notification=True)
        context.bot.send_message(chat_id=chat_id, text=message)


# To-do list reminder + self care, sends reminders if there are items remaining on the to-do list.
def list_reminder(context):
    # sticker_url = 'CAACAgUAAxkBAAIIFmDlZCMBw6yYfKTntImNuRpVKQdZAAKzBQACoPkoV4iWYNQQxMDEIAQ'
    sticker_url = 'CAACAgUAAxkBAAIKamDoAgzCqkfj-gABbUfu5F2X8yQdOgACiwMAAuw5QFe5EDq90bFkzCAE'

    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT chatid FROM users")]
    conn.close()

    conn2 = sqlite3.connect('dbs/todolist.db')
    c2 = conn2.cursor()

    for chat_id in chat_ids:
        c2.execute("SELECT task FROM todolist WHERE chatid='" + chat_id + "'")
        rows = [i[0] for i in c2.fetchall()]

        context.bot.send_sticker(chat_id=chat_id, sticker=sticker_url, disable_notification=True)
        message = "Stay hydrated!\n"

        if len(rows) != 0:
            message += "Reminder: You have " + str(
                len(rows)) + " item(s) left on your to-do list."

        context.bot.send_message(chat_id=chat_id, text=message)

    conn2.close()


# Daily reset (11.59pm, deduct hp from meownace if there are items left in the todo list)
def daily_reset(context):
    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT chatid FROM USERS")]
    conn.close()

    conn2 = sqlite3.connect("dbs/todolist.db")
    c2 = conn2.cursor()

    for chat_id in chat_ids:
        # Get the number of items left inside the user's todolist

        rc = c2.execute("DELETE FROM todolist WHERE chatid='" + chat_id + "'").rowcount

        # Update report
        message = "🌙 It's the end of the day! Here's your report:"
        message += "\n🔖 You have " + str(rc) + " item(s) left in your to-do list."
        if rc == 0:
            message += "\n💖 Good job!"
        else:
            message += " -HP"
            message += "\n❗ To-do list has been cleared."

        # For each item, deduct 10hp
        update_health(chat_id, rc * (-20))

        sleep_sticker = 'CAACAgUAAxkBAAIGEWDieI8dC2eHsy0yDxROBXvQvbTPAAJhAwACc8EIV_ToZnIn-TSkIAQ'

        context.bot.send_sticker(chat_id=chat_id, sticker=sleep_sticker, disable_notification=True)
        context.bot.send_message(chat_id=chat_id, text=message)

        conn2.commit()

    conn2.close()


""" Misc functions """


# API call for cat fact
def get_cat_fact():
    endpoint = "https://catfact.ninja/fact"
    response = requests.get(endpoint)
    fact = response.json()["fact"]
    return fact


# Cmd for cat fact
def cat(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=get_cat_fact())


def get_inspirational():
    response = requests.get('http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en')
    return '{quoteText} - {quoteAuthor}'.format(**loads(response.text))


def inspirational(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=get_inspirational())


""" Timer """


def remove_job_if_exists(name: str, context) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def unset(update, context) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)


def timer(update, context):
    keyboard = [
        ['⏰ set timer'],
        ['ε=ε=ε=┌(╯°□°)┘ start sprint!'],
        ['⚙ sprint settings'],
        ['stop sprint!'],
    ]
    update.message.reply_text(text="Welcome to Meownace's timer! 💖 Please select options below.\n(Note: although the "
                                   "buttons are listed in minutes, the actual timings have been changed to seconds "
                                   "for easier testing. Eg: Button that says 15min will last 15s!)",
                              reply_markup=ReplyKeyboardMarkup(keyboard))


# Handler for when user presses set timer
def set_timer(update, context):
    keyboard = [[InlineKeyboardButton("15 min", callback_data='15'),
                 InlineKeyboardButton("25 min", callback_data='25'),
                 InlineKeyboardButton("30 min", callback_data='30'),
                 InlineKeyboardButton("50 min", callback_data='50'),
                 ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose your desired timing below!⏰\n', reply_markup=reply_markup)


def settings_timer(update, context):
    keyboard = [
        ['change sprint pomodoro duration'],
        ['change sprint rest duration'],
        ['change number of pomodoros'],
        ['i am done! head back please']
    ]
    update.message.reply_text(text="Please select options below!", reply_markup=ReplyKeyboardMarkup(keyboard))


def changeDur(update, context):
    keyboard = [
        ['set sprint duration to 10 min'],
        ['set sprint duration to 15 min'],
        ['set sprint duration to 20 min'],
        ['set sprint duration to 25 min'],
        ['set sprint duration to 30 min'],
        ['set sprint duration to 35 min'],
        ['set sprint duration to 40 min'],
        ['set sprint duration to 45 min'],
        ['set sprint duration to 50 min'],
        ['set sprint duration to 60 min'],
        ['i am done! head back please'],
    ]

    update.message.reply_text(text="Please select pomodoro duration below!", reply_markup=ReplyKeyboardMarkup(keyboard))


def changeRest(update, context):
    keyboard = [
        ['set sprint rest to 2 min'],
        ['set sprint rest to 3 min'],
        ['set sprint rest to 5 min'],
        ['set sprint rest to 10 min'],
        ['set sprint rest to 15 min'],
        ['i am done! head back please'],
    ]

    update.message.reply_text(text="Please select pomodoro rest time below!",
                              reply_markup=ReplyKeyboardMarkup(keyboard))


def changeNum(update, context):
    keyboard = [
        ['set number of pomodoros to 2'],
        ['set number of pomodoros to 3'],
        ['set number of pomodoros to 4'],
        ['set number of pomodoros to 5'],
        ['set number of pomodoros to 6'],
        ['set number of pomodoros to 7'],
        ['set number of pomodoros to 8'],
        ['set number of pomodoros to 9'],
        ['set number of pomodoros to 10'],
        ['i am done! head back please'],
    ]

    update.message.reply_text(text="Please select number of pomodoros below!",
                              reply_markup=ReplyKeyboardMarkup(keyboard))


# Adds the user to the sprint database with default values if they are not in the sprint database.

def insert_new_user_sprint(chat_id):
    # Connecting to the SQL database
    conn = sqlite3.connect('dbs/sprint.db')
    c = conn.cursor()

    c.execute("SELECT * FROM sprint WHERE id = " + chat_id)

    record = c.fetchone()

    if record is not None:
        print("User is already in sprint DB")
    else:
        insert_query = """INSERT INTO SPRINT
                      (ID, DURATION, REST, NUMBER) 
                       VALUES 
                      (?,?,?,?);"""
        data_tuple = (chat_id, 30, 5, 5)
        c.execute(insert_query, data_tuple)
        conn.commit()

        print("New user inserted successfully into SPRINT table ", c.rowcount)

    conn.close()


def update_sprint_table(query, data, chat_id):
    conn = sqlite3.connect('dbs/sprint.db')
    c = conn.cursor()

    c.execute(query, (data, chat_id))
    conn.commit()
    print("Record Updated successfully.")
    conn.close()


# Returns a String of the user's sprint information
def sprint_full_info(chat_id):
    conn = sqlite3.connect('dbs/sprint.db')
    c = conn.cursor()
    c.execute("SELECT * from SPRINT where ID = " + chat_id)
    chat_id, dur, rest, num = c.fetchone()

    conn.close()

    return "Sprint settings have been saved successfully. Your sprint consists of:\n" \
           + str(num) + " pomodoros 🍅\n" \
           + str(dur) + " minutes each ⌛\n" \
           + str(rest) + " minutes rest time in between 😌\n\n" \
           + "Press 'i am done' -> '⚙ sprint settings' in the keyboard if you would like to " \
           + "change anything else!\n " \
           + "If you are ready to begin your sprint, press 'i am done' -> 'start sprint' ✨"


# Change the duration for the sprint
def changeDurDB(update, context):
    string = update.message.text
    username = update.message.from_user.username
    if username is None:
        username = update.message.from_user.first_name

    newString = string.removeprefix('set sprint duration to ')[0:2]
    duration = int(newString)
    chat_id = str(update.message.chat_id)

    print(duration, chat_id)

    insert_new_user_sprint(chat_id)

    updateQuery = "UPDATE sprint SET duration=? WHERE id=?"
    update_sprint_table(updateQuery, duration, chat_id)

    update.message.reply_text(sprint_full_info(chat_id))


# Change the rest duration for sprint
def changeRestDB(update, context):
    string = update.message.text
    username = update.message.from_user.username

    if username is None:
        username = update.message.from_user.first_name

    string = string.removeprefix('set sprint rest to ')
    string = string.removesuffix(' min')

    restdur = int(string)
    chat_id = str(update.message.chat_id)
    print(restdur, chat_id)

    insert_new_user_sprint(chat_id)

    updateQuery = "UPDATE sprint SET rest=? WHERE id = ?"
    update_sprint_table(updateQuery, restdur, chat_id)

    update.message.reply_text(sprint_full_info(chat_id))


# Change the number of pomodoros for the sprint
def changeNumDB(update, context):
    string = update.message.text
    username = update.message.from_user.username

    if username is None:
        username = update.message.from_user.first_name

    newString = string.removeprefix('set number of pomodoros to ')
    number = int(newString)
    chat_id = str(update.message.chat_id)
    print(number, chat_id)

    insert_new_user_sprint(chat_id)

    updateQuery = """UPDATE sprint SET number=? WHERE id = ?"""
    update_sprint_table(updateQuery, number, chat_id)

    update.message.reply_text(sprint_full_info(chat_id))


def startSprint(update, context):
    chat_id = str(update.message.chat_id)

    conn = sqlite3.connect('dbs/sprint.db')
    c = conn.cursor()

    insert_new_user_sprint(chat_id)

    selectQuery = "SELECT * FROM sprint WHERE id = ?"
    c.execute(selectQuery, (chat_id,))
    record = c.fetchone()

    chat_id, dur, rest, num = record

    conn.close()

    n = num
    print("number of pomodoros is: ")
    print(n)
    total = n * (dur + rest)
    update.message.reply_text("Sprint started. It will last " + str(total) + " min. Your sprint consists of:\n"
                              + str(num) + " pomodoros 🍅\n"
                              + str(dur) + " minutes each ⌛\n"
                              + str(rest) + " minutes rest time in between 😌\n"
                              + "\n" + "Press stop sprint to stop sprint. ")
    newRest = 0
    newDur = dur
    while n > 0:
        context.job_queue.run_once(callback_alarm_duration, newDur * 60, context=chat_id, name=str(chat_id))
        newRest = newRest + dur + rest
        if n != 1:
            print(newRest)
            context.job_queue.run_once(callback_alarm_rest, newRest * 60, context=chat_id, name=str(chat_id))
        if n == 1:
            print(newRest)
            context.job_queue.run_once(callback_alarm_last, newRest * 60, context=chat_id, name=str(chat_id))
        newDur = newDur + rest + dur
        print(newDur)
        n -= 1


# Main button menu
class FilterSetTimer(MessageFilter):
    def filter(self, message):
        return '⏰ set timer' in message.text


class FilterSettingsTimer(MessageFilter):
    def filter(self, message):
        return '⚙ sprint settings' in message.text


class FilterSprintTimer(MessageFilter):
    def filter(self, message):
        return 'ε=ε=ε=┌(╯°□°)┘ start sprint!' in message.text


class FilterCancelTimer(MessageFilter):
    def filter(self, message):
        return 'stop sprint!' in message.text


# Filter settings options
class FilterChangeDuration(MessageFilter):
    def filter(self, message):
        return 'change sprint pomodoro duration' in message.text


class FilterChangeRest(MessageFilter):
    def filter(self, message):
        return 'change sprint rest duration' in message.text


class FilterChangeNumber(MessageFilter):
    def filter(self, message):
        return 'change number of pomodoros' in message.text


class FilterReturn(MessageFilter):
    def filter(self, message):
        return 'i am done! head back please' in message.text


# Change timings filter
class FilterSprintDuration(MessageFilter):
    def filter(self, message):
        return 'set sprint duration to ' in message.text


class FilterSprintRest(MessageFilter):
    def filter(self, message):
        return 'set sprint rest to ' in message.text


class FilterSprintNumber(MessageFilter):
    def filter(self, message):
        return 'set number of pomodoros to ' in message.text


# Callback for normal alarm
def callback_alarm_15(context) -> None:
    job = context.job
    context.bot.send_message(job.context, text='BEEP! Your 15 minutes is up! Call /set for your next round!')


def callback_alarm_25(context) -> None:
    job = context.job
    context.bot.send_message(job.context, text='BEEP! Your 25 minutes is up! Call /set for your next round!')


def callback_alarm_30(context) -> None:
    job = context.job
    context.bot.send_message(job.context, text='BEEP! Your 30 minutes is up! Call /set for your next round!')


def callback_alarm_50(context) -> None:
    job = context.job
    context.bot.send_message(job.context, text='BEEP! Your 50 minutes is up! Call /set for your next round!')


# Callback for sprint
def callback_alarm_duration(context) -> None:
    job = context.job
    id = str(job.context)
    restTime = get_sprint_info(id, 2)
    print(restTime)

    context.bot.send_message(id, text='Pomodoro is done! Please have a ' + restTime + ' min break!')


def get_sprint_info(id, num):
    conn = sqlite3.connect('dbs/sprint.db')
    c = conn.cursor()

    selectQuery = """SELECT * from SPRINT where ID = ?"""
    c.execute(selectQuery, (id,))
    record = c.fetchone()
    c.close()
    # Send user a message with the updated sprint duration

    chat_id, dur, rest, number = record
    total = number * (dur + rest)

    if num == 1:
        return str(dur)
    if num == 2:
        return str(rest)
    if num == 3:
        return str(number)
    if num == 4:
        return str(total)


def callback_alarm_rest(context) -> None:
    job = context.job
    id = job.context
    duration = get_sprint_info(id, 1)
    print(duration)
    context.bot.send_message(id, text='Pomodoro ' + duration + ' min has started!')


def callback_alarm_last(context) -> None:
    keyboard = [[InlineKeyboardButton("Sprint again!", callback_data='sprint_again'),
                 InlineKeyboardButton("Edit sprint", callback_data='edit_sprint')
                 ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    job = context.job
    id = job.context
    total = get_sprint_info(id, 4)
    print(total)
    context.bot.send_message(id,
                             text='Congratulations! You have completed your sprint of '
                                  + total + ' ! What would you like to do next?', reply_markup=reply_markup)


# For normal timer inline keyboard
def call_back(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    query.answer()
    if query.data == 'sprint_again':
        startSprint(query, context)
    if query.data == 'edit_sprint':
        settings_timer(query, context)
    if query.data == '15':
        query.answer(text='Timer started for 15 minutes.')
        context.bot.send_message(chat_id=chat_id, text='Timer started for 15 minutes')
        context.job_queue.run_once(callback_alarm_15, 900, context=chat_id, name=str(chat_id))

    if query.data == '25':
        query.answer(text='Timer started for 25 minutes')
        context.bot.send_message(chat_id=chat_id, text='Timer started for 25 minutes')
        context.job_queue.run_once(callback_alarm_25, 1500, context=chat_id, name=str(chat_id))

    if query.data == '30':
        query.answer(text='Timer started for 30 minutes')
        context.bot.send_message(chat_id=chat_id, text='Timer started for 30 minutes')
        context.job_queue.run_once(callback_alarm_30, 1800, context=chat_id, name=str(chat_id))

    if query.data == '50':
        query.answer(text='Timer started for 50 minutes')
        context.bot.send_message(chat_id=chat_id, text='Timer started for 50 minutes')
        context.job_queue.run_once(callback_alarm_50, 3000, context=chat_id, name=str(chat_id))


@send_typing_action
def stopSprint(update, context):
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Sprint successfully stopped!' if job_removed else 'You have no active sprint.'
    update.message.reply_text(text)


# Non-commands

def manage_text(update, context):
    update.message.reply_text("Meownace does not understand! Use /help for more information")


def manage_command(update, context):
    update.message.reply_text("Meownace does not recognise that command. Use /help for more information")


def error(update, context):
    # Log Errors caused by Updates.
    logger.warning('Error: "%s" caused error "%s"', update, context.error)


# Main
def main():
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    filter_settimer = FilterSetTimer()
    filter_settingsTimer = FilterSettingsTimer()
    filter_sprintTimer = FilterSprintTimer()
    filter_return = FilterReturn()

    # Commands
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('about', about))

    # TO-DO list
    dp.add_handler(CommandHandler('add', addtask))
    dp.add_handler(CommandHandler('clear', cleartask))
    dp.add_handler(CommandHandler('clearall', clearall))
    dp.add_handler(CommandHandler('delete', deletetask))
    dp.add_handler(CommandHandler('deleteall', deleteall))
    dp.add_handler(CommandHandler('list', show_list))

    # Interaction
    dp.add_handler(CommandHandler('pat', pat))
    dp.add_handler(CommandHandler('walk', walk))
    dp.add_handler(CommandHandler('feed', feed))

    # HP
    dp.add_handler(CommandHandler('health', health))

    # Study helpers
    dp.add_handler(CommandHandler("set", set_timer))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    # Cat fact
    dp.add_handler(CommandHandler('catfact', cat))

    # Inspirational
    dp.add_handler(CommandHandler('inspirational', inspirational))

    # Alarm
    dp.add_handler(CallbackQueryHandler(call_back, pass_job_queue=True))
    dp.add_handler(CommandHandler("timer", timer))
    dp.add_handler(MessageHandler(filter_settimer, set_timer))
    dp.add_handler(MessageHandler(filter_settingsTimer, settings_timer))
    dp.add_handler(MessageHandler(filter_sprintTimer, startSprint))
    dp.add_handler(MessageHandler(FilterCancelTimer(), stopSprint))
    dp.add_handler(MessageHandler(filter_return, timer))

    # Message handler for change buttons
    dp.add_handler(MessageHandler(FilterChangeDuration(), changeDur))
    dp.add_handler(MessageHandler(FilterChangeRest(), changeRest))
    dp.add_handler(MessageHandler(FilterChangeNumber(), changeNum))

    # Message handler for db side
    dp.add_handler(MessageHandler(FilterSprintDuration(), changeDurDB))
    dp.add_handler(MessageHandler(FilterSprintRest(), changeRestDB))
    dp.add_handler(MessageHandler(FilterSprintNumber(), changeNumDB))

    # Non-commands
    dp.add_handler(MessageHandler(Filters.text, manage_text))
    dp.add_handler(MessageHandler(Filters.command, manage_command))

    # Log all errors
    dp.add_error_handler(error)

    # Morning message at 6.00 am
    j = updater.job_queue
    job_morning = j.run_daily(morning, days=(0, 1, 2, 3, 4, 5, 6),
                              time=datetime.time(hour=6, minute=00, second=00, tzinfo=pytz.timezone("Asia/Singapore")))

    # Reminder message at 6.30pm SGT
    job_reminder = j.run_daily(list_reminder, days=(0, 1, 2, 3, 4, 5, 6),
                               time=datetime.time(hour=12 + 6, minute=30, second=00,
                                                  tzinfo=pytz.timezone("Asia/Singapore")))

    # Daily reset at 11.59pm SGT
    job_reset = j.run_daily(daily_reset, days=(0, 1, 2, 3, 4, 5, 6),
                            time=datetime.time(hour=23, minute=59, second=0,
                                               tzinfo=pytz.timezone("Asia/Singapore")))

    job_loss = j.run_repeating(loss, datetime.timedelta(minutes=30))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    bot_token = "TOKEN"
    main()