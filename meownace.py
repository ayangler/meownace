import sqlite3
from functools import wraps
import datetime, pytz, requests

import logging
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

    text = '🐈 Welcome to meownace, ' + str(
        update.message.from_user.first_name) + '! 🐈' + '\nType /help for more info.\n'

    context.bot.send_animation(chat_id=update.message.chat_id,
                               animation="https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/d7461165-0cc6"
                                         "-432d-8b4e-867918a69c75/dekbqui-f3ef15aa-1435-41f4-93f5-8e95be94f894.gif"
                                         "?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
                                         ".eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjo"
                                         "idXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgi"
                                         "OiJcL2ZcL2Q3NDYxMTY1LTBjYzYtNDMyZC04YjRlLTg2NzkxOGE2OWM3NVwvZGVrYnF1aS1mM2VmM"
                                         "TVhYS0xNDM1LTQxZjQtOTNmNS04ZTk1YmU5NGY4OTQuZ2lmIn1dXSwiYXVkIjpbInVybjpzZXJ2aW"
                                         "NlOmZpbGUuZG93bmxvYWQiXX0.q_AOQYIMVd45WdK3hPHAiNK7eHH_CCBmLA47ZWQGf0A",
                               caption=text)

    # Connect to the SQL db.
    conn = sqlite3.connect('dbs/users.db')
    c = conn.cursor()

    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username
    if username is None:
        username = update.message.from_user.first_name

    # Check existence of user in database. If exists, do nothing, else add chatid and username to database.
    if c.execute("SELECT 1 FROM USERS WHERE CHATID='" + chat_id + "'").fetchone():
        print("User is already recorded in db")
    else:
        c.execute("INSERT INTO USERS VALUES('" + chat_id + "','" + username + "'," + "75)")

    conn.commit()
    conn.close()


""" List of commands """


@send_typing_action
def help(update, context):
    """Send a message when the command /help is issued."""
    # context.bot.send_sticker(chat_id=update.effective_chat.id,
    #                         sticker='CAACAgUAAxkBAAIDIGDIorsZlJg8jeZHgmnO8wjZgLCjAAKLAgACY3BIVrN-6y3Hce4eHwQ',
    #                         disable_notification=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Meownace is here to help! ヾ(•ω•`)o\n'
                                  'Use the commands shown below to interact with me:\n\n'
                                  ' 📅 TODO 📅\n'
                                  '/add <name of task> - add a task \n'
                                  '/clear <name of task> or <index> - remove a finished task \n'
                                  '/clearall - remove all finished tasks \n'
                                  '/delete <name of task> or <index> - remove a task \n'
                                  '/deleteall - remove all tasks\n'
                                  '/list - show all your tasks \n\n'
                                  '🏫STUDY🏫\n'
                                  '/set - set a timer\n'
                                  '/unset - remove an existing timer \n'
                                  '/timer - choose your desired timer settings\n\n'
                                  ' 🧸 PET FUNCTIONS 🧸\n'
                                  '/health - how am i feeling right now? \n'
                                  '/pat - gimme head pats \n'
                                  '/walk - take me on a walk \n'
                                  '/inspirational - ready to be inspired? [WIP]\n'
                                  '/catfact - learn more about my species \n'
                                  '/pic - get cute cat pics [WIP]\n')


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

            message = "Added to to-do list!"

        conn.commit()
        conn.close()

        update.message.reply_text(message)
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
            update.message.reply_text("❌ Index is not in your to-do list.")
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
        update.message.reply_text("✔Task successfully cleared from your list: " + taskName + "\n+hp!")

        show_list(update, context)


@send_typing_action
def clearall(update, context):
    conn = sqlite3.connect('dbs/todolist.db')
    c = conn.cursor()
    chat_id = str(update.message.chat_id)

    rc = c.execute("DELETE FROM TODOLIST WHERE CHATID='" + chat_id + "'").rowcount

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
        update.message.reply_text("✔️ Task successfully deleted from your list: " + taskName + "\n")
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
        update.message.reply_text("Your to-do list is empty!")
    conn.commit()
    conn.close()


