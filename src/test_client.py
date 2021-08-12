#!/usr/bin/env python3
import socket
import os
import threading
import curses
import time
import struct, math
import atexit, sys
from client_chat import User, Chat_Window
from myprotocol import ACTION, encode_method, RESULT, STANDARD

  

def my_raw_input(stdscr, prompt_string):
	stdscr.addstr(prompt_string)
	stdscr.refresh()
	st = stdscr.getstr().decode(encoding="utf-8")
	return st

def length_valid(input_string):
	string_length = len(input_string)
	if(string_length <= 0 or string_length >20):
		return -1
	return 1

	

def sign_in(window, server_fd, my_name_list):
	window.clear()
	username = my_raw_input(window, "Input username, only a~z or 0~9:")
	passwd = my_raw_input(window, "Input passwd:")
	# invalid length of username or passwd => input  again
	if(length_valid(username) == -1 or length_valid(passwd) == -1 or username.isalnum() == False):
		window.addstr("invalid username or passwd\n")
		my_raw_input(window, "enter anthing to continue: ")
		return -1
	
	signin_payload  = ACTION.SIGN_IN() + struct.pack(">I", len(username)).decode(encode_method) + struct.pack(">I", len(passwd)).decode(encode_method) + username + passwd 
	try:
		server_fd.send(signin_payload.encode(encode_method))
		response = server_fd.recv(1).decode(encode_method)
		if(response == RESULT.SUCCESS()):
			window.addstr("sign in successfully.\n")
			my_name_list.append(username)
			window.refresh()
			time.sleep(0.5)
			return server_fd
		else :
			window.clear()
			signin_error_msg_len = int.from_bytes(server_fd.recv(4), "big")
			signin_error_msg = server_fd.recv(signin_error_msg_len).decode(encode_method)
			window.addstr(signin_error_msg + "\n")
			my_raw_input(window, "enter anthing to continue: ")
			return -1

			#else: input username passwd agian

	except Exception as e:
		#when error occur, connecting server again
		window.clear()
		window.addstr(str(e))
		my_raw_input(window, "\nenter anything to continue: ")
		return -1



			
def sign_up(window, server_fd):
	window.clear()
	username = my_raw_input(window, "length<=20, Input username, only a~z or 0~9: ")
	passwd = my_raw_input(window, "length<=20, Input passwd: ")
	#print(username)
	#print(passwd)
	passwd_check = my_raw_input(window, "Input passwd again: ")
	#print(1)
	if(passwd != passwd_check):
		window.addstr("Different password!\n")
		my_raw_input(window, "enter anthing to continue: ")
		return -1
	#print(2)
	# invalid length of username or passwd => input  again
	if(length_valid(username) == -1 or length_valid(passwd) == -1 or username.isalnum() == False):
		window.addstr("invalid length of username or passwd!\n")
		my_raw_input(window, "enter anthing to continue: ")
		return -1
	#print(3)
	signup_payload  = ACTION.SIGN_UP() + struct.pack(">I", len(username)).decode(encode_method) + struct.pack(">I", len(passwd)).decode(encode_method) + username + passwd 
	try:
		window.refresh()
		server_fd.send(signup_payload.encode(encode_method))
		window.refresh()

		response = server_fd.recv(1).decode(encode_method)
		if( response == RESULT.SUCCESS() ):
			window.addstr("sign up successfully.\n")
			window.refresh()
			time.sleep(1)
			return 1
		else :
			signup_error_msg_len = int.from_bytes(server_fd.recv(4), "big")
			signup_error_msg = server_fd.recv(signup_error_msg_len).decode(encode_method)
			window.addstr(signup_error_msg)
			my_raw_input(window, "\nenter anthing to continue: ")
			return -1

	except Exception as e:
		#when error occur, connecting server again
		window.addstr(str(e))
		window.addstr("\n")
		return -1


def connecting_server(window, my_name_list):
	while(1):
		while(1):
			try:
				window.clear()
				server_addr = my_raw_input(window, "Input server address:")
				server_port = int(my_raw_input(window, "Input server port:"))
				server_addr = socket.gethostbyname(server_addr)
				server_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
				server_fd.connect((server_addr, server_port))
				break #connect to server successfully
			except Exception as e:
				window.addstr(str(e))
				window.addstr("\n")
				while(1):
					action = my_raw_input(window, "quit? y/n: ")
					if(action == "y"):
						curses.endwin()
						sys.exit()
					elif(action != 'n'):
						continue
					break

				continue

		while(1):
			window.clear()
			action = my_raw_input(window, "Input\n1 to sign in.\n2 to sign up\nquit to quit\nelse to connect to another server: ")
			if(action == '1'):
				ret_fd = sign_in(window, server_fd, my_name_list)
				if(ret_fd == -1): #fail
					continue
				else: #sign in successfully
					return ret_fd

			elif(action == '2'):
				res = sign_up(window, server_fd)
			elif(action == 'quit'):
				curses.endwin()
				sys.exit()
			else:
				server_fd.close()
				break 
			

