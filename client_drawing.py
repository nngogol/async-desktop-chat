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
    Created     : 2020-06-08 16:25:51
    Origin      : https://github.com/nngogol/async-desktop-chat
    pip install : pip install pysimplegui websockets

'''

import asyncio, json, websockets, datetime, time, sys, uuid
from collections import namedtuple
from general_variables import PORT
import PySimpleGUI as sg

global_message_queue = asyncio.Queue()
global_websock = None
GLOBAL_my_name = ''

def today_date(): return datetime.datetime.now().strftime('%m-%d %H:%M:%S')
enable_print = True
def my_print(*args):
    if enable_print:
        print(*args)


def ui():
    '''

        return a PySimpleGUI layout

    '''
    global GLOBAL_my_name

    T_css = dict(font=("Helvetica", 12))

    users         = sg.Listbox([], size=(30-5, 16), enable_events=True, key='users')
    message_board = sg.ML(         size=(50-5, 15), key='messages_board')
    pm_board      = sg.ML(         size=(30-5, 16), key='pm_board')

    users_column = sg.Col([ [sg.T('Users:', **T_css)], [users]])
    message_board_column = sg.Col([
            [sg.T('Message board', **T_css)], [message_board]
           ,[sg.I(key='message', size=(15, 1)),
               sg.B('▲ Public', key='public-msg'), sg.B('▲ User', disabled=True, key='private-msg'),
               sg.B('View cam', key='view_webcam_btn_tab1'),
            ]
    ])
    pm_column = sg.Col([[sg.T('PM messages', **T_css)], [pm_board] ])

    main_tab = [
        [sg.T('Your name'), sg.Input(GLOBAL_my_name, **T_css, disabled=True, use_readonly_for_disable=True, size=(30, 1), key='my_name'), sg.B('Change my name...', key='change-my-name')],
        [users_column, message_board_column, pm_column]
    ]
    

    graph_metadata= dict(
         bg='grey'
        ,pen_color='red'
        ,pen_size=5
    )
    drawing_tab = [[]]
    #     [
    #     sg.Graph(key='graph',
    #             canvas_size=(400,400), graph_bottom_left=(0,0), graph_top_right=(400,400),
    #             background_color=graph_metadata['bg'],
    #             #change_submits=True, drag_submits=True
    #             metadata=graph_metadata
    #             )
    #     ]
    # ]


    NUM_LINES = 48
    font_size=6
    ml_params = dict(
            size=(115,NUM_LINES), font=('Courier', font_size), pad=(0,0), background_color='black', text_color='white'
        )
    webcam_tab = [
        [sg.ML(**ml_params, key='-client-ascii-image-'), sg.ML(**ml_params, key='-my-ascii-image-')],

        [
            sg.B('X toggle camera',    key='send_webcam_btn'),
            sg.B('X see picked friend',      key='view_webcam_btn'),
        ]
    ]
    
    return [[sg.TabGroup([[sg.Tab(title, tab_ui, key=f'tab_{title}') for title, tab_ui in zip('chat webcam'.split(' '), [main_tab, webcam_tab])]], key='tabs') ] ]
    # return [[sg.TabGroup([[sg.Tab(title, tab_ui) for title, tab_ui in zip('chat canvas webcam'.split(' '), [main_tab, drawing_tab, webcam_tab])]])] ]


from PIL import Image
import numpy as np, cv2

async def gui_application():
    global global_message_queue, global_websock
    global GLOBAL_my_name
    while not GLOBAL_my_name:
        await asyncio.sleep(0.1)
        break
    
        
    try:
        window = sg.Window('Chat', ui(), finalize=True)
    except Exception as e:
        print('\n'*5)
        print(e)
        print('\n'*5)
    


    # webcam
    cap = cv2.VideoCapture(0); cap.set(3, 640); cap.set(4, 360)
    is_viewing_ascii_frame = False
    is_viewing_ascii_frame_user = None
    is_sending_webcam = False
    # ascii conversion
    chars = np.asarray(list(' .,:;irsXA253hMHGS#9B&@'))
    SC, GCF, WCF = .1, 2, 7/4
    def toggle_view_user_webcam_ui(state, user=None):
        # state can be:
        # - bool
        # - str: 'inverse'
        nonlocal is_viewing_ascii_frame, is_viewing_ascii_frame_user, window
        if type(state) is str:    is_viewing_ascii_frame = not is_viewing_ascii_frame
        elif type(state) is bool: is_viewing_ascii_frame = state
        else:
            raise TypeError

        is_viewing_ascii_frame_user = user

        # update gui
        btn_color = ('white', 'red') if is_viewing_ascii_frame else sg.DEFAULT_BUTTON_COLOR
        btn_char = '√' if is_viewing_ascii_frame else 'X'
        toggle_btn_key = 'view_webcam_btn'
        window[toggle_btn_key](btn_char + window[toggle_btn_key].GetText()[2:], button_color=btn_color)

    def toggle_send_webcam_ui(state):
        # state can be:
        # - bool
        # - str: 'inverse'
        nonlocal is_sending_webcam, window
        if type(state) is str:    is_sending_webcam = not is_sending_webcam
        elif type(state) is bool: is_sending_webcam = state
        else:
            raise TypeError

        # update gui
        btn_color = ('white', 'red') if is_sending_webcam else sg.DEFAULT_BUTTON_COLOR
        btn_char = '√' if is_sending_webcam else 'X'
        toggle_btn_key = 'send_webcam_btn'
        window[toggle_btn_key](btn_char + window[toggle_btn_key].GetText()[2:], button_color=btn_color)
        

    def img2ascii(frame):

        try:
            img = Image.fromarray(frame)  # create PIL image from frame
            SC = .1
            GCF = 1.
            WCF = 7/4

            # More magic that coverts the image to ascii
            S = (round(img.size[0] * SC * WCF), round(img.size[1] * SC))
            img = np.sum(np.asarray(img.resize(S)), axis=2)
            img -= img.min()
            img = np.array((1.0 - img / img.max()) ** GCF * (chars.size - 1), dtype=np.uint8)

            # "Draw" the image in the window, one line of text at a time!
            str_img = '\n'.join(["".join(r) for r in chars[img.astype(int)]])
            return str_img
        except Exception as e:
            return False


    while True:
        event, values = window(timeout=5)
        await asyncio.sleep(0.001)
        if event in ('Exit', None): break
        if '__TIMEOUT__' != event: my_print(event)#, values)         # print event name

        
        #=============
        # read a queue
        #=============
        try:
            if not global_message_queue.empty():
                while not global_message_queue.empty():
                    item = await global_message_queue.get()

                    my_print(f'Handle message ▼▼▼')
        
                    if not item or item is None:
                        my_print('Bad queue item', item)
                        break
                    
                    elif item['type'] == 'view_ascii_frame':
                        status = item['status']
                        if status == 'ok':
                            try:
                                window['-client-ascii-image-'](item['ascii_img'])
                            except Exception as e:
                                print('\n'*5)
                                print(e)
                                print('\n'*5)
                                import pdb; pdb.set_trace();
                                
                        else:
                            toggle_view_user_webcam_ui(False)

                        global_message_queue.task_done(); my_print('Task done -=-=- (view_ascii_frame)')

                    elif item['type'] == 'get-your-name':
                        my_name = item['name']
                        window['my_name'](my_name)
                        values['my_name'] = my_name
                        my_print(f'❄❄❄ my will be {my_name}')
                        global_message_queue.task_done(); my_print('Task done -=-=- (get-your-name)')

                    elif item['type'] == 'new_public_messages':
                        if item['messages_board']:
                            my_print('❄❄❄ new_public_messages')
    
                            mess = sorted(item['messages_board'], key=lambda x: x[0])
                            messages = '\n'.join(    [ '{}: {}'.format(m[1], m[2]) for m in mess]    )
    
                            # update board
                            window['messages_board'].update(messages)
                            global_message_queue.task_done(); my_print('Task done -=-=- (new_public_messages)')

                    elif item['type'] == 'new_user_state':
                        my_print('\n', '❄❄❄ new_user_state')
                        
                        my_name_val = values['my_name']
                        users_ = item['users']
                        filtered_users = [user_name for user_name in item['users'] if user_name != my_name_val]


                        if is_viewing_ascii_frame_user not in filtered_users:
                            toggle_view_user_webcam_ui(False)
                        window['users'].update(values=filtered_users)
                        
                        my_print('''my_name:   {}\nall_users: {}\nfiltered: {}\n'''.format(my_name_val, ','.join(users_), ','.join(filtered_users)))
                        global_message_queue.task_done(); my_print('Task done -=-=- (new_user_state)')

                    elif item['type'] == 'pm_message':
                        my_print('\n', '❄❄❄ pm_message')
                        
                        params = today_date(), item['author'], item['text']
                        window['pm_board'].print("{}  {: <30} : {}".format(*params))
                        global_message_queue.task_done(); my_print('Task done -=-=- (pm_message)')

                    elif item['type'] == 'change-my-name':
                        if item['status'] == 'ok':
                            new_name = item['new_name']
                            window['my_name'](new_name)
                            my_print('\n', '❄❄❄ change-my-name', f'\nnew name will be: {new_name}')

                        elif item['status'] == 'no':
                            sg.Popup(item['message'])

                        global_message_queue.task_done(); my_print('Task done -=-=- (change-my-name)')

                    elif item['type'] == 'exit':
                        my_print('\n', '❄❄❄ exit')
                        global_message_queue.task_done(); my_print('Task done exit -=-=- (exit)')
                        break
                    my_print(f'▲▲▲')

        except Exception as e: my_print(e, '-'*30)

        if values['users']:
            window['private-msg'](disabled=False)


        #               _
        #              | |
        # __      _____| |__   ___ __ _ _ __ ___
        # \ \ /\ / / _ \ '_ \ / __/ _` | '_ ` _ \
        #  \ V  V /  __/ |_) | (_| (_| | | | | | |
        #   \_/\_/ \___|_.__/ \___\__,_|_| |_| |_|
        if is_viewing_ascii_frame:
            if global_websock.state.value != 1:
                continue
            await global_websock.send(json.dumps({'action': 'view_ascii_frame', "which_user_name": is_viewing_ascii_frame_user}))
        if event == 'view_webcam_btn':
            # No user selected.
            if not values['users']:
                sg.popup('Select user first!')
                continue
            # change state
            which_user_name = values['users'][0]
            toggle_view_user_webcam_ui('inv', which_user_name)


        if is_sending_webcam:
            
            # 1. send image to server
            # 2. plot image in my gui
            
            ret, img = cap.read()

            if not ret: continue


            ret, frame = cap.read()
            ascii_image = img2ascii(frame)
            if not ascii_image: continue
            # 
            # step 1
            # 
            window['-my-ascii-image-'](ascii_image)
            # 
            # step 2
            # 
            if global_websock.state.value == 1: # OPEN
                await global_websock.send(json.dumps({
                    'action': 'update_my_ascii_frame',
                    "ascii_img": ascii_image}))


        if event == 'send_webcam_btn':
            toggle_send_webcam_ui('inv')
            if not is_sending_webcam:
                await global_websock.send(json.dumps({'action': 'close_my_ascii_frame'}))

        # ==========
        if event == 'view_webcam_btn_tab1':
            # view_webcam_btn_tab1
            if not values['users']:
                sg.popup('Select user first!')
                continue

            which_user_name = values['users'][0]
            window['tab_webcam'].Select()


        # ==========

        if event == 'change-my-name':
            new_name = sg.PopupGetText('New Name')
            if new_name:
                await global_websock.send(json.dumps({'action': 'change-my-name', "new_name": new_name}))

        if event == 'public-msg':
            message = json.dumps({'action': 'post-public-message', "text": values['message']})

            my_print(f"let's send public\nI will send: {message}")
            await global_websock.send(message)

            # clear GUI text element
            window['message']('')
        
        if event == 'private-msg':
        
            # validate
            if not values['users']:
                window['message'].update('Please, select the user first.')
                continue
        
            if not values['message'].strip():
                window['message'].update('Please, type a non-empty message.')
                continue
            
            my_print("Let's send pm")
            text = values['message']
            which_user_name = values['users'][0]
            message = json.dumps({
                'action': 'send-a-pm',
                "which_user_name": which_user_name,
                'text': text})

            my_print(f'I will send: {message}')
            await global_websock.send(message)

            # clear GUI text element
            window['pm_board'].print("{}  {: <30} : {}".format(today_date(), 'to:' + which_user_name, text))
            window['message']('')

    #
    # CLOSE
    #
    # -> psg close
    window.close()

    # -> websocket close
    if global_websock and not global_websock.closed:
        await global_websock.send(json.dumps({'action': 'exit'})) # disconnect me

async def websocket_reading():
    global PORT, global_message_queue, global_websock, GLOBAL_my_name
    try:
        # connect to a server
        a_ws = await websockets.connect(f"ws://localhost:{PORT}")
        global_websock = a_ws
        GLOBAL_my_name = json.loads(await a_ws.recv())['name']
        # # send "hello world" message
        # await a_ws.send(json.dumps({'action': 'post-public-message', "text": 'hello'}))
        

        # read messages, till you catch STOP message
        async for result in a_ws:
            json_msg = json.loads(result)

            # exit
            if json_msg['type'] == 'exit':
                break

            # put in global message queue
            await global_message_queue.put(json_msg)
    
        # close socket
        try: await a_ws.close()
        except Exception as e: print('Exception. cant close ws:', e)


    except Exception as e:
        print('Exception. ws died: ', e)

async def client():
    await asyncio.wait([websocket_reading(), gui_application()])

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client())
    loop.close()

if __name__ == '__main__':
    print('started')
    main()
    print('ended')
