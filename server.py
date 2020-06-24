#!/usr/bin/python3

'''
    Public/Private chat for N users.
    
    Main things are:
    - GET a public board with messages
    - POST messages to this public board
    - GET a public list of currently connected users
    - SENT private messages to selected user
    - CHANGE name

    Author      : nngogol
    Created     : 2020-06-08 16:25:53
    Origin      : https://github.com/nngogol/async-desktop-chat
    pip install : pip install pysimplegui websockets

'''

import asyncio, json, websockets, datetime, time, sys, uuid
from collections import namedtuple
from general_variables import PORT

class User(object):
    def __init__(self, name, ws, uuid):
        self.name = name
        self.ws = ws
        self.uuid = uuid
        self.curr_ascii_img = ''
USERS = set()

Message = namedtuple('Message', 'time author_name text'.split(' '))
STATE = {
    "messages_board": [],
    "video_frames" : {}
}

def mk_uuid4(): return str(uuid.uuid4())

def state_event():
    global STATE
    if not STATE['messages_board']:
        return 
    return json.dumps({"type": "new_public_messages", 'messages_board' : STATE['messages_board']})

def get_available_name():
    global USERS
    names = [user.name for user in USERS]
    
    myname = f'user#{str(len(USERS)+0)}'
    for i in range(10_000_000):
        if myname not in names: break
        myname = f'user#{str(len(USERS)+i)}'
    return myname

async def notify_state():
    global USERS, STATE

    if USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        if message:
            await asyncio.wait([user.ws.send(message) for user in USERS])
            return
        print('no messages to sent')

    else:
        USERS = set()
        STATE['messages_board'] = []

def get_user_names(): return [user.name for user in USERS]

async def notify_users(skip_user=None):
    global USERS
    if not USERS: return 

    users_with_himself = USERS - set([skip_user]) if skip_user else USERS
    
    if len(users_with_himself) != 0: # asyncio.wait doesn't accept an empty list

        message_json = {'type': 'new_user_state', "users": get_user_names() }
        message = json.dumps(message_json)
        print('I will send messages to: ', ','.join(message_json['users']))
        await asyncio.wait([ user.ws.send(message)
                             for user in users_with_himself])

async def notify_users_msg(msg, skip_user=None):
    global USERS
    if not USERS: return 

    users_with_himself = USERS - set([skip_user]) if skip_user else USERS
    
    if len(users_with_himself) != 0: # asyncio.wait doesn't accept an empty list
        message = json.dumps(msg)
        await asyncio.wait([ user.ws.send(message)
                             for user in users_with_himself])

    # for i in USERS:
    #                     await i.ws.send(json.dumps(data))

async def register(user):
    global USERS
    USERS.add(user)
    await notify_users()

async def unregister(user):
    global USERS
    
    if len(USERS) == 1 and list(USERS)[0] == user:
        USERS = set()
        STATE['messages_board'] = []
    if len(USERS) > 1:
        for auser in USERS: # set([i for id_, websocket in USERS if id_ == name]):
            if auser.name == user.name:
                USERS.remove(user)
                await notify_users()
                break

    print(f'No users left.' if not USERS else f'# {len(USERS)} users online: ' + ', '.join(get_user_names()))

