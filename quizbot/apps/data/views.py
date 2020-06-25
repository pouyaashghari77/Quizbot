from random import shuffle
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from .models import User, Quiz, QuizAttempt
from .strings import Strings
import os
import mimetypes


token = "501245946:AAE1ITYGn17d2WbCh2ld7cmr1dCbeKK-E9U"
token = "1185340658:AAFMgSxgeUyPZAL1wtNla61I8lix0T3IME0"

token = "1241363538:AAFJlqW-18mXC_iOFMK_Z_lDNWcBfUedKCs"

tlgrph_token = "2319402d25c11d357badd7980bfe31b7b37b49c4bc23009d03d6d61fe649"
bot = TeleBot(token=token)
owners = [191407555, 344539579]
strings = Strings()
channel = -1001268256971

# STEP definitions
STEP_WAITING_FOR_QUIZ_QUESTION = 1
STEP_WAITING_FOR_QUIZ_OPTION1 = 11
STEP_WAITING_FOR_QUIZ_OPTION2 = 12
STEP_WAITING_FOR_QUIZ_OPTION3 = 13
STEP_WAITING_FOR_QUIZ_OPTION4 = 14
STEP_WAITING_FOR_QUIZ_OPT1_DESCRIPTION = 15
STEP_WAITING_FOR_QUIZ_OPT2_DESCRIPTION = 16
STEP_WAITING_FOR_QUIZ_OPT3_DESCRIPTION = 17
STEP_WAITING_FOR_QUIZ_OPT4_DESCRIPTION = 18

STEP_WAITING_FOR_QUIZ_CONFIRMATION = 3
STEP_MAIN_MENU = 0

QUIZ_TYPE_PHOTO = 1
QUIZ_TYPE_TEXT = 2

QUIZ_PER_PAGE = 5
QUIZ_MAX_QUIZZES_TO_SHOW = 50
QUIZ_ITEM_PREVIEW_LENGTH = 40
QUIZ_PAGES_PER_LINE = 7


def get_current_directory():
    return os.getcwd() + '/'

def show_admin_panel(m):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(strings.create_test_button_text)
    markup.row(strings.show_pending_tests_button_text)
    markup.row(strings.show_best_results)
    markup.row(strings.cancel_button_text)
    bot.send_message(m.chat.id, strings.main_menu, reply_markup=markup)


def has_voted(quiz: Quiz, user: User):
    return QuizAttempt.filter(quiz=quiz, user=user).first()


def is_admin(tg_id):
    try:
        global owners
        admins = bot.get_chat_administrators(channel)
        tg_ids = [x.user.id for x in admins]
        owners.extend(tg_ids)
        owners = list(set(owners))
        if tg_id in owners:
            return True
        return False
    except:
        return tg_id in owners


def send_button(quiz: Quiz):
    send_now = InlineKeyboardButton(
        text=strings.quiz_send_now_button_string,
        callback_data="qsendnow_{}".format(quiz.id)
    )
    send_later = InlineKeyboardButton(
        text=strings.quiz_send_later_button_string,
        callback_data="qsendlater_{}".format(quiz.id)
    )
    delete = InlineKeyboardButton(
        text=strings.delete_quiz,
        callback_data="qdel_{}".format(quiz.id)
    )
    return send_now, send_later, delete


