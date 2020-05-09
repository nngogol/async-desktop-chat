#!/usr/bin/python3

import asyncio, json, websockets, datetime, time, sys

PORT = 8050

#       _ _            _   
#      | (_)          | |  
#   ___| |_  ___ _ __ | |_ 
#  / __| | |/ _ \ '_ \| __|
# | (__| | |  __/ | | | |_ 
#  \___|_|_|\___|_| |_|\__|

import PySimpleGUI as sg

p, q, websock = asyncio.Queue(), asyncio.Queue(), None

async def gui():

	global p,q, websock

	###############################################################################################
	#         _       __ _                                  _   _                         _       #
	#        | |     / _(_)                                (_) | |                       | |      #
	#      __| | ___| |_ _ _ __   ___    __ _    __ _ _   _ _  | | __ _ _   _  ___  _   _| |_     #
	#     / _` |/ _ \  _| | '_ \ / _ \  / _` |  / _` | | | | | | |/ _` | | | |/ _ \| | | | __|    #
	#    | (_| |  __/ | | | | | |  __/ | (_| | | (_| | |_| | | | | (_| | |_| | (_) | |_| | |_     #
	#     \__,_|\___|_| |_|_| |_|\___|  \__,_|  \__, |\__,_|_| |_|\__,_|\__, |\___/ \__,_|\__|    #
	#                                            __/ |                   __/ |                    #
	#                                           |___/                   |___/                     #
	###############################################################################################
	users         = sg.Listbox([], size=(30-5, 16), key='users')
	message_board = sg.ML(         size=(50-5, 15), key='messages_board')
	pm_board      = sg.ML(         size=(30-5, 16), key='pm_board')
	good_font = ("Helvetica", 12) # good_font2 = ("Helvetica", 12, "bold")
	T_css = dict(font=good_font)

	users_column = sg.Col([[sg.T('Users', **T_css)], [users]])
	message_board_column = sg.Col([
			[sg.T('Message board', **T_css)], [message_board]
		   ,[sg.T('Message', size=(15,1)), sg.I(key='message', size=(15, 1)),
			 sg.B('send-message'), sg.B('send-a-pm')]
	])
	pm_column = sg.Col([[sg.T('PM messages', **T_css)], [pm_board] ])

	layout = [
		[sg.T('Your name'), sg.Input(**T_css, disabled=True, use_readonly_for_disable=True, size=(30, 1), key='my_name'), sg.B('Change my name...', key='change-my-name')],
		[users_column, message_board_column, pm_column]
	]

	###############################
	#     _                       #
	#    | |                      #
	#    | | ___   ___  _ __      #
	#    | |/ _ \ / _ \| '_ \     #
	#    | | (_) | (_) | |_) |    #
	#    |_|\___/ \___/| .__/     #
	#                  | |        #
	#                  |_|        #
	###############################
	window = sg.Window('Chat', layout, finalize=True)

	enable_print = not False
	def my_print(*args):
		if enable_print:
			print(*args)

	while True:
		event, values = window(timeout=5)
		await asyncio.sleep(0.00001)
		if event in ('Exit', None): break

		if '__TIMEOUT__' != event: my_print(event)#, values)

		try:
			#=============
			# read a queue
			#=============
			if not q.empty():
				while not q.empty():
					item = await q.get()
					my_print(f'PSG >item = {item}...')
					my_print(f'values = {values}...')
		
					if not item or item is None:
						my_print('WHAAAAAAAAAAAAT?', item)
						break
					if item['type'] == 'get-your-code-name':
						my_name = item['code']
						window['my_name'](my_name)
						q.task_done(); my_print('Task done -=-=-')
					if item['type'] == 'new_public_messages':
						my_print('\n'*3)
						if item['messages_board']:
							mess = sorted(item['messages_board'], key=lambda x: x[0])
							messages = [ '{}: {}'.format(m[1], m[2]) for m in mess]
							# update board
							message_board.update('\n'.join(messages))
							q.task_done(); my_print('Task done -=-=-')
					elif item['type'] == 'new_user_state':
						my_print('\n'*3)
						my_code_val = values['my_name']
						new_users = [user_code
									 for user_code in item['users']
									 if user_code != my_code_val]
						users.update(values = new_users)
						q.task_done(); my_print('Task done -=-=-')
					elif item['type'] == 'pm_message':
						today = datetime.datetime.now().strftime('%m-%d %H:%M:%S')
						params = today, item['author'], item['text']
						pm_board.print("{}  {: <30} : {}".format(*params))
						my_print(112222222)
						q.task_done(); my_print('Task done -=-=-')
					elif item['type'] == 'change-my-name':
						if item['status'] == 'ok': window['my_name'](item['new_name'])
						elif item['status'] == 'no': sg.Popup(item['message'])
						q.task_done(); my_print('Task done -=-=-')
					elif item['type'] == 'exit':
						q.task_done(); my_print('Task done exit -=-=-')
						break

				my_print(f'exit psg while loop')

		except Exception as e:
			my_print(e)
			my_print('-'*30)

	
		if event == 'for-server':
			message = json.dumps({'action': 'for-server', "text": 'hello world!'})
			my_print('>>> '+message)
			await p.put(message)
		
		if event == 'change-my-name':
			new_name = sg.PopupGetText('New Name')
			if new_name:
				await websock.send(json.dumps({'action': 'change-my-name', "new_name": new_name}))

		if event == 'send-message':
			my_print("let's send public")
			# message = json.dumps({'type': 'send', "action": USERS})
			text = values['message']
			message = json.dumps({'action': 'post-public-message', "text": text})
			my_print('>>> '+message)
			await websock.send(message)
			window['message']('')
			my_print('public sented')
			# await p.put(message)
		
		if event == 'send-a-pm':
			if not values['users']:
				window['message'].update('Please, select the user first.')
				continue
			if not values['message'].strip():
				window['message'].update('Please, type a non-empty message.')
				continue
			
			my_print("let's send pm")
			
			text = values['message']
			which_user_code = values['users'][0]

			message = json.dumps({
				'action': 'send-a-pm',
				"which_user_code": which_user_code,
				'text': text})

			my_print('>>> '+message)
			await websock.send(message)

			my_print('pm sented')
			pm_board.print("{}  {: <30} : {}".format(
				datetime.datetime.now().strftime('%m-%d %H:%M:%S'),
				'to:' + which_user_code, text))
			window['message']('')

	#       _                
	#      | |               
	#   ___| | ___  ___  ___ 
	#  / __| |/ _ \/ __|/ _ \
	# | (__| | (_) \__ \  __/
	#  \___|_|\___/|___/\___|

	window.close() # close pysimplegui window

	if websock and not websock.closed:
		await websock.send(json.dumps({'action': 'exit'})) # disconnect me

async def bg():
	global PORT
	global p,q, websock
	try:
		a_ws = await websockets.connect(f"ws://localhost:{PORT}")
		websock = a_ws
		await a_ws.send(json.dumps({'action': 'post-public-message', "text": 'hello'}))
		working_status = True
		while working_status and not a_ws.closed:
			# get a message from server
			
			result = await a_ws.recv() # print('reading socket...')
			obj = json.loads(result)
			print('<<< incoming type <<< '+obj['type'])

			# CLOSE CONNECTION if I need
			if not result or obj['type'] == 'exit':
				break

			# give it to pysimplegui loop
			await q.put(obj)
			await asyncio.sleep(0.00001)
		await a_ws.close()
	except Exception as e:
		print('STOPPED reading from websocket -> Exception: ', e)

# start
async def client():
	await asyncio.wait([bg(), gui()])
	
if __name__ == '__main__':
	print('starting the client///')
	loop = asyncio.get_event_loop()
	loop.run_until_complete(client())
	loop.close()
	print('/// stopping all')