async def on_ws_connected(websocket, path):
    # register(websocket) sends user_event() to websocket

    # add user to a list
    curr_user = User(get_available_name(), websocket, mk_uuid4())
    await websocket.send(json.dumps({'type' : 'get-your-name', 'name' : curr_user.name}))
    await register(curr_user)

    try:
        # show public board
        state = state_event()
        if state:
            await websocket.send(state)

        # READ messages from user
        # this for loop is live "infinite while true" loop.
        # It will end, end connection is dropped.

        async for message in websocket:
            data = json.loads(message)

            if data["action"] == "exit":
                # EXITING MESSAGE from user
                await curr_user.ws.send(json.dumps({'type': 'exit'}))
                await websocket.close()
                break

            ##################################################################################
            #                                                      _   _                     #
            #                                                     | | (_)                    #
            #     _   _ ___  ___ _ __    ___  _ __   ___ _ __ __ _| |_ _  ___  _ __  ___     #
            #    | | | / __|/ _ \ '__|  / _ \| '_ \ / _ \ '__/ _` | __| |/ _ \| '_ \/ __|    #
            #    | |_| \__ \  __/ |    | (_) | |_) |  __/ | | (_| | |_| | (_) | | | \__ \    #
            #     \__,_|___/\___|_|     \___/| .__/ \___|_|  \__,_|\__|_|\___/|_| |_|___/    #
            #                                | |                                             #
            #                                |_|                                             #
            ##################################################################################
            elif data["action"] == "change-my-name":
                new_name = data["new_name"]

                # if there are user with name like our user wants:
                # -(stratergy)->  modify name a little bit
                # -(stratergy)-> ✔say no (all users must have uniq name)
                # -(stratergy)->  say yes (all users are identified by uuid on a server)
                filtered_users = [user_name for user_name in get_user_names() if user_name == new_name]
                if filtered_users:
                    await curr_user.ws.send(json.dumps({'type': 'change-my-name', 'status': 'no', 'message': 'name is taken'}))
                    continue

                curr_user.name = new_name
                await curr_user.ws.send( json.dumps({'type': 'change-my-name', 'status': 'ok', 'new_name': new_name}) )
                await notify_users(curr_user)

            ############################################################################
            #     _            _                                                       #
            #    | |          | |                                                      #
            #    | |_ _____  _| |_   _ __ ___   ___  ___ ___  __ _  __ _  ___  ___     #
            #    | __/ _ \ \/ / __| | '_ ` _ \ / _ \/ __/ __|/ _` |/ _` |/ _ \/ __|    #
            #    | ||  __/>  <| |_  | | | | | |  __/\__ \__ \ (_| | (_| |  __/\__ \    #
            #     \__\___/_/\_\\__| |_| |_| |_|\___||___/___/\__,_|\__, |\___||___/    #
            #                                                       __/ |              #
            #                                                      |___/               #
            ############################################################################
            elif data["action"] == "post-public-message":
                # This is "user to users" message
                STATE["messages_board"].append(
                    Message(time=time.time(),
                            author_name=curr_user.name,
                            text=data["text"]) )
                await notify_state()

            elif data["action"] == "send-a-pm":
                # This is "user to user" message
                # Don't record messages in servers logs
                target_user_name = data["which_user_name"]
                message_eater = [user for user in USERS if user.name == target_user_name][0]
                await message_eater.ws.send(json.dumps({'type': 'pm_message',
                                    'text': data["text"],
                                    'author': curr_user.name}))


            #                 _ _   _
            #                (_|_) (_)
            #   __ _ ___  ___ _ _   _ _ __ ___   __ _  __ _  ___
            #  / _` / __|/ __| | | | | '_ ` _ \ / _` |/ _` |/ _ \
            # | (_| \__ \ (__| | | | | | | | | | (_| | (_| |  __/
            #  \__,_|___/\___|_|_| |_|_| |_| |_|\__,_|\__, |\___|
            #                                          __/ |
            #                                         |___/
            # ON
            elif data["action"] == "update_my_ascii_frame": curr_user.curr_ascii_img = data["ascii_img"]
            # OFF
            elif data["action"] == "close_my_ascii_frame":  curr_user.curr_ascii_img = ''
            # SEND
            elif data["action"] == "view_ascii_frame":
                target_user_name = data["which_user_name"]
                message_eater = [user for user in USERS if user.name == target_user_name][0]
                ascii_img = message_eater.curr_ascii_img
                if ascii_img:
                    await curr_user.ws.send(json.dumps({'type': 'view_ascii_frame', 'status' : 'ok', 'ascii_img': ascii_img}))
                else:
                    await curr_user.ws.send(json.dumps({'type': 'view_ascii_frame', 'status' : 'empty'}))
            #   ___ __ _ _ ____   ____ _ ___
            #  / __/ _` | '_ \ \ / / _` / __|
            # | (_| (_| | | | \ V / (_| \__ \
            #  \___\__,_|_| |_|\_/ \__,_|___/

            elif data["action"] == "update_public_canvas":
                data['type'] = data['action']
                
                # forwarding
                await notify_users_msg(data)
                

            else:
                print("unsupported event: {}".format(data))
        print(f'Connection with user {curr_user.name} is done.')
    except Exception as e:
        print(f'Error with user {curr_user.name} >', e)

    print(f'Unregistering user {curr_user.name}')
    await unregister(curr_user)
    print(f'Bye, {curr_user.name}!')

def main():
    global PORT
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(on_ws_connected, "localhost", PORT))
    loop.run_forever()

if __name__ == '__main__':
    print('started')
    main()
    print('ended')