def get_quizzes(page=1, ready=False, is_played=False):
    all_quizzes = Quiz.filter(ready=ready, is_played=is_played).order_by('created_time')
    if len(all_quizzes) > QUIZ_MAX_QUIZZES_TO_SHOW:
        all_quizzes = all_quizzes[len(all_quizzes)-QUIZ_MAX_QUIZZES_TO_SHOW:]
    pages = len(all_quizzes) // QUIZ_PER_PAGE + 0 if len(all_quizzes) % QUIZ_PER_PAGE == 0 else 1
    if page > pages > 0:
        page = pages
    if len(all_quizzes) > 0:
        text = ""
        for i in range(len(all_quizzes)):
            quiz = all_quizzes[i]
            camera_icon = "🏞 " if quiz.photo else ""
            end = "" if len(quiz.question) <= QUIZ_ITEM_PREVIEW_LENGTH else "..."
            text += strings.quizzes_list_item.format(
                    i+1,
                    camera_icon,
                    quiz.question[:QUIZ_ITEM_PREVIEW_LENGTH] + end
                )
    else:
        text = strings.quizzes_no_quiz_to_show
    markup = InlineKeyboardMarkup(row_width=QUIZ_PAGES_PER_LINE)
    page_buttons = []
    for i in range(len(all_quizzes)):
        page_buttons.append(
            InlineKeyboardButton(
                text=str(i+1),
                callback_data="qdetails_{}".format(all_quizzes[i].id)
            )
        )
    markup.add(*page_buttons)
    return text, markup


def get_image_link(image_file_id):
    try:
        path = bot.get_file(image_file_id).file_path
        print(path)
        file_dl_url = "https://api.telegram.org/file/bot{}/{}"
        image_file = requests.get(file_dl_url.format(token, path))
        full_path = get_current_directory() + path
        full_path = full_path.replace('\\', '/')
        with open(full_path, 'wb') as f:
            f.write(image_file.content)
        uploaded = upload_file(full_path)
        return 'https://telegra.ph' + uploaded[0]
    except Exception as e:
        print("UPLOAD ERROR:", e)
        return None


def upload_file(f):
    """ Upload file to Telegra.ph's servers. Returns a list of links.
        Allowed only .jpg, .jpeg, .png, .gif and .mp4 files.
    :param f: filename or file-like object.
    :type f: file, str or list
    """
    with FilesOpener(f) as files:
        response = requests.post(
            'https://telegra.ph/upload',
            files=files
        ).json()

    if isinstance(response, list):
        error = response[0].get('error')
    else:
        error = response.get('error')

    if error:
        raise TelegraphException(error)

    return [i['src'] for i in response]


class FilesOpener(object):
    def __init__(self, paths, key_format='file{}'):
        if not isinstance(paths, list):
            paths = [paths]

        self.paths = paths
        self.key_format = key_format
        self.opened_files = []

    def __enter__(self):
        return self.open_files()

    def __exit__(self, type, value, traceback):
        self.close_files()

    def open_files(self):
        self.close_files()

        files = []

        for x, file_or_name in enumerate(self.paths):
            name = ''
            if isinstance(file_or_name, tuple) and len(file_or_name) >= 2:
                name = file_or_name[1]
                file_or_name = file_or_name[0]

            if hasattr(file_or_name, 'read'):
                f = file_or_name

                if hasattr(f, 'name'):
                    filename = f.name
                else:
                    filename = name
            else:
                filename = file_or_name
                f = open(filename, 'rb')
                self.opened_files.append(f)

            mimetype = mimetypes.MimeTypes().guess_type(filename)[0]

            files.append(
                (self.key_format.format(x), ('file{}'.format(x), f, mimetype))
            )

        return files

    def close_files(self):
        for f in self.opened_files:
            f.close()

        self.opened_files = []


def get_quiz_stats(quiz: Quiz, user: User):
    all_attempts = quiz.quizattempt_set.all()
    attempted = True if all_attempts.filter(user=user).first() else False
    option1_count = all_attempts.filter(option=1)
    option2_count = all_attempts.filter(option=2)
    option3_count = all_attempts.filter(option=3)
    option4_count = all_attempts.filter(option=4)
    if len(all_attempts) > 0:
        percent_per_attempt = 100 / len(all_attempts)
    else:
        percent_per_attempt = 0

    data = {
        'attempts': len(all_attempts),
        '1': {'overall': len(option1_count), 'percent': len(option1_count)*percent_per_attempt},
        '2': {'overall': len(option2_count), 'percent': len(option2_count)*percent_per_attempt},
        '3': {'overall': len(option3_count), 'percent': len(option3_count)*percent_per_attempt},
        '4': {'overall': len(option4_count), 'percent': len(option4_count)*percent_per_attempt},
        'attempted': attempted
    }
    return data


