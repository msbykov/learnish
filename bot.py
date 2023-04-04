# -*- coding: utf-8 -*-
import random
import telegram
from telegram.ext import Updater, CommandHandler
import datetime
import time
import requests
from bs4 import BeautifulSoup

# Функция для получения списка наиболее употребляемых слов английского языка
def get_common_words():
    url = "https://www.ef.com/wwen/english-resources/english-vocabulary/top-1000-words/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", {"class": "dataTable"}) # Находим таблицу со словами
    words = []
    for row in table.find_all("tr")[1:]: # Проходим по всем строкам таблицы, кроме заголовка
        word = row.find_all("td")[1].get_text().lower() # Берем второй столбец таблицы (слово)
        words.append(word)
    return words

# Список из наиболее употребляемых слов английского языка
words = get_common_words()

# Словарь для хранения времени отправки сообщения для каждого пользователя
user_time = {}

# Словарь для хранения слов, отправленных каждому пользователю
user_words = {}

# Функция для получения транскрипции и значений слова с помощью API Merriam-Webster
def get_word_info(word):
    api_key = "your_api_key" # Замените на свой API-ключ от Merriam-Webster
    url = "https://www.dictionaryapi.com/api/v3/references/learners/json/{word.lower()}?key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        return None, None
    data = response.json()
    if isinstance(data[0], str):
        return None, None
    transcription = data[0]["hwi"]["prs"][0]["mw"] if data[0].get("hwi") and data[0]["hwi"].get("prs") else ""
    meanings = ", ".join([d for d in data[0].get("def")[0].get("sseq")[0][0][1].get("dt")[0][1]])
    return transcription, meanings

# Функция для отправки сообщения с 10 случайными словами
def send_words(bot, job):
    # Получаем данные о пользователе из контекста задачи
    user_id = job.context['user_id']
    chat_id = job.context['chat_id']
   
    # Проверяем, прошло ли уже 24 часа с момента последней отправки слов пользователю
    if user_id in user_time and time.time() - user_time[user_id] < 86400:
        bot.send_message(chat_id=chat_id, text="Вы уже получили слова сегодня. Попробуйте позже.")
        return

    # Выбираем 10 случайных слов из списка words
    words_to_send = random.sample(words, 10)

    # Получаем список 10 случайных слов из общего списка слов
    selected_words = random.sample(words, 10)

    # Сохраняем список отправленных слов для пользователя
    user_words[user_id] = selected_words

    # Отправляем пользователю сообщение с транскрипцией и значениями каждого слова
    for word in selected_words:
        transcription, meanings = get_word_info(word)
        if transcription and meanings:
            message = "{word.capitalize()} [{transcription}]: {meanings}"
            bot.send_message(chat_id=chat_id, text=message)

    # Сохраняем время отправки сообщения для пользователя
    user_time[user_id] = time.time()
    
# Функция для обработки команды /start
def start(update, context):
    bot = context.bot
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # Отправляем пользователю приветственное сообщение
    bot.send_message(chat_id=chat_id, text="Привет! Я могу отправить тебе 10 случайных английских слов каждый день. Напиши /words, чтобы получить слова сейчас.")

    # Устанавливаем задачу на отправку слов через 10 секунд после команды /start
    context.job_queue.run_once(send_words, 10, context={"user_id": user_id, "chat_id": chat_id})
    
# Функция для обработки команды /words
def get_words(update, context):
    bot = context.bot
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

# Проверяем, прошло ли уже 24 часа с момента последней отправки слов пользователю
if user_id in user_time and time.time() - user_time[user_id] < 86400:
    bot.send_message(chat_id=chat_id, text="Вы уже получили слова сегодня. Попробуйте снова завтра.")
else:
    # Отправляем пользователю 10 случайных слов
    send_words(bot, context.job_queue.run_repeating(send_words, interval=86400, first=10, context={"user_id": user_id, "chat_id": chat_id}))

# Функция для обработки неизвестных команд
def unknown(update, context):
    bot = context.bot
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text="Извините, я не понимаю эту команду. Пожалуйста, введите /start или /words.")

# Импортируем переменную TOKEN из файла config.py
from config import TOKEN

# Создаем экземпляр класса Updater и передаем ему токен бота
updater = Updater(TOKEN, use_context=True)

# Создаем обработчики команд /start и /words
start_handler = CommandHandler('start', start)
words_handler = CommandHandler('words', get_words)

# Регистрируем обработчики команд
updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(words_handler)

# Регистрируем обработчик неизвестных команд
updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))

