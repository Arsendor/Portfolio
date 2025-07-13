from logic import DB_Manager
from config import *
from config import TOKEN
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "Отмена 🚫"
def cansel(message):
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info 😉.", reply_markup=hideBoard)
  
def no_projects(message):
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!\nМожешь добавить их с помошью команды /new_project 📎.')

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_projects = {'Имя проекта' : ["Введите новое имя проекта", "project_name"],
                          "Описание" : ["Введите новое описание проекта", "description"],
                          "Ссылка" : ["Введите новую ссылку на проект", "url"],
                          "Статус" : ["Выберите новый статус задачи", "status_id"]}

def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Навыки пока не добавлены'
    bot.send_message(message.chat.id, f"""Project name: {info[0]}
Description: {info[1]}
Link: {info[2]}
Status: {info[3]}
Skills: {skills}
""")
#Хэндлер для начала работы с ботом
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """Привет!👋 Я бот-менеджер проектов 💠. 
Помогу тебе сохранить твои проекты и информацию о них 😀!) 
""")
    info(message)

#Хэндлер для получения информации о командах
@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
"""
Вот команды которые могут тебе помочь:

/new_project - используй для добавления нового проекта ➕,
/skills - используй для добавления навыков к проекту 🛠️,
/projects - используй для просмотра всех проектов 📂,
/delete - используй для удаления проекта 🗑️,
/update_projects - используй для обновления информации о проекте 🔄.

Также ты можешь ввести имя проекта и узнать информацию о нем 💡!""")

#Хэндлер для добавления нового проекта
@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

#Функция для обработки названия проекта
#и перехода к следующему шагу - описанию проекта
def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "Введите описание проекта:")
    bot.register_next_step_handler(message, description_project, data=data)

#Функция для обработки описания проекта
#и перехода к следующему шагу - ссылке на проект
def description_project(message, data):
    description = message.text
    data.append(description)
    bot.send_message(message.chat.id, "Введите ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)

#Функция для обработки ссылки на проект
#и перехода к следующему шагу - статусу проекта
def link_project(message, data):
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()] 
    bot.send_message(message.chat.id, "Введите текущий статус проекта:", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

#Функция для обработки статуса проекта
#и перехода к следующему шагу - загрузке изображения проекта
def callback_project(message, data, statuses):
    status = message.text

    if status == cancel_button:
        cansel(message)
        return

    if status not in statuses:
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй ещё раз 🎯!", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return

    status_id = manager.get_status_id(status)
    data.append(status_id)

    bot.send_message(
        message.chat.id,
        "Теперь можешь отправить изображение проекта или нажми 'Пропустить':",
        reply_markup=gen_markup(["Пропустить"])
    )
    bot.register_next_step_handler(message, save_project, data=data)

#Функция для сохранения проекта в базе данных
#и отправки сообщения об успешном сохранении
def save_project(message, data):
    user_id, name, description, url, status_id = data

    if message.text == cancel_button:
        cansel(message)
        return

    file_id = None
    file_blob = None

    if message.text == "Пропустить":
        pass
    elif message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id

        file_info = bot.get_file(file_id)
        file_blob = bot.download_file(file_info.file_path)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправь фото или нажми 'Пропустить'.")
        bot.register_next_step_handler(message, save_project, data=data)
        return

    manager.insert_full_project(user_id, name, description, url, status_id, file_id, file_blob)
    bot.send_message(message.chat.id, "Проект сохранён ✔!", reply_markup=hideBoard)

#Хэндлер для добавления навыков к проекту
@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, 'Выбери проект, для которого нужно выбрать навык 🎯.', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)

#Функция для обработки выбора проекта и перехода к выбору навыка
def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта ❌, попробуй еще раз 🔃! Выбери проект, для которого нужно выбрать навык 🎯.', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, 'Выбери навык 🛠.', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

#Функция для обработки выбора навыка и добавления его к проекту
def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, 'Видимо, ты выбрал навык не из спика, попробуй еще раз 🔃! Выбери навык 🛠.', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill )
    bot.send_message(message.chat.id, f'Навык {skill} добавлен проекту {project_name} ✔.', reply_markup=hideBoard)

#Хэндлер для получения списка проектов
@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)

#Хэндлер для удаления проекта
@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)

#Функция для обработки удаления проекта
def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id

    if message.text == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта ❌, попробуй выбрать еще раз 🔃!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'Проект {project} удален 🧹!', reply_markup=hideBoard)

#Хэндлер для обновления информации о проекте
@bot.message_handler(commands=['update_projects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить 🎯.", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
    else:
        no_projects(message)

#Функция для обработки выбора проекта и перехода к выбору атрибута для обновления
def update_project_step_2(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так!) Выбери проект, который хочешь изменить, еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
        return
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте:", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

#Функция для обработки выбора атрибута и перехода к обновлению информации
#Если выбран статус, то предоставляется список доступных статусов
def update_project_step_3(message, project_name):
    attribute = message.text
    reply_markup = None 
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся 🧐, попробуй еще раз 🔃!", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup=gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup = reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

#Функция для обновления информации о проекте
#Если выбран статус, то проверяется его корректность
def update_project_step_4(message, project_name, attribute): 
    update_info = message.text
    if attribute== "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз 🔄!", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "Готово 🕊! Обновления внесены 🙌!", reply_markup=hideBoard)

#Хэндлер для обработки текстовых сообщений
#Если текст совпадает с именем проекта, то выводится информация о проекте
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects =[ x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "Тебе нужна помощь 🔆?")
    info(message)

  
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()