def quiz_preview(quiz: Quiz):
    quiz_type = QUIZ_TYPE_PHOTO if quiz.photo else QUIZ_TYPE_TEXT
    markup = InlineKeyboardMarkup(row_width=2)
    options = [quiz.option1, quiz.option2, quiz.option3, quiz.option4]
    options_detailed = {
        '1': quiz.option1,
        '2': quiz.option2,
        '3': quiz.option3,
        '4': quiz.option4,
    }
    option_buttons = [
        InlineKeyboardButton(text=options[0], callback_data="qoption_{}_1".format(quiz.id)),
        InlineKeyboardButton(text=options[1], callback_data="qoption_{}_2".format(quiz.id)),
        InlineKeyboardButton(text=options[2], callback_data="qoption_{}_3".format(quiz.id)),
        InlineKeyboardButton(text=options[3], callback_data="qoption_{}_4".format(quiz.id))
    ]
    shuffle(option_buttons)
    stats_button = InlineKeyboardButton(text=strings.stats_button_text, callback_data="qstats_{}".format(quiz.id))
    # markup.row(option_buttons[0], option_buttons[1])
    # markup.row(option_buttons[2], option_buttons[3])
    tmp_btns = []
    for i in option_buttons:
        if len(options_detailed[i.callback_data.split('_')[-1]]) > 15:
            markup.row(i)
        else:
            tmp_btns.append(i)
        if len(tmp_btns) >= 2:
            markup.add(*tmp_btns)
            tmp_btns = []
    if tmp_btns:
        markup.add(*tmp_btns)
    markup.row(stats_button)
    try:
        channel_username = bot.get_chat(channel).username
    except:
        channel_username = '404'
    footer = "\n\nKanalga a'zo bo'ling\n👉 @{} 👈".format(channel_username)
    photo = ''
    if quiz.photo:
        photo = '<a href="{}">‌‌‎</a>'.format(quiz.photo)
    return quiz_type, photo + quiz.question + footer, markup


