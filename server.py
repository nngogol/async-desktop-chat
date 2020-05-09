#!/usr/bin/python3

'''
	made at 2020-05-08 19:25:54

	✔ list of people, that is connected to server
	✔ list of public messages a.k.a. board

	✔ send a PM to some user, connected to a server

	WHEN:
		✔ a new user connects       - it appers in a user lists
		✔ a new messages is written - it appers in a board

	features: [synchronization state across client]
'''

import asyncio, json, logging, websockets, time
from collections import namedtuple
import uuid

PORT = 8050


#  ___  ___ _ ____   _____ _ __ 
# / __|/ _ \ '__\ \ / / _ \ '__|
# \__ \  __/ |   \ V /  __/ |   
# |___/\___|_|    \_/ \___|_|   

User = namedtuple('User', 'code ws uuid'.split(' '))
Message = namedtuple('Message', 'time author_code text'.split(' '))
STATE,USERS = {"messages_board": []}, set()

def state_event():
	global STATE
	if not STATE['messages_board']:
		return
	return json.dumps({"type": "new_public_messages", 'messages_board' : STATE['messages_board']})

def get_available_name():
	global USERS
	names = [i.code for i in USERS]
	i=1
	myname = str(len(USERS) + i)
	while True:
		if myname not in names:
			break
		i+=1
		myname = str(len(USERS) + i)
	return myname

async def notify_state(skip_user_code=None):
	global USERS, STATE

	if USERS:  # asyncio.wait doesn't accept an empty list
		message = state_event()
		if message:
			# filtered_users = USERS # filter_users
			# if skip_user_code:
			#     filtered_users = [i for i in USERS if i.code != skip_user_code]

			await asyncio.wait([user.ws.send(message) for user in USERS])
		
			return
		print('no messages to sent')

	else:
		USERS = set()
		STATE['messages_board'] = []

async def notify_users(skip_user=None):
	global USERS
	def format_users():
		return [user.code for user in USERS]
	
	if USERS:  # asyncio.wait doesn't accept an empty list
		message = json.dumps({'type': 'new_user_state', "users": format_users()})
		filtered_users = USERS - set(skip_user) if skip_user else USERS
		if not filtered_users:
			return
		await asyncio.wait([user.ws.send(message) for user in filtered_users])

async def register(user):
	global USERS
	USERS.add(user)
	await notify_users(skip_user=user)

async def unregister(user):
	global USERS
	if len(USERS) == 0:
		pass
	elif len(USERS) == 1 and list(USERS)[0] == user:
		USERS = set()
		STATE['messages_board'] = []
	else:
		list_of_users = list(USERS)
		for auser in list_of_users: # set([i for id_, websocket in USERS if id_ == code]):
			if auser.code == user.code:
				USERS.remove(user)
				break
		await notify_users()

	# await notify_state()
	print(f'No users left.' if not USERS else f'# {len(USERS)} users online: ' + ', '.join([user.code for i in USERS]))

async def on_connected_user(websocket, path):
	# register(websocket) sends user_event() to websocket

	# add user to a list
	curr_user = User(get_available_name(), websocket, str(uuid.uuid4()))
	await websocket.send(json.dumps({'type' : 'get-your-code-name', 'code' : curr_user.code}))
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
				break

			elif data["action"] == "change-my-name":
				new_name = data["new_name"]

				# if there are user with name like our user wants:
				# -(stratergy)->  modify name a little bit
				# -(stratergy)-> ✔say no (all users must have uniq name)
				# -(stratergy)->  say yes (all users are identified by uuid on a server)
				filtered_users = [user for user in USERS if user.code == new_name]
				if filtered_users:
					await curr_user.ws.send(json.dumps({'type': 'change-my-name', 'status': 'no', 'message': 'name is taken'}))
					continue


				# if name is free:
				# new set name
				# notify other usersnew set name

				old_uuid = curr_user.uuid
				USERS.remove(curr_user)
				curr_user = User(new_name, websocket, old_uuid)
				USERS.add(curr_user)
				await curr_user.ws.send( json.dumps({'type': 'change-my-name', 'status': 'ok', 'new_name': new_name}) )
				await notify_users(skip_user=curr_user)


			elif data["action"] == "for-server":
				# This is "user to server" message
				print(f'data for server FROM user {curr_user.code}', data['text'])

			elif data["action"] == "post-public-message":
				# This is "user to users" message
				m = Message(time=time.time(), author_code=curr_user.code, text=data["text"])
				STATE["messages_board"].append(m)
				await notify_state()
				# await notify_state(skip_user_code=curr_user)

			elif data["action"] == "send-a-pm":
				# This is "user to user" message
				# Don't record messages in servers logs

				target_code = data["which_user_code"]
				message_eater = [user for user in USERS if user.code == target_code][0]
				print(f'message_eater = {message_eater}')
				await message_eater.ws.send(json.dumps({'type': 'pm_message',
									'text': data["text"],
									'author': curr_user.code}))

			else:
				print("unsupported event: {}", data)
		print(f'Connection with user {curr_user.code} is done.')
	except Exception as e:
		print(f'Error with user {curr_user.code} >', e)

	print(f'Unregistering user {curr_user.code}')
	await unregister(curr_user)

start_server = websockets.serve(on_connected_user, "localhost", PORT)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()