def show_list(update, context):
    chat_id = str(update.message.chat_id)

    rows = get_arr_of_tasks(chat_id)

    if len(rows) != 0:
        items = ""
        for i in range(0, len(rows)):
            items += str(i + 1) + ". " + rows[i] + "\n"
        update.message.reply_text("📄 " + update.message.from_user.first_name + "'s pending tasks:\n" + items)
    else:
        update.message.reply_text("Your to-do list is empty! (´･ω･`)")


""" Pet interaction """


@send_typing_action
def pat(update, context):
    update_health(str(update.message.chat_id), 1)
    # context.bot.send_sticker(chat_id = chat_id, sticker =
    # "CAACAgUAAxkBAAIBfmC9zdWSIGzwSFuGfbY2-DaM27eUAAJyAAOw6HQBc5yhV2DYgA0fBA", disable_notification = True)
    update.message.reply_text("You gave meownace a pat on the head! +hp")


@send_typing_action
def walk(update, context):
    update_health(str(update.message.chat_id), 1)
    # context.bot.send_sticker(chat_id = chat_id, sticker =
    # "CAACAgUAAxkBAAIBfmC9zdWSIGzwSFuGfbY2-DaM27eUAAJyAAOw6HQBc5yhV2DYgA0fBA", disable_notification = True)

    update.message.reply_text("You took meownace on a walk! +hp")


""" Pet's health """


@send_typing_action
def health(update, context):
    """ report current health of pet """
    conn = sqlite3.connect('dbs/users.db')
    c = conn.cursor()

    chat_id = update.message.chat_id
    chat_id = str(chat_id)

    hp = c.execute("SELECT HP FROM USERS WHERE CHATID='" + chat_id + "'").fetchall()[0][0]

    if hp == 0:
        context.bot.send_sticker(chat_id=chat_id,
                                 sticker='CAACAgUAAxkBAAIDGGDIoZZSasZYD4_yGP8ZRxLEove7AAJ-AgACl2dAVmhgDWxdCb2CHwQ',
                                 disable_notification=True)
        text = "Very upset"
    elif hp == 150:
        context.bot.send_sticker(chat_id=chat_id,
                                 sticker='CAACAgUAAxkBAAIC9GDInwJcjiituqnl1eBpBqq4hFbwAAL3AQACiPlJVvQMbOW7p78jHwQ',
                                 disable_notification=True)
        text = "Ecstatic"
    elif hp in range(1, 50):
        context.bot.send_sticker(chat_id=chat_id,
                                 sticker='CAACAgUAAxkBAAIDAWDIoGjY0F3mLKqbNEPscAaAvq29AAIfBAACEwNJVpUZ2LvHB95yHwQ',
                                 disable_notification=True)
        text = "Sad"
    elif hp in range(50, 100):
        context.bot.send_sticker(chat_id=chat_id,
                                 sticker='CAACAgUAAxkBAAIDAAFgyKAPsMHCgcLTz_kKGr9hiD1GEwACQQQAAsagQFZvDPyy_eIjox8E',
                                 disable_notification=True)
        text = "Neutral"
    else:
        context.bot.send_sticker(chat_id=chat_id,
                                 sticker='CAACAgUAAxkBAAIC7mDInlmoxvXO3UsXy6PLzpyngPXQAALpAgACZk5JVq9UssuYYljOHwQ',
                                 disable_notification=True)
        text = "Pleased"
    conn.close()

    update.message.reply_text("Mood: " + health_bar(hp) + "\n" + text)


def health_bar(hp):
    maxHP = 150
    healthDashes = 15
    dashConvert = int(maxHP / healthDashes)
    currentDashes = int(hp / dashConvert)
    remainingHealth = healthDashes - currentDashes

    healthDisplay = '- ' * currentDashes
    remainingDisplay = ' ' * remainingHealth
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


# Gradual HP loss every 2 hours.
def loss(context):
    # Deduct for all users
    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT chatid FROM USERS")]

    # Send message to all users
    for chat_id in chat_ids:
        update_health(chat_id, -1)