def chatting_initial(window, server_fd, my_name):
	try:
		server_fd.send(ACTION.CHATTING_LIST().encode(encode_method))
		#print("chatting_init ")
		response = server_fd.recv(1).decode(encode_method)
		#print("recv")
		if(response != RESULT.SUCCESS()):
			window.clear()
			error_msg_len = int.from_bytes(server_fd.recv(4), "big")
			error_msg = server_fd.recv(error_msg_len).decode(encode_method)
			window.addstr(error_msg + "\n")
			my_raw_input(window, "enter anthing to continue: ")
			return -1
		chatP_list_num = int.from_bytes(server_fd.recv(4), "big")
		chatP_list = []
		#print("recv chatP_list_num ")
		#print(chatP_list_num)
		for i in range(chatP_list_num):
			#print(str(i))
			user_name_len = int.from_bytes(server_fd.recv(4), "big")
			#print(user_name_len)
			user_name = server_fd.recv(user_name_len).decode(encode_method)
			#print(user_name)
			msg_num = int.from_bytes(server_fd.recv(4), "big")
			#print(msg_num)
			chatting_history = []
			for msg_i in range(msg_num):
				#print("msgi: " + str(msg_i))
				whose_msg = server_fd.recv(1).decode(encode_method)
				msg_serial_num = int.from_bytes(server_fd.recv(4), "big")
				msg_len = int.from_bytes(server_fd.recv(4), "big")
				msg = server_fd.recv(msg_len).decode(encode_method)
				chatting_history.append((whose_msg, msg_serial_num, msg))
			useri = User(user_name, chatting_history)
			chatP_list.append(useri)
		#print("create my_chatwin")
		my_chat_win = Chat_Window(chatP_list, window, my_name)
		my_chat_win.show()
		return my_chat_win				

	except Exception as e:
		#when error occur, connecting server again
		window.addstr(str(e))
		return -1

def server_thread(window, my_chat_win, server_fd, semaphore, server_running):
	while(server_running.isSet()):
		try:
			action = server_fd.recv(1).decode(encode_method)
		except:
			continue

		semaphore.acquire()
		if(action == ACTION.CHAT()):
			res = server_fd.recv(1).decode(encode_method)
			if(res == RESULT.FAIL()):
				msg_len = int.from_bytes(server_fd.recv(4), "big")
				error_msg = server_fd.recv(msg_len).decode(encode_method)
				my_chat_win.system_msg_show(error_msg)
			elif(res == RESULT.SUCCESS()):
				name_len = int.from_bytes(server_fd.recv(4), "big")
				name = server_fd.recv(name_len).decode(encode_method)
				#print("chat with: " + name)
				my_chat_win.chat_with_chatP(name)
		elif(action == ACTION.RECV_MSG()):
			msg_len = int.from_bytes(server_fd.recv(4), "big")
			msg = server_fd.recv(msg_len).decode(encode_method)
			name_len = int.from_bytes(server_fd.recv(4), "big")
			name = server_fd.recv(name_len).decode(encode_method)
			my_chat_win.recv_chatP_msg(name, msg)
		elif(action == ACTION.FILE()):
			base_len = int.from_bytes(server_fd.recv(4), "big")
			print("base_len " + str(base_len))
			base = server_fd.recv(base_len).decode(encode_method)
			sender_name_len = int.from_bytes(server_fd.recv(4), "big")
			sender_name = server_fd.recv(sender_name_len).decode(encode_method)
			file_size = int.from_bytes(server_fd.recv(4), "big")
			f = open(base, "wb")
			my_chat_win.system_msg_show(sender_name + " sending file: " +base + " " + str(file_size) + "bytes")
			data_list = []
			while(file_size > 0):
				my_chat_win.system_msg_show(sender_name + " sending file: " +base + " " + str(file_size) + "bytes")
				if(file_size < 1024):
					l = server_fd.recv(file_size)
					data_list.append(l)
					file_size = file_size - len(l)
				else:
					l = server_fd.recv(1024)
					data_list.append(l)
					file_size = file_size - len(l)
			for data in data_list:
				f.write(data)
			f.close()
			my_chat_win.system_msg_show(sender_name + " finish sending " + base)
		semaphore.release()
	
	

	