@bot.message_handler(content_types=['text', 'photo'])
def msg(m):
    uid = m.from_user.id
    text = m.text if m.text else ""
    user = User.get(tg_id=uid)
    user = User.get(tg_id=uid)
    if not user:
        user = User.create(tg_id=uid)
    # commands go here
    if text == '/start':
        user.step = STEP_MAIN_MENU
        user.save()
        if uid in owners:
            # if user is owner
            show_admin_panel(m)
        # here comes greeting part
        bot.reply_to(m, strings.welcome)
        return
    if is_admin(uid):
        if text == '/newquiz' or text == strings.create_test_button_text:
            if user.step == STEP_MAIN_MENU:
                bot.reply_to(m, strings.new_quiz)
                user.step = STEP_WAITING_FOR_QUIZ_QUESTION
                user.save()
            else:
                bot.reply_to(m, strings.finish_first)
            return
        elif text == '/cancel' or text == strings.cancel_button_text:
            user.step = STEP_MAIN_MENU
            user.save()
            bot.reply_to(m, strings.cancelled)
            show_admin_panel(m)
            return
        elif text == '/pending' or text == strings.show_pending_tests_button_text:
            text, markup = get_quizzes(1, ready=True)
            bot.reply_to(m, text, parse_mode="html", reply_markup=markup)
            return
        elif text == strings.show_best_results:
            testers = QuizAttempt.objects.values('user').distinct()
            results = {}
            for tester in testers:
                score = QuizAttempt.filter(user=tester['user'], option=1).count()
                results[tester['user']] = score
            sorted_dict = {k: v for k, v in sorted(results.items(), key=lambda item: item[1], reverse=True)}

            text = ""
            n = 1
            for i in list(sorted_dict.keys())[:20]:
                user = User.get(id=i)
                try:
                    # user_chat = bot.get_chat(user.tg_id)
                    # print(user_chat)
                    text += "{}. <a href=\"tg://user?id={}\">{}</a>: {} ball\n".format(
                        n,
                        user.tg_id,
                        bot.get_chat(user.tg_id).first_name,
                        sorted_dict[i]
                    )
                    n += 1
                except:
                    print(i)
                    pass
            if not text:
                text = "Natijalar topilmadi"
            bot.reply_to(m, text, parse_mode="html")

    if user.step == STEP_WAITING_FOR_QUIZ_QUESTION:
        if m.photo:
            if not m.caption:
                bot.reply_to(m, strings.caption_not_found)
                return
            photo = m.photo[-1].file_id
            image_url = get_image_link(photo)
            question = m.caption
            new_quiz = Quiz.create(question=question, photo=image_url)
            user.temp_data = new_quiz.id
            user.step = STEP_WAITING_FOR_QUIZ_OPTION1
            user.save()
            bot.reply_to(m, strings.send_option_true)
        elif text:
            question = text
            new_quiz = Quiz.create(question=question)
            user.temp_data = new_quiz.id
            user.step = STEP_WAITING_FOR_QUIZ_OPTION1
            user.save()
            bot.reply_to(m, strings.send_option_true)
        else:
            bot.reply_to(m, strings.unknown_command)
        return

    elif user.step == STEP_WAITING_FOR_QUIZ_OPTION1:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return
            quiz.option1 = text
            quiz.save()
            user.step = STEP_WAITING_FOR_QUIZ_OPT1_DESCRIPTION
            user.save()
            bot.send_message(uid, strings.send_description)
        else:
            bot.reply_to(m, strings.unknown_command)

    elif user.step == STEP_WAITING_FOR_QUIZ_OPT1_DESCRIPTION:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return
            quiz.description = text
            quiz.save()
            user.step = STEP_WAITING_FOR_QUIZ_OPTION2
            user.save()
            bot.send_message(uid, strings.send_option_send_others)
            bot.send_message(uid, strings.send_option_2)
        else:
            bot.reply_to(m, strings.unknown_command)

    elif user.step == STEP_WAITING_FOR_QUIZ_OPTION2:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return

            quiz.option2 = text
            quiz.save()
            user.step = STEP_WAITING_FOR_QUIZ_OPT2_DESCRIPTION
            user.save()
            bot.send_message(uid, strings.send_description_2)
        else:
            bot.reply_to(m, strings.unknown_command)

    elif user.step == STEP_WAITING_FOR_QUIZ_OPT2_DESCRIPTION:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return
            quiz.description2 = text
            quiz.save()
            user.step = STEP_WAITING_FOR_QUIZ_OPTION3
            user.save()
            bot.send_message(uid, strings.send_option_3)
        else:
            bot.reply_to(m, strings.unknown_command)

    elif user.step == STEP_WAITING_FOR_QUIZ_OPTION3:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return
            quiz.option3 = text
            quiz.save()
            user.step = STEP_WAITING_FOR_QUIZ_OPT3_DESCRIPTION
            user.save()
            bot.send_message(uid, strings.send_description_3)
        else:
            bot.reply_to(m, strings.unknown_command)

    elif user.step == STEP_WAITING_FOR_QUIZ_OPT3_DESCRIPTION:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return
            quiz.description3 = text
            quiz.save()
            user.step = STEP_WAITING_FOR_QUIZ_OPTION4
            user.save()
            bot.send_message(uid, strings.send_option_4)
        else:
            bot.reply_to(m, strings.unknown_command)

    elif user.step == STEP_WAITING_FOR_QUIZ_OPTION4:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return
            quiz.option4 = text
            quiz.save()
            user.step = STEP_WAITING_FOR_QUIZ_OPT4_DESCRIPTION
            user.save()
            bot.send_message(uid, strings.send_description_4)
            return
        else:
            bot.reply_to(m, strings.unknown_command)

    elif user.step == STEP_WAITING_FOR_QUIZ_OPT4_DESCRIPTION:
        if text:
            quiz_id = user.temp_data
            quiz = Quiz.get(id=int(quiz_id))
            if not quiz:
                bot.reply_to(m, strings.quiz_not_found)
                return
            quiz.description3 = text
            quiz.ready = True
            quiz.save()
            user.step = STEP_MAIN_MENU
            user.save()
            quiz_type, question, quiz_markup = quiz_preview(quiz)
            if not quiz_type:
                bot.reply_to(m, strings.quiz_not_found)
                return
            send_now, send_later, delete = send_button(quiz)
            quiz_markup.row(send_now, send_later)
            quiz_markup.row(delete)
            bot.send_message(uid, text=question, parse_mode="html", reply_markup=quiz_markup)
            user.step = STEP_MAIN_MENU
            user.save()
        else:
            bot.reply_to(m, strings.unknown_command)


