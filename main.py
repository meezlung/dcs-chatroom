import flet as ft

from cs12232lab07lib import authenticate, Session
from cs12232lab07lib.project_types import ChatMessage
from getpass import getpass

import asyncio

async def login() -> Session:
    print('Enter name: ')
    name = input()  # Must have no arguments; Flet issue
    print('Enter password: ')
    password = getpass()  # Must have no arguments; Flet issue

    try:
        session = await authenticate(name, password, 'ws://oj.dcs.upd.edu.ph:7777/ws')
    except ValueError:
        print('Invalid credentials!')
        exit(1)
    else:
        print('Valid Credentials!')

    return session


async def app_main(page: ft.Page):
    session = await login()
    
    # -------------------------------------------- CHAT DISPLAY --------------------------------------------
    live_chats = ft.ListView(spacing=10, 
                     height=450,
                     width=1250,
                     auto_scroll=True
                     )
    
    # load history
    if session.chats:
        for chat in session.chats:
            if not chat.dst: # from public message
                live_chats.controls.append(ft.Text(f'[PubM] {chat.src}: {chat.msg}'))
            
            else: # from direct message
                live_chats.controls.append(ft.Text(f'[DM] {chat.src} -> {chat.dst}: {chat.msg}', color="blue"))

    # load current live messages from the server
    def display_new_incoming_message(chat: ChatMessage):
        nonlocal chat_box, live_chats
        # need to distinguish whether that chat is public message or direct message

        if not chat.dst: # from a public message
            live_chats.controls.append(ft.Text(f'[PubM] {chat.src}: {chat.msg}'))   

        else: # from a direct message
            if ',' in chat.dst: # if multiple recipients
                recipients = chat.dst.split(', ')

                for user_recipient in recipients:
                    for target_user_recipient in user_recipient:
                        live_chats.controls.append(ft.Text(f'[DM] {chat.src} -> {target_user_recipient}: {chat.msg}', color="blue"))

            else: # if single recipient
                live_chats.controls.append(ft.Text(f'[DM] {chat.src} -> {chat.dst}: {chat.msg}', color="blue"))  

        page.update()

    page.run_task(session.make_task(on_chat_received=display_new_incoming_message))
    # -------------------------------------------- CHAT DISPLAY --------------------------------------------

    # functions
    async def search(_: ft.ControlEvent):
        nonlocal live_chats, session

        if search_text_box.value != '':
            search_term = str(search_text_box.value)

            if search_term and session.chats:
                chat_messages = list(filter(lambda x: (search_term in x.src) or (search_term in x.msg), session.chats))

                page.remove(live_chats)

                live_chats = ft.ListView(spacing=10, 
                                    height=450,
                                    width=1250,
                                    auto_scroll=True
                                    )
                
                for message in chat_messages:
                    print(message)
                    if message.dst: # direct
                        live_chats.controls.append(ft.Text(f'[DM] {message.src} -> {message.dst}: {message.msg}', color="blue"))
                    else: # public
                        live_chats.controls.append(ft.Text(f'[PubM] {message.src}: {message.msg}'))

                page.insert(2, live_chats)

        else:
            page.remove(live_chats)

            live_chats = ft.ListView(spacing=10, 
                                height=450,
                                width=1250,
                                auto_scroll=True
                                )
            
            page.insert(2, live_chats)

            if session.chats:
                for message in session.chats:
                    if message.dst:
                        live_chats.controls.append(ft.Text(f'[DM] {message.src} -> {message.dst}: {message.msg}', color="blue"))
                    else:
                        live_chats.controls.append(ft.Text(f'[PubM] {message.src}: {message.msg}'))

        page.update()


    async def send_message(_: ft.ControlEvent):
        nonlocal chat_box, live_chats, dm_check
        my_username = 'gabriel'

        if not dm_check.value: # to public message
            session.send_group_chat_message(chat_box.value)
            chat_box.value = ""
        
        else: # to direct message
            if dm_txt_box.value:
                if ',' in dm_txt_box.value: # if multiple recipients
                    recipients = [dm_txt_box.value.split(', ')] # TODO: authenticate this
                    dm_txt_box.value = ''

                    for user_recipient in recipients:
                        for target_user_recipient in user_recipient:

                            # actual sending
                            session.send_direct_message(chat_box.value, target_user_recipient) 

                            # display for flet
                            live_chats.controls.append(ft.Text(f'[DM] {my_username} -> {target_user_recipient}: {chat_box.value}', color="blue")) # Format: [TODO: add my username here], Recipient, Message 


                else: # if single recipient
                    single_recipient = dm_txt_box.value # TODO: authenticate this
                    dm_txt_box.value = ''

                    # actual sending
                    session.send_direct_message(chat_box.value, single_recipient)

                    # display for flet
                    live_chats.controls.append(ft.Text(f'[DM] {my_username} -> {single_recipient}: {chat_box.value}', color="blue")) # Format: [TODO: add my username here], Recipient, Message

        page.update()


    # ui
    chat_box = ft.TextField(value=None, hint_text="Insert Message here")
    btn_send = ft.OutlinedButton(text="Send", on_click=send_message)

    dm_check = ft.Switch(label="DM?", value=False)
    dm_txt_box = ft.TextField(value=None, hint_text="Recipient(s)")

    search_btn = ft.OutlinedButton(text="Search", on_click=search)
    search_text_box = ft.TextField(value=None, hint_text="Insert Username/Message here")
    
    page.add(ft.Row(controls=[chat_box, search_btn, search_text_box]))
    page.add(ft.Row(controls=[btn_send]))
    page.add(live_chats)
    page.add(ft.Row(controls=[dm_check, dm_txt_box]))



def main():
    ft.app(app_main)


if __name__ == '__main__':
    main()