# Morning message sent to every user.
def morning(context):
    message = "☀ Good morning! It's a brand new day. ☀"

    # Send to everybody in the users db
    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT CHATID FROM USERS")]

    # Send message to all users
    for chat_id in chat_ids:
        context.bot.send_message(chat_id=chat_id, text=message)


# To-do list reminder, sends reminders if there are items remaining on the to-do list.

def list_reminder(context):
    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT chatid FROM USERS")]

    conn2 = sqlite3.connect('dbs/todolist.db')
    c2 = conn2.cursor()

    for chat_id in chat_ids:
        c2.execute("SELECT task FROM todolist WHERE chatid='" + chat_id + "'")
        rows = [i[0] for i in c2.fetchall()]

        # Send message only if users has items left on to-do list
        if len(rows) != 0:
            context.bot.send_message(chat_id=chat_id, text="(。・・)ノ Reminder: You have " + str(
                len(rows)) + " item(s) remaining on your to-do list.")

    conn.close()
    conn2.close()


# Daily reset (11.59pm, deduct hp from meownace if there are items left in the todo list)
def daily_reset(context):
    conn = sqlite3.connect("dbs/users.db")
    c = conn.cursor()

    conn2 = sqlite3.connect("dbs/todolist.db")
    c2 = conn2.cursor()

    chat_ids = [i[0] for i in c.execute("SELECT CHATID FROM USERS")]

    for chat_id in chat_ids:
        # Get the number of items left inside the user's todolist

        rc = c2.execute("DELETE FROM TODOLIST WHERE CHATID='" + chat_id + "'").rowcount

        # Update report
        message = "🌃 It's the end of the day! Here's your report:"
        message += "\nYou have " + str(rc) + " item(s) left in your to-do list."
        if rc == 0:
            message += "\nGood job!"
        else:
            message += "\nHp lost!"

        # For each item, deduct 10hp
        update_health(chat_id, rc * (-20))

        message += "\nTo-do list has been reset."

        context.bot.send_message(chat_id=chat_id, text=message)

        conn.commit()
        conn2.commit()

    conn2.close()
    conn.close()


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


