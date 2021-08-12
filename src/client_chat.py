import curses
import math
import time
class User:
    name = "a"
    chatting_history = [] # tuple ("0" or "1" , i, "message") "0": other_side's messege, "1": user_side's messege, i : i_th msg
    def __init__(self, _name, _chat_h):
        self.name = _name
        self.chatting_history = _chat_h

    

class Chat_Window:
    def __init__(self, chatP_list, window, my_name):
        self.__window = window
        self.__my_name = my_name
        self.__height, self.__width = window.getmaxyx()
        self.__chatP_list_win = self.__window.subwin(self.__height - 10 , self.__width, 8, 0)
        self.__chat_page_win = self.__window.subwin(self.__height - 10 , self.__width, 8, 0)
        self.__system_msg_win = self.__window.subwin(2 , self.__width, 0, 0)
        self.__readme_win = self.__window.subwin(5, self.__width, 2, 0)
        self.__chatP_list = chatP_list #chatting person
        self.__state = 0 # 0 for main page, 1 for chatting page
        self.__now_chatP = User(" null",  [])
        self.__now_chatP_msg_start = -1
        self.__now_chatP_msg_end = -1
        self.__chatP_display_num = (self.__height - 12) // 3
        self.__chatP_display_start = 0

        if( len(chatP_list) > self.__chatP_display_num ):         
            self.__chatP_display_end = self.__chatP_display_num - 1
        else:
            self.__chatP_display_end = len(chatP_list) - 1
        window.clear()
        window.addstr("\n" * 2)
        window.addstr("hi: " + self.__my_name+ "\n")
        window.addstr("enter \"c:[username]\" to chat with someone\n")
        window.addstr("enter \"n\" to turn to the next page of user\n")
        window.addstr("enter \"p\" to turn to the previous page of user\n")
        window.addstr("enter \"quit\" to quit")
        window.move(self.__height-1, 0)

    def chatP_list_next_page(self):
        if(self.__chatP_display_start + self.__chatP_display_num >= len(self.__chatP_list)):
            return
        self.__chatP_display_start = self.__chatP_display_start + self.__chatP_display_num
        if(self.__chatP_display_end + self.__chatP_display_num >= len(self.__chatP_list)):
            self.__chatP_display_end = len(self.__chatP_list) - 1
        else:
            self.__chatP_display_end = self.__chatP_display_end + self.__chatP_display_num
    
    def chatP_list_previous_page(self):
        if(self.__chatP_display_start - self.__chatP_display_num < 0):
            return
        self.__chatP_display_start = self.__chatP_display_start - self.__chatP_display_num
        if( len(self.__chatP_list) > self.__chatP_display_start + self.__chatP_display_num ):         
            self.__chatP_display_end = self.__chatP_display_start + self.__chatP_display_num - 1
        else:
            self.__chatP_display_end = len(self.__chatP_list) - 1

    def readme_show(self):
        window = self.__readme_win
        window.clear()
        if(self.__state == 0):
            window.addstr("hi: " + self.__my_name + "\n")
            window.addstr("enter \"c:[username]\" to chat with someone\n")
            window.addstr("enter \"n\" to turn to the next page of user\n")
            window.addstr("enter \"p\" to turn to the previous page of user\n")
            window.addstr("enter \"quit\" to quit")


        else:
            window.addstr("hi: " + self.__my_name + "\n")
            window.addstr("enter \"up\" or \"down\" to scroll msg\n")
            window.addstr("enter \"send:[msg]\" to send messege\n")
            window.addstr("enter \"file:path1 path2..\" to send file\n")
            window.addstr("enter \"main\" to go back to main page")
        window.refresh()
    
    def system_msg_show(self, msg):
        window = self.__system_msg_win
        window.clear()
        window.addnstr(msg, self.__width * 2)
        window.refresh()
        self.__window.move(self.__height - 1, 0)
        self.__window.refresh()
    
    def chat_page_show(self):
        window = self.__chat_page_win
        chatP = self.__now_chatP
        height, width = window.getmaxyx()
        window.clear()
        window.addstr("now chat: " + chatP.name + "\n")
        line_len = (self.__width // 2) - 1
        line_num = 1
        for i in range(self.__now_chatP_msg_start, len(chatP.chatting_history)):
            now_msg = chatP.chatting_history[i][2]
            if(chatP.chatting_history[i][0] == "0"):
                starting_pt = 0
            else:
                starting_pt = line_len
            if(line_num + math.ceil(len(now_msg)/ line_len) + 1 > height):
                break
            self.__now_chatP_msg_end = i
            while(len(now_msg) > 0):
                window.addnstr(line_num, starting_pt, now_msg, line_len)
                now_msg = now_msg[line_len:]
                line_num = line_num + 1
            line_num = line_num + 1

        window.addstr(height-1, 0, str(self.__now_chatP_msg_start+1) + "~" + str(self.__now_chatP_msg_end+1) + "/" + str(len(chatP.chatting_history)))
        window.refresh()

    def update_now_chatP_msg_end(self):
        window = self.__chat_page_win
        chatP = self.__now_chatP
        height, width = window.getmaxyx()
        line_len = (self.__width // 2) - 1
        line_num = 1
        for i in range(self.__now_chatP_msg_start, len(chatP.chatting_history)):
            now_msg = chatP.chatting_history[i][2]
            if(line_num + math.ceil(len(now_msg)/ line_len) + 1 > height):
                break
            self.__now_chatP_msg_end = i
            line_num = line_num + math.ceil(len(now_msg)/ line_len)+1
        return self.__now_chatP_msg_end

    def chat_page_up(self):
        height, width = self.__chat_page_win.getmaxyx()
        start = self.__now_chatP_msg_start - 1
        chatP = self.__now_chatP
        line_len = (self.__width // 2) - 1
        line_num = 1
        if(start <= 0):
            self.__now_chatP_msg_start = 0
            self.update_now_chatP_msg_end()
            return
        full = 0
        while(start >= 0):
            now_msg = chatP.chatting_history[start][2]
            while(len(now_msg) > 0):
                now_msg = now_msg[line_len:]
                line_num = line_num + 1
            line_num = line_num + 1
            if(line_num > height):
                full = 1
                break
            start = start - 1
        self.__now_chatP_msg_start = start + full    
        if(self.__now_chatP_msg_start <= 0):
            self.__now_chatP_msg_start = 0
        self.update_now_chatP_msg_end()
    
    def chat_page_down(self):
        height, width = self.__chat_page_win.getmaxyx()
        start = self.__now_chatP_msg_start + 1
        chatP = self.__now_chatP
        line_len = (self.__width // 2) - 1
        line_num = 1
        if(start >= len(chatP.chatting_history) - 1):
            self.__now_chatP_msg_start = len(chatP.chatting_history) - 1
            self.update_now_chatP_msg_end()
            return
        full = 0
        while(start < len(chatP.chatting_history)):
            now_msg = chatP.chatting_history[start][2]
            while(len(now_msg) > 0):
                now_msg = now_msg[line_len:]
                line_num = line_num + 1
            line_num = line_num + 1
            if(line_num > height):
                full = 1
                break
            start = start + 1
        self.__now_chatP_msg_start = start - full    
        if(self.__now_chatP_msg_start >= len(chatP.chatting_history) ):
            self.__now_chatP_msg_start = len(chatP.chatting_history) - 1
        self.update_now_chatP_msg_end()
    def update_chatP_display_end(self):
        self.__chatP_display_end = self.__chatP_display_start + self.__chatP_display_num - 1
        if(self.__chatP_display_end >= len(self.__chatP_list)):
            self.__chatP_display_end = len(self.__chatP_list) - 1

    def chatP_list_show(self):
        window = self.__chatP_list_win
        window.clear()
        dstart, dend, dnum = self.__chatP_display_start, self.__chatP_display_end, self.__chatP_display_num
        chatP_list = self.__chatP_list
        for i in range(dstart, dend + 1):
            msg_info = chatP_list[i].name + "\n"
            if(len(chatP_list[i].chatting_history) > 0):                
                now_msg = chatP_list[i].chatting_history[-1][2][0:self.__width//2]
                if(chatP_list[i].chatting_history[-1][0] == "1"):
                    msg_info = msg_info + "you: " + now_msg
                else:
                    msg_info = msg_info + chatP_list[i].name +": " + now_msg
            else:
                msg_info = msg_info + "nothing"
            window.addstr(msg_info + "\n\n")

        window.addstr("\n" * ((dnum - dend + dstart - 1)*3))
        window.addstr("page " + str(dstart // dnum + 1) + "/" + str(math.ceil(len(self.__chatP_list) / dnum)) + "\n")
        window.refresh()

    def chat_with_chatP(self, chatP_name):
        for i in range(len(self.__chatP_list)):
            if(self.__chatP_list[i].name == chatP_name):
                line_len = (self.__width // 2) - 1
                line_num = 1
                height, width = self.__chat_page_win.getmaxyx()
                self.__now_chatP = self.__chatP_list[i]
                chatP = self.__now_chatP
                start = len(chatP.chatting_history) - 1
                if(start <= 0):
                    self.__now_chatP_msg_start = 0
                else:    
                    full = 0
                    while(start >= 0):
                        now_msg = chatP.chatting_history[start][2]
                        line_num = line_num + math.ceil(len(now_msg) / line_len)
                        line_num = line_num + 1
                        if(line_num > height):
                            full = 1
                            break
                        start = start - 1
                    self.__now_chatP_msg_start = start + full
                    if(self.__now_chatP_msg_start < 0):
                        self.__now_chatP_msg_start = 0
                self.update_now_chatP_msg_end()
                self.__state = 1
                self.show()
                return
        new_usr = User(chatP_name, [])
        self.__chatP_list.insert(0, new_usr)
        self.__now_chatP = self.__chatP_list[0]
        self.__state = 1
        self.__now_chatP_msg_start = 0
        self.__now_chatP_msg_end = 0
        self.update_chatP_display_end()
        self.show()
        return


    def update_chatP_msg(self, chatP_name, msg, whose):
        for i in range(len(self.__chatP_list)):
            if(self.__chatP_list[i].name == chatP_name):
                msg_serial = len(self.__chatP_list[i].chatting_history)
                self.__chatP_list[i].chatting_history.append((whose, msg_serial, msg))
                ret = self.__chatP_list[i]
                self.__chatP_list.pop(i)
                self.__chatP_list.insert(0, ret)
                return ret
        #not found, new user
        new_usr = User(chatP_name, [(whose, 0, msg)])
        self.__chatP_list.insert(0, new_usr)
        self.update_chatP_display_end()
        return self.__chatP_list[0]
    
    def recv_chatP_msg(self, chatP_name, msg):
        chatP = self.update_chatP_msg(chatP_name, msg, "0")
        self.system_msg_show("new msg from: " + chatP_name)
        if(self.__state == 1 and self.__now_chatP.name == chatP.name):
            if(self.__now_chatP_msg_end == len(self.__now_chatP.chatting_history) - 2): #display last message
                line_len = (self.__width // 2) - 1
                line_num = 1
                height, width = self.__chat_page_win.getmaxyx()
                start = len(chatP.chatting_history) - 1
                if(start <= 0):
                    self.__now_chatP_msg_start = 0
                else:    
                    full = 0
                    while(start >= 0):
                        now_msg = chatP.chatting_history[start][2]
                        line_num = line_num + math.ceil(len(now_msg) / line_len)
                        line_num = line_num + 1
                        if(line_num > height):
                            full = 1
                            break
                        start = start - 1
                    self.__now_chatP_msg_start = start + full
                    if(self.__now_chatP_msg_start < 0):
                        self.__now_chatP_msg_start = 0
                self.update_now_chatP_msg_end()
                self.__state = 1

            self.show()

        elif(self.__state == 0):
            self.show()
        return chatP
    
    def send_chatP_msg(self, chatP_name, msg):
        chatP = self.update_chatP_msg(chatP_name, msg, "1")
        if(self.__state == 1 and self.__now_chatP.name == chatP.name):
            if(self.__now_chatP_msg_end == len(self.__now_chatP.chatting_history) - 2): #display last message
                line_len = (self.__width // 2) - 1
                line_num = 1
                height, width = self.__chat_page_win.getmaxyx()
                start = len(chatP.chatting_history) - 1
                if(start <= 0):
                    self.__now_chatP_msg_start = 0
                else:    
                    full = 0
                    while(start >= 0):
                        now_msg = chatP.chatting_history[start][2]
                        line_num = line_num + math.ceil(len(now_msg) / line_len)
                        line_num = line_num + 1
                        if(line_num > height):
                            full = 1
                            break
                        start = start - 1
                    self.__now_chatP_msg_start = start + full
                    if(self.__now_chatP_msg_start < 0):
                        self.__now_chatP_msg_start = 0
                self.update_now_chatP_msg_end()

            self.show()


    def show(self):
        if(self.__state == 0):
            self.readme_show()
            self.chatP_list_show()
        elif(self.__state == 1):
            self.readme_show()
            self.chat_page_show()
        self.__window.move(self.__height-1, 0)
        self.__window.refresh()
    
    def get_state(self):
        return self.__state
    
    def set_state(self, i):
        self.__state = i

    def get_chat_name(self):
        return self.__now_chatP.name
