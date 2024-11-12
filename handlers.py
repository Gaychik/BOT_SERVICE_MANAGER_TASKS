from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler,MessageHandler,filters,ContextTypes, Application,ConversationHandler
import requests
from keyboards import *

async def start(update:Update,context):
    user=update.message.from_user.to_dict()
    response=requests.post("http://127.0.0.1:8000/users",json=user)
    res=response.json()
    if res['is_admin']:
        keyboard = keyboard_admin_base 
    else:
        keyboard = keyboard_user
    reply_markup= ReplyKeyboardMarkup(keyboard,resize_keyboard=True)    
    await update.message.reply_text("что буим делать?",reply_markup=reply_markup)
    
CHOOSING,ASSIGNTASK = range(2)
ERROR = -1

def get_users_by_api_to_str(context)->str:
    response = requests.get("http://127.0.0.1:8000/users")
    users=response.json()
    context.user_data['users']=users
    body = ""
    for i in range(len(users)):
        body += (f"id={i+1}\n"
         f"{users[i]['first_name']}\n"
         f"{users[i]['last_name']}\n"
         f"{users[i].get('phone', '')}\n")
    return body

async def handle_btn_clk_assign_task(update:Update,context):
    body = get_users_by_api_to_str(context)
    await update.message.reply_text(body)
    await update.message.reply_text("Выберите пользователя для назначения задачи, указав его id\n"
                                    "Если хотите назначить всем задачу введите команду /all"
                                    )
    return CHOOSING

async def selected_users(update:Update,context):
    target=update.message.text
    if '/all' not in target:
        user_id=int(target)
        target_object=[context.user_data['users'][user_id-1]]
    else:
        target_object=context.user_data['users']
    context.user_data['selected_users']= target_object
    context.user_data['prev_state'] = CHOOSING
    await update.message.reply_text("Укажите задачу в формате [Тело задачи] [приоритет]")
    return ASSIGNTASK    

async def send_task_users(update:Update,context):
    context.user_data['prev_state'] = ASSIGNTASK
    task= update.message.text
    chunks = task.split()
    if not chunks[-1].strip().isdigit():
        return ERROR
    priority = int(chunks[-1].strip())
    body = ' '.join(chunks[:-1])
    
    body_request = {"name":body,"priority":priority,"users":context.user_data['selected_users']}
    response=requests.post("http://127.0.0.1:8000/tasks",json=body_request)
    if response.status_code==200:
        await update.message.reply_text("Задача успешно назначена!")
    else:
        await update.message.reply_text("Задача не назначена, произошла внутренняя ошибка")
    return ConversationHandler.END
    
async def handle_btn_clk_show_user(update:Update,context):
    response = requests.get(f"http://127.0.0.1:8000/users/id{update.message.from_user['id']}")
    await update.message.reply_text(response.text)
    
CHOOSING_USER=0    
async def handle_btn_clk_show_users(update:Update,context):
    body = get_users_by_api_to_str(context)
    keyboard = keyboard_show_users
    reply_markup= ReplyKeyboardMarkup(keyboard,resize_keyboard=True)   
    await update.message.reply_text(body,reply_markup=reply_markup) 

    
async def handle_select_for_del_user(update:Update,context):
    await update.message.reply_text("Выберите id пользователя либо для удаление нескольких пользователей перечилсите их для удаления")
    return CHOOSING_USER

async def handle_btn_del_user(update:Update,context):
    context.user_data['prev_state'] = CHOOSING_USER
    target=update.message.text
    user_id=int(target)
    target_object=context.user_data['users'][user_id-1]
    print(target_object)
    response=requests.delete(f"http://127.0.0.1:8000/users/{target_object['id']}")
    if response.status_code==302:
        await update.message.reply_text('Пользователь успешно удален')
    return ConversationHandler.END

   
async def handle__btn_clk_show_tasks_all(update:Update,context):
    response = requests.get("http://127.0.0.1:8000/tasks")
    tasks=response.json()
    if response.status_code==404:   await update.message.reply_text(tasks['message'])
    else:
        context.user_data['tasks']=tasks
        body = ""
        for i in range(len(tasks)):
            body+=f'id = {i+1} {tasks[i]["name"]} -> {tasks[i]["priority"]} - {tasks[i]["status"]}\n'
        keyboard = keyboard_show_tasks
        reply_markup= ReplyKeyboardMarkup(keyboard,resize_keyboard=True)   
        await update.message.reply_text(body,reply_markup=reply_markup) 
 
CHOOSING_TASK=0
async def handle_select_for_del_task(update:Update,context):
    await update.message.reply_text("Выберите id задачи либо для удаление нескольких задач перечилсите их для удаления")
    return CHOOSING_TASK

async def cancel_del_btn(update:Update,context):
    keyboard = keyboard_admin_base
    reply_markup= ReplyKeyboardMarkup(keyboard,resize_keyboard=True)    
    await update.message.reply_text('Операция отменена!',reply_markup=reply_markup)
    return ConversationHandler.END
    
async def handle_btn_clk_cancel_task(update:Update,context):
    context.user_data['prev_state'] = CHOOSING_TASK
    target=update.message.text
    task_id=int(target)
    target_object=[context.user_data['tasks'][task_id-1]]
    response=requests.delete(f"http://127.0.0.1:8000/tasks/{target_object['id']}")
    if response.status_code==302:
        await update.message.reply_text('Задача успешно удалена')
    return ConversationHandler.END
    
async def handle_btn_clk_show_tasks_by_user(update:Update,context):
    response = requests.get(f"http://127.0.0.1:8000/tasks/user/{update.message.from_user['id']}")
    tasks=response.json()
    if response.status_code==404: await update.message.reply_text(tasks['message'])
    else:
        body=''
        print(tasks)
        for task in tasks:
            body+=f'{task["name"]} -> {task["priority"]} - {task["status"]}\n'
        await update.message.reply_text(body)

async def handle_all_errors(update:Update,context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Произошла ошибка, проверьте формат ввода сообщения")
    return context.user_data['prev_state']

def register(engine:Application):
    engine.add_handler(CommandHandler("start",start))
    engine.add_handler(MessageHandler(filters.Text(['Посмотреть задачи']),handle_btn_clk_show_tasks_by_user))
    engine.add_handler(MessageHandler(filters.Text(['Профиль']),handle_btn_clk_show_user))
    engine.add_handler(MessageHandler(filters.Text(['Отменить удаление']),cancel_del_btn))
    engine.add_handler(MessageHandler(filters.Text(['Показать пользователей']),handle_btn_clk_show_users))
    engine.add_handler(MessageHandler(filters.Text(['Показать задачи']),handle__btn_clk_show_tasks_all))
    
    fsm_asign_task = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Назначить задачу']),handle_btn_clk_assign_task)],
        states={
            CHOOSING:[MessageHandler(filters.TEXT,selected_users)],
            ASSIGNTASK:[MessageHandler(filters.TEXT,send_task_users)]
        },
        fallbacks=[MessageHandler(filters.TEXT,handle_all_errors)]
    )
    
    fsm_del_task = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Удалить задачу']),handle_select_for_del_task)],
        states={
            CHOOSING_TASK:[MessageHandler(filters.TEXT,handle_btn_clk_cancel_task)],
        },
        fallbacks=[]
    )
    
    fsm_del_user = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Удалить пользователя']),handle_select_for_del_user)],
        states={
            CHOOSING_USER:[MessageHandler(filters.TEXT,handle_btn_del_user)],
        },
        fallbacks=[]
    )
    engine.add_handler(fsm_asign_task)
    engine.add_handler(fsm_del_task)
    engine.add_handler(fsm_del_user)