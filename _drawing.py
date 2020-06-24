import PySimpleGUI as sg
bg = 'grey'
pen_color = 'red'
pen_size = 5

graph = sg.Graph(canvas_size=(400, 400), graph_bottom_left=(0,0), graph_top_right=(400, 400), background_color=bg, key='graph', change_submits=True, drag_submits=True)
window = sg.Window('Test', [
    [graph],
    [
    sg.B('',  button_color=('red', 'red'), key='color_red', size=(3,1))
    ,sg.B('', button_color=('green', 'green'), key='color_green', size=(3,1))
    ,sg.B('', button_color=('blue', 'blue'), key='color_blue', size=(3,1))
    ,sg.B('', button_color=('orange', 'orange'), key='color_orange', size=(3,1))
    ,sg.B('', button_color=('brown', 'brown'), key='color_brown', size=(3,1))
    ,sg.B('eraser', button_color=('white', bg), key='color_grey', size=(5,1))
    ,sg.B('X', key='clear', size=(3,1))
    ]
], finalize=True, return_keyboard_events=True)

def check_pen_size():
    if pen_size < 0: pen_size = 1
    if pen_size > 30: pen_size = 30

while True:
    event, values = window(timeout=50)
    if event in ('Exit', None): break

    if '__TIM' not in event:
        print(event, values)
    
    if event in '1 2 3 4 5 6'.split(' '):
        color_id = event
        pen_color = list(enumerate('red green blue orange brown grey'.split()))[int(color_id)-1][1]
        print(f'pen_color = {pen_color}')
        print(f'!!!!!!!!!!!')

    if 'w'==event:
        pen_size -= 3
        check_pen_size()
    if 's'==event:
        pen_size += 3
        check_pen_size()

    if 'F1' in event or '7' in event or 'clear' == event:
        # graph.Erase()
        graph.DrawRectangle((0,0), (400,400), fill_color=bg, line_color=bg)
        graph.Erase()
    if 'graph' == event:
        mouseX, mouseY = values[event]
        circle = graph.DrawCircle((mouseX, mouseY), pen_size, fill_color=pen_color, line_color=pen_color)
    if 'color' in event:
        pen_color = event[6:]
        print(f'pen_color = {pen_color}')

window.close()


