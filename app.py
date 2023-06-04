from flask import Flask, request
from flask_restful import Api
from pyrogram import Client
from pyrogram.raw import functions
import secrets
from tgbot.handlers.tasks import confirmation_user, set_user_task, delete_messages


app = Flask(__name__)
api = Api()



@app.post('/delete')
async def delete():
    data = request.get_json()
    chat_id = data['chat_id']
    messages = data['messages']

    resp = await delete_messages(chat_id=chat_id, message_ids=messages)

    if resp['code']:
        return {
            "Status": "Success",
            "Code": 200,
        }

    else:
        return {
            "Status": "Success",
            "Code": 200,
        }

# Endpoint to confirm that user completed the task/
# If the task is completed successfully, we inform the person about it. If not, we ask them to retry the task.
@app.post('/confirmed')
async def confirmed_user():

    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        text = data.get('text')
        confirmation = data.get('confirmation')

        resp = await confirmation_user(chat_id=chat_id, text=text, confirmation=confirmation)

        if resp['code']:
            return {
                "Status": "Success",
                "Code": 200,
                "BlockedUsers": resp['blocked_users']
            }

        else:
            return {
                "Status": "Error",
                "Code": 400,
                "BlockedUsers": resp['blocked_users']
            }

    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to send user a new task
@app.post('/writeUser')
async def write_user():

    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        text = data.get('text')
        documents = data.get('documents')

        resp = await set_user_task(chat_id=chat_id, text=text, documents=documents)

        if resp['code']:
            return {
                "Status": "Success",
                "Code": 200,
                "BlockedUsers": resp['blocked_users']
            }
        else:
            return {
                "Status": "Error",
                "Code": 400,
                "Error": resp['error']
            }

    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to authorize a new telegram account
@app.post("/authorize")
async def authorize():
    try:
        data = request.get_json()
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        token = secrets.token_hex(16)
        async with Client(f'{token}', api_id, api_hash) as application:
            await application.send_message('me', "Ваш аккаунт был авторизован")
        return {
            "Status": "Success",
            "Token": token
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to send messages from authorized account
@app.post("/sendMessage")
async def send_message():
    try:
        data = request.get_json()
        auth_token = request.headers.get('Authorization')
        user = data.get('user')
        message = data.get('message')
        btn = data.get('btn')
        link = data.get('link')
        async with Client(f"{auth_token}") as application:
            await application.send_message(user, f'{message}\n{btn}: {link}')
        return {
            "Status": "Success",
            "Code": 200
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to create groups from authorized account
@app.post("/createGroup")
async def create_group():
    try:
        data = request.get_json()
        auth_token = request.headers.get('Authorization')
        group_name = data.get('group_name')
        users = data.get('users')
        message = data.get('message')
        async with Client(f"{auth_token}") as application:
            group = await application.create_group(group_name, users)
            await application.send_message(group.id, f'{message}')
            supergroup = await application.invoke(functions.messages.MigrateChat(chat_id=abs(group.id)))
        return {
            "Status": "Success",
            "Code": 200,
            "Group_id": supergroup.updates[0].channel_id
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to delete group created earlier
@app.post("/deleteGroup")
async def delete_group():
    try:
        data = request.get_json()
        auth_token = request.headers.get('Authorization')
        group_id = data.get('group_id')
        group_id = int('-100' + str(group_id))
        async with Client(f'{auth_token}') as application:
            await application.delete_supergroup(group_id)
        return {
            "Status": "Success",
            "Code": 200,
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Running flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0')