# STUDY TIMER
# Send study timer alarm
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
    update.message.reply_text(text="Welcome to Meownace's timer~ Please select options below! (Note: although the "
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


# Change the duration for the sprint
def changeDurDB(update, context):
    string = update.message.text
    username = update.message.from_user.username
    if username is None:
        username = update.message.from_user.first_name

    newString = string.removeprefix('set sprint duration to ')
    newString = newString[0:2]
    duration = int(newString)
    print(duration)
    chat_id = update.message.chat_id
    chat_id = str(chat_id)
    print(chat_id)

    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        selectQuery = """SELECT * from SPRINT where ID = ?"""
        c.execute(selectQuery, (chat_id,))
        record = c.fetchone()
        # Check existence of user in database. If exists, do nothing, else add chatid and username to database.
        if (record != None):
            print("User is already recorded in db")
        else:
            insert_query = """INSERT INTO SPRINT
                          (ID, DURATION, REST, NUMBER) 
                           VALUES 
                          (?,?,?,?);"""
            data_tuple = (chat_id, 30, 5, 5)
            c.execute(insert_query, data_tuple)
            conn.commit()
            print("New user inserted successfully into SPRINT table ", c.rowcount)
            c.close()
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        updateQuery = """UPDATE SPRINT set DURATION=? where ID = ?"""
        data = (duration, chat_id)
        c.execute(updateQuery, data)
        conn.commit()
        print("Record Updated successfully ")
        c.close()
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        selectQuery = """SELECT * from SPRINT where ID = ?"""
        c.execute(selectQuery, (chat_id,))
        record = c.fetchone()
        # Send user a message with the updated sprint duration
        dur = str(record[1])
        rest = str(record[2])
        num = str(record[3])
        update.message.reply_text("Hi " + username + "!~ \n"
                                  + "Sprint settings have been saved successfully. Your sprint consists of:\n"
                                  + num + " pomodoros 🍅\n"
                                  + dur + " minutes each ⌛\n"
                                  + rest + " minutes rest time in between 😌\n"
                                  + "\n" +
                                  "Press 'i am done' -> '⚙ sprint settings' in the keyboard if you would like to change anything else!\n"
                                  + "If you are ready to begin your sprint, press 'i am done' -> 'start sprint'")
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")


# Change the rest duration for sprint
def changeRestDB(update, context):
    string = update.message.text
    username = update.message.from_user.username

    if username is None:
        username = update.message.from_user.first_name

    string = string.removeprefix('set sprint rest to ')
    string = string.removesuffix(' min')
    restdur = int(string)
    print(restdur)
    chat_id = update.message.chat_id
    chat_id = str(chat_id)
    print(chat_id)

    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        selectQuery = """SELECT * from SPRINT where ID = ?"""
        c.execute(selectQuery, (chat_id,))
        record = c.fetchone()
        # Check existence of user in database. If exists, do nothing, else add chatid and username to database.
        if (record != None):
            print("User is already recorded in db")
        else:
            insert_query = """INSERT INTO SPRINT
                          (ID, DURATION, REST, NUMBER) 
                           VALUES 
                          (?,?,?,?);"""
            data_tuple = (chat_id, 30, 5, 5)
            c.execute(insert_query, data_tuple)
            conn.commit()
            print("New user inserted successfully into SPRINT table ", c.rowcount)
            c.close()
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        updateQuery = """UPDATE SPRINT set REST=? where ID = ?"""
        data = (restdur, chat_id)
        c.execute(updateQuery, data)
        conn.commit()
        print("Record Updated successfully ")
        c.close()
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        selectQuery = """SELECT * from SPRINT where ID = ?"""
        c.execute(selectQuery, (chat_id,))
        record = c.fetchone()
        # Send user a message with the updated sprint duration
        dur = str(record[1])
        rest = str(record[2])
        num = str(record[3])
        update.message.reply_text("Hi " + username + "!~ \n"
                                  + "Sprint settings have been saved successfully. Your sprint consists of:\n"
                                  + num + " pomodoros 🍅\n"
                                  + dur + " minutes each ⌛\n"
                                  + rest + " minutes rest time in between 😌\n"
                                  + "\n" +
                                  "Press 'i am done' -> 'settings ⚙' in the keyboard if you would like to change "
                                  "anything else!\n "
                                  + "If you are ready to begin your sprint, press 'i am done' -> 'start sprint'")
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")


# Change the number of pomodoros for the sprint
def changeNumDB(update, context):
    string = update.message.text
    username = update.message.from_user.username

    if username is None:
        username = update.message.from_user.first_name
    newString = string.removeprefix('set number of pomodoros to ')
    number = int(newString)
    print(number)
    chat_id = update.message.chat_id
    chat_id = str(chat_id)
    print(chat_id)

    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        selectQuery = """SELECT * from SPRINT where ID = ?"""
        c.execute(selectQuery, (chat_id,))
        record = c.fetchone()
        # Check existence of user in database. If exists, do nothing, else add chatid and username to database.
        if (record != None):
            print("User is already recorded in db")
        else:
            insert_query = """INSERT INTO SPRINT
                          (ID, DURATION, REST, NUMBER) 
                           VALUES 
                          (?,?,?,?);"""
            data_tuple = (chat_id, 30, 5, 5)
            c.execute(insert_query, data_tuple)
            conn.commit()
            print("New user inserted successfully into SPRINT table ", c.rowcount)
            c.close()
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        updateQuery = """UPDATE SPRINT set NUMBER=? where ID = ?"""
        data = (number, chat_id)
        c.execute(updateQuery, data)
        conn.commit()
        print("Record Updated successfully ")
        c.close()
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")
    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        selectQuery = """SELECT * from SPRINT where ID = ?"""
        c.execute(selectQuery, (chat_id,))
        record = c.fetchone()
        # Send user a message with the updated sprint duration
        dur = str(record[1])
        rest = str(record[2])
        num = str(record[3])
        update.message.reply_text("Hi " + username + "!~ \n"
                                  + "Sprint settings have been saved successfully. Your sprint consists of:\n"
                                  + num + " pomodoros 🍅\n"
                                  + dur + " minutes each ⌛\n"
                                  + rest + " minutes rest time in between 😌\n"
                                  + "\n" +
                                  "Press 'i am done' -> '⚙ sprint settings' in the keyboard if you would like to change anything else!\n"
                                  + "If you are ready to begin your sprint, press 'i am done' -> 'start sprint'")
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")


def startSprint(update, context):
    chat_id = update.message.chat_id
    conn = sqlite3.connect('dbs/sprint.db')
    c = conn.cursor()

    selectQuery = """SELECT * from SPRINT where ID = ?"""
    c.execute(selectQuery, (chat_id,))
    record = c.fetchone()
    # Check existence of user in database. If exists, do nothing, else add chatid and username to database.
    if (record != None):
        print("User is already recorded in db")
    else:
        insert_query = """INSERT INTO SPRINT
                          (ID, DURATION, REST, NUMBER) 
                           VALUES 
                          (?,?,?,?);"""
        data_tuple = (chat_id, 30, 5, 5)
        c.execute(insert_query, data_tuple)
        conn.commit()
        print("New user inserted successfully into SPRINT table ", c.rowcount)
        c.close()
    try:
        # Connecting to the SQL database
        conn = sqlite3.connect('dbs/sprint.db')
        c = conn.cursor()

        chat_id = update.message.chat_id
        chat_id = str(chat_id)

        selectQuery = """SELECT * from SPRINT where ID = ?"""
        c.execute(selectQuery, (chat_id,))
        record = c.fetchone()

        dur = record[1]
        rest = record[2]
        num = record[3]

        c.close()
    except sqlite3.Error as error:
        print("Failed to update sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("The SQLite connection is closed")

    n = num
    print(n)
    total = n * (dur + rest)
    update.message.reply_text("Sprint started. It will last " + str(total) + " min. Your sprint consists of:\n"
                              + str(num) + " pomodoros 🍅\n"
                              + str(dur) + " minutes each ⌛\n"
                              + str(rest) + " minutes rest time in between 😌\n"
                              + "\n" + "Press stop sprint to stop sprint. ")
    restRest = rest
    durDur = dur
    while n > 0:
        context.job_queue.run_once(callback_alarm_duration, durDur, context=chat_id, name=str(chat_id))
        restRest = restRest + dur + rest
        if n != 1:
            context.job_queue.run_once(callback_alarm_rest, restRest, context=chat_id, name=str(chat_id))
        if n == 1:
            context.job_queue.run_once(callback_alarm_last, restRest, context=chat_id, name=str(chat_id))
        durDur = durDur + rest + dur
        n = n - 1


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
    id = job.context
    id = str(id)
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
    dur = record[1]
    rest = record[2]
    number = record[3]
    strdur = str(dur)
    strrest = str(rest)
    strnumber = str(number)
    total = number * (dur + rest)
    strtotal = str(total)

    if num == 1:
        return strdur
    if num == 2:
        return strrest
    if num == 3:
        return strnumber
    if num == 4:
        return strtotal


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

    # HP
    dp.add_handler(CommandHandler('health', health))

    # Study helpers
    dp.add_handler(CommandHandler("set", set_timer))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    # Cat fact
    dp.add_handler(CommandHandler('catfact', cat))

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

    # Morning message
    j = updater.job_queue
    job_morning = j.run_daily(morning, days=(0, 1, 2, 3, 4, 5, 6),
                              time=datetime.time(hour=6, minute=00, second=00, tzinfo=pytz.timezone("Asia/Singapore")))

    # Daily reset
    job_reset = j.run_daily(daily_reset, days=(0, 1, 2, 3, 4, 5, 6),
                            time=datetime.time(hour=11, minute=59, second=0,
                                               tzinfo=pytz.timezone("Asia/Singapore")))

    job_reminder = j.run_daily(list_reminder, days=(0, 1, 2, 3, 4, 5, 6),
                               time=datetime.time(hour=12 + 6, minute=30, second=00,
                                                  tzinfo=pytz.timezone("Asia/Singapore")))

    job_loss = j.run_repeating(loss, datetime.timedelta(hours=2))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    bot_token = "token"
    endpoint = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(endpoint)
    print(response.text)

    main()