# Функция для обработки команды /help
def help_command(update, context):
    """Отправляет справочное сообщение о боте"""
    update.message.reply_text("""Этот бот отправляет случайные слова на английском языке со значениями и транскрипцией. Чтобы получить 10 слов, напишите /words. Чтобы получить информацию о слове, напишите /info [слово].""")

# Функция для обработки команды /words
def words_command(update, context):
    """Отправляет 10 случайных слов"""

# Получаем данные о пользователе из объекта update
user_id = update.message.chat_id

# Проверяем, прошло ли уже 24 часа с момента последней отправки слов пользователю
if user_id in user_time and time.time() - user_time[user_id] < 86400:
    update.message.reply_text("Вы уже получили слова сегодня. Попробуйте еще раз завтра.")
    return

# Получаем 10 случайных слов из списка words
user_words[user_id] = random.sample(words, 10)

# Формируем сообщение со словами и отправляем его
message = "Вот 10 случайных слов на английском языке:\n\n" + "\n".join(user_words[user_id])
update.message.reply_text(message)

# Обновляем время отправки сообщения для пользователя
user_time[user_id] = time.time()
# Функция для обработки команды /info
def info_command(update, context):
    """Отправляет информацию о слове"""
# Получаем данные о пользователе из объекта update
user_id = update.message.chat_id

# Получаем слово из сообщения пользователя
word = " ".join(context.args).lower()

# Проверяем, отправлялось ли слово пользователю ранее
if user_id not in user_words or word not in user_words[user_id]:
    update.message.reply_text("Вы не получали слово {word} сегодня. Напишите /words, чтобы получить новые слова.")
    return

# Получаем транскрипцию и значения слова
transcription, meanings = get_word_info(word)

# Формируем сообщение с информацией о слове и отправляем его
message = "{word.capitalize()} - {transcription}\n\nMeanings:\n{meanings}"
update.message.reply_text(message)
# Функция для запуска бота
def main():
    # получаем токен бота из файла config
    token = config.TOKEN

# Создаем объект Updater и получаем токен бота из переменной окружения TELEGRAM_BOT_TOKEN
updater = Updater(token=os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)

# Получаем диспетчер сообщений из объекта updater
dispatcher = updater.dispatcher

# Регистрируем обработчики команд
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("words", words_command))
dispatcher.add_handler(CommandHandler("info", info_command))

# Запускаем бота

# Функция для обработки команды /start
def start(update, context):
    # Отправляем приветственное сообщение и инструкцию по использованию бота
    context.bot.send_message(chat_id=update.message.chat_id, text="Привет! Я могу отправлять тебе новые слова каждый день.\n\nДля начала работы отправь мне команду /words.")

# Функция для обработки команды /words
def words(update, context):
    # Получаем идентификатор пользователя и чат
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

# Создаем задачу для отправки слов и запоминаем время отправки для данного пользователя
job = context.job_queue.run_daily(send_words, time=datetime.time(hour=9), context={"user_id": user_id, "chat_id": chat_id})
user_time[user_id] = time.time()

# Отправляем сообщение с подтверждением и инструкцией по отмене задачи
context.bot.send_message(chat_id=chat_id, text="Я буду присылать тебе новые слова каждый день в 9 утра.\n\nЧтобы остановить рассылку, отправь мне команду /stop.")
# Функция для обработки команды /stop
def stop(update, context):
    # Получаем идентификатор пользователя и чат
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

# Отменяем задачу для данного пользователя и удаляем время отправки и слова для него
if user_id in user_time:
    job = context.job_queue.get_jobs_by_name(str(user_id))[0]
    job.schedule_removal()
    del user_time[user_id]
    del user_words[user_id]

# Отправляем сообщение с подтверждением отмены рассылки
context.bot.send_message(chat_id=chat_id, text="Рассылка остановлена.")
# Функция для обработки текстовых сообщений
def message(update, context):
    # Получаем текст сообщения и идентификатор пользователя
    text = update.message.text
    user_id = update.message.from_user.id

# Проверяем, не является ли сообщение командой, иначе игнорируем его
if text.startswith("/") or not user_id in user_time:
    return

# Добавляем слово в словарь для данного пользователя
if user_id in user_words:
    user_words[user_id].append(text.lower())
else:
    user_words[user_id] = [text.lower()]
# Функция для обработки неизвестных команд
def unknown(update, context):
    # Отправляем сообщение с инструкцией по использованию бота
    context.bot.send_message(chat_id=update.message.chat_id, text="Я не понимаю эту команду.\n\nДля начала работы отправь мне команду /words.")

# Создаем объект бота и добавляем обработчики команд и сообщений
updater = Updater(token="your_token", use_context=True)
dispatcher = updater.dispatcher