def chat_control(window, my_chat_win, server_fd):
	semaphore = threading.Semaphore(1)
	server_fd.settimeout(5)
	server_running = threading.Event()
	server_running.set()
	thrd = threading.Thread(target = server_thread, args = (window, my_chat_win, server_fd, semaphore, server_running, ))
	thrd.start()
	height, width = window.getmaxyx()
	# state 0 for main page, 1 for chatting page
	while(1):
		window.move(height-1, 0)
		window.clrtoeol()
		action = my_raw_input(window, "")
		if(len(action) <= 0):
			continue
		semaphore.acquire()
		if( my_chat_win.get_state() == 0 ):
			if(action[0] == "c" and len(action) >= 3 and action[1] == ":"):				
				buf = ACTION.CHAT().encode(encode_method) + struct.pack(">I", len(action) - 2) + action[2:].encode(encode_method)
				server_fd.send(buf)
			elif(action == "n"):
				my_chat_win.chatP_list_next_page()
				my_chat_win.show()
			elif(action == "p"):
				my_chat_win.chatP_list_previous_page()
				my_chat_win.show()
			elif(action == "quit"):
				my_chat_win.system_msg_show("quitting~~~")
				server_running.clear()
				thrd.join()
				server_fd.close()
				curses.endwin()
				sys.exit()
			else:
				my_chat_win.system_msg_show("invalid command")
			semaphore.release()
		else:
			if(action == "up"):
				my_chat_win.chat_page_up()
				my_chat_win.show()
			elif(action == "down"):
				my_chat_win.chat_page_down()
				my_chat_win.show()
			elif(action == "main"):
				my_chat_win.set_state(0)
				my_chat_win.show()
			elif(len(action) > 5 and action[4] == ":"):
				if(action[0:4] == "send"):
					if(len(action) - 5 > STANDARD.MAX_MESSAGE_LEN()):
						my_chat_win.system_msg_show("MAX MESSAGE LENGTH IS {}".format(STANDARD.MAX_MESSAGE_LEN()))
					else:
						buf = ACTION.SEND_MSG().encode(encode_method) + struct.pack(">I", len(action) - 5) + action[5:].encode(encode_method)
						#print(my_chat_win.get_chat_name())
						buf = buf + struct.pack(">I", len(my_chat_win.get_chat_name())) + my_chat_win.get_chat_name().encode(encode_method)
						server_fd.send(buf)
						my_chat_win.send_chatP_msg(my_chat_win.get_chat_name(), action[5:])
				elif(action[0:4] == "file" and len(action) > 5):
					path_list = action[5:].split(" ")
					for path in path_list:
						if(len(path) > 40):
							my_chat_win.system_msg_show("too long: " + path)
							continue
						try:
							f = open(path, "rb")
						except Exception as e:
							my_chat_win.system_msg_show(path + " open fail")
							continue
						file_size = os.stat(path).st_size
						if(file_size > 10485760):
							my_chat_win.system_msg_show(path + " too large")
							continue
						base = os.path.basename(path)
						buf = ACTION.FILE().encode(encode_method) + struct.pack(">I", len(base.encode(encode_method))) + base.encode(encode_method)
						buf = buf + struct.pack(">I", len(my_chat_win.get_chat_name())) + my_chat_win.get_chat_name().encode(encode_method)
						buf = buf + struct.pack(">I", file_size)
						server_fd.send(buf)
						my_chat_win.system_msg_show("sending: " + base)
						while(file_size > 0):
							my_chat_win.system_msg_show("sending: " + base +" " + str(file_size) + "bytes")
							if(file_size < 1024):
								l = f.read(file_size)
								file_size -= len(l) 
								server_fd.send(l)
							else:
								l = f.read(1024)
								file_size = file_size - len(l)
								server_fd.send(l)
						f.close()
						my_chat_win.system_msg_show("finish: " + base)

						

			else:
				my_chat_win.system_msg_show("invalid command")
			semaphore.release()	



if __name__ == '__main__':
	window = curses.initscr()
	window.resize(20, 60)
	curses.echo()
	my_name_list = []
	while(1):
		server_fd = connecting_server(window, my_name_list)
		if(server_fd == -1):
			continue
		# start chatting
		my_chat_win = chatting_initial(window, server_fd, my_name_list[0])
		if(my_chat_win == -1):
			continue
		chat_control(window, my_chat_win, server_fd)

		




	
	