@bot.callback_query_handler(lambda x: True)
def callback(call):
    uid = call.from_user.id
    m = call.message
    data = call.data
    user = User.get(tg_id=uid)
    if not user:
        user = User.create(tg_id=uid)
    if data.startswith("qsendnow_"):
        quiz_id = int(data.replace('qsendnow_', ''))
        quiz = Quiz.get(id=quiz_id)
        if not quiz:
            bot.reply_to(m, strings.quiz_not_found)
        else:
            quiz_type, question, markup = quiz_preview(quiz)
            bot.send_message(channel, text=question, parse_mode="html", reply_markup=markup)
            quiz.is_played = True
            quiz.save()
            bot.delete_message(uid, m.message_id)
            bot.send_message(uid, strings.quiz_sent)
        show_admin_panel(m)

    elif data.startswith("qsendlater_"):
        quiz_id = int(data.replace('qsendlater_', ''))
        quiz = Quiz.get(id=quiz_id)
        if not quiz:
            bot.reply_to(m, strings.quiz_not_found)
        else:
            quiz.scheduled = True
            quiz.save()
            bot.delete_message(uid, m.message_id)
            bot.send_message(uid, strings.quiz_saved)
        show_admin_panel(m)

    elif data.startswith("qoption_"):
        data = data.replace("qoption_", "").split("_")
        quiz_id = int(data[0])
        option_index = data[1]
        quiz = Quiz.get(id=quiz_id)
        attempt = has_voted(quiz, user)
        if not quiz:
            bot.answer_callback_query(call.id, strings.quiz_not_found, show_alert=True)
            return
        stats = get_quiz_stats(quiz, user)

        descriptions = {
            '1': quiz.description,
            '2': quiz.description2,
            '3': quiz.description3,
            '4': quiz.description4,
        }
        description = descriptions.get(option_index, False)
        if description:
            description += '\n'
        else:
            description = ''

        if attempt:
            submitted_answer = quiz.option1
            if attempt.option == 2:
                submitted_answer = quiz.option2
            elif attempt.option == 3:
                submitted_answer = quiz.option3
            elif attempt.option == 4:
                submitted_answer = quiz.option4
            if attempt.option == int(option_index):
                if option_index == '1':
                    # user found the answer
                    bot.answer_callback_query(
                        call.id,
                        strings.true_answer_alert_message.format(
                            description,
                            stats[option_index]['overall'],
                            stats[option_index]['percent'],
                            stats['attempts']
                        ),
                        show_alert=True
                    )
                else:
                    # user is wrong
                    bot.answer_callback_query(
                        call.id,
                        strings.wrong_answer_alert_message.format(
                            description,
                            stats[option_index]['overall'],
                            stats[option_index]['percent'],
                            stats['attempts']
                        ),
                        show_alert=True
                    )
                    bot.answer_callback_query(call.id, strings.no, show_alert=True)
            bot.answer_callback_query(call.id, strings.already_answered.format(submitted_answer), show_alert=True)
        else:
            attempt = QuizAttempt.create(quiz, user, int(option_index))
            stats = get_quiz_stats(quiz, user)
            submitted_answer = quiz.option1
            if attempt.option == 2:
                submitted_answer = quiz.option2
            elif attempt.option == 3:
                submitted_answer = quiz.option3
            elif attempt.option == 4:
                submitted_answer = quiz.option4
            if option_index == '1':
                # user found the answer
                bot.answer_callback_query(
                    call.id,
                    strings.true_answer_alert_message.format(
                        description,
                        stats[option_index]['overall'],
                        stats[option_index]['percent'],
                        stats['attempts']
                    ),
                    show_alert=True
                )
            else:
                # user is wrong
                bot.answer_callback_query(
                    call.id,
                    strings.wrong_answer_alert_message.format(
                        description,
                        stats[option_index]['overall'],
                        stats[option_index]['percent'],
                        stats['attempts']
                    ),
                    show_alert=True
                )
                bot.answer_callback_query(call.id, strings.no, show_alert=True)

    elif data.startswith('qstats_'):
        quiz_id = int(data.replace("qstats_", ""))
        quiz = Quiz.get(id=quiz_id)
        if not quiz:
            bot.answer_callback_query(call.id, strings.quiz_not_found, show_alert=True)
        else:
            if not has_voted(quiz, user):
                bot.answer_callback_query(call.id, strings.answer_first, show_alert=True)
            else:
                stats = get_quiz_stats(quiz, user)
                # prepare stats and show
                op_length = 25
                op1 = quiz.option1
                if len(quiz.option1) > op_length:
                    op1 = "..." + op1[len(quiz.option1)-op_length:]
                op2 = quiz.option2
                if len(quiz.option2) > op_length:
                    op2 = "..." + op2[len(quiz.option2)-op_length:]
                op3 = quiz.option3
                if len(quiz.option3) > op_length:
                    op3 = "..." + op3[len(quiz.option3)-op_length:]
                op4 = quiz.option4
                if len(quiz.option4) > op_length:
                    op4 = "..." + op4[len(quiz.option4)-op_length:]

                bot.answer_callback_query(
                    call.id,
                    strings.quiz_stats_alert_message.format(
                        op1, stats['1']['overall'], stats['1']['percent'],
                        op2, stats['2']['overall'], stats['2']['percent'],
                        op3, stats['3']['overall'], stats['3']['percent'],
                        op4, stats['4']['overall'], stats['4']['percent'],
                        stats['attempts']
                    ),
                    show_alert=True
                )
    elif data.startswith("qdetails_"):
        quiz_id = data.replace("qdetails_", "")
        quiz = Quiz.get(id=quiz_id)
        if not quiz:
            bot.answer_callback_query(call.id, strings.quiz_not_found)
            return
        quiz_type, question, markup = quiz_preview(quiz)
        send_now, send_later, delete = send_button(quiz)
        quiz_type_string = "text"
        back = InlineKeyboardButton(text=strings.back, callback_data="pending_" + quiz_type_string)
        markup.row(send_now, send_later)
        markup.row(delete)
        markup.row(back)
        bot.edit_message_text(text=question, chat_id=uid, message_id=m.message_id, parse_mode="html",
                                  reply_markup=markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("pending_"):
        text, markup = get_quizzes(1, ready=True)
        if data == "pending_photo":
            bot.delete_message(uid, m.message_id)
            bot.send_message(uid, text, parse_mode="html", reply_markup=markup)
        elif data == "pending_text":
            bot.edit_message_text(
                text,
                chat_id=uid, message_id=m.message_id, parse_mode="html", reply_markup=markup
            )
        bot.answer_callback_query(call.id)
    elif data.startswith("qdel_"):
        quiz_id = int(data.replace("qdel_", ""))
        quiz = Quiz.get(id=quiz_id)
        if not quiz:
            bot.answer_callback_query(call.id, strings.quiz_not_found, show_alert=True)
            return
        quiz.delete()
        bot.edit_message_text(strings.quiz_deleted, chat_id=uid, message_id=m.message_id)
        bot.answer_callback_query(call.id)


@csrf_exempt
def main_webhook(request):
    if request.headers.get('content-type') == 'application/json':
        json_string = request.body.decode('utf-8')
        update = Update.de_json(json_string)
        bot.process_new_updates([update])
        return JsonResponse({'ok': True})
    else:
        return JsonResponse({'ok': False})
