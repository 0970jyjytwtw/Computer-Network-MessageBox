#!/usr/bin/env python3
import socket, math
import os
import sys, time
import threading
import select
import struct
import sqlite3
import hashlib
from myprotocol import ACTION, encode_method, RESULT
def length_valid(input_string):
	string_length = len(input_string)
	if(string_length <= 0 or string_length > 20):
		return -1
	return 1

def signup(c, fd):
    username_len = int.from_bytes(fd.recv(4), "big")
    passwd_len = int.from_bytes(fd.recv(4), "big")
    print(username_len)
    print(passwd_len)
    if(username_len > 20 or username_len <= 0 or passwd_len > 20 or passwd_len <= 0):
        return -1 #close connection
    username = fd.recv(username_len).decode(encode_method)
    passwd = fd.recv(passwd_len).decode(encode_method)
    print(username)
    print(passwd)
    if(username.isalnum() == False): #invalid username
        error_msg = "invalid username"
        print(error_msg)
        buf = RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1

    rows = c.execute("SELECT * from usr_info WHERE username == (?)", [username]).fetchall()

    if(len(rows) > 0):
        error_msg = "username exists"
        print(error_msg)
        buf = RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
    else:
        sha256 = hashlib.sha256()
        sha256.update(passwd.encode(encode_method))
        passwd_hash = sha256.hexdigest()
        c.execute("INSERT INTO usr_info (username, passwd) VALUES (?, ?)", (username, passwd_hash))
        c.execute("CREATE TABLE IF NOT EXISTS {} (ID INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, whose TEXT, msg TEXT)".format("msg_" + username))
        fd.send(RESULT.SUCCESS().encode(encode_method))
    return 1

def signin(c, fd, online_user_list, fd_username_id_dict, username_fd_dict):
    username_len = int.from_bytes(fd.recv(4), "big")
    passwd_len = int.from_bytes(fd.recv(4), "big")
    if(username_len > 20 or username_len <= 0 or passwd_len > 20 or passwd_len <= 0):
        return -1 #close connection
    username = fd.recv(username_len).decode(encode_method)
    passwd = fd.recv(passwd_len).decode(encode_method)
    print(username)
    print(passwd)
    if(username.isalnum() == False): #invalid username
        error_msg = "username or passwd wrong"
        buf = RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    print("isalnum")
    rows = c.execute("SELECT * from usr_info WHERE username == (?)", [username]).fetchall()
    if(len(rows) <= 0):
        error_msg = "username or passwd wrong"
        buf = RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    print("exist")
    row = rows[0]
    sha256 = hashlib.sha256()
    sha256.update(passwd.encode(encode_method))
    passwd_hash = sha256.hexdigest()
    if(row[2] != passwd_hash):
        error_msg = "username or passwd wrong"
        buf = RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    elif(row[0] in online_user_list):
        error_msg = "this user has signed in"
        buf = RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    else:
        fd.send(RESULT.SUCCESS().encode(encode_method))
        online_user_list.append(row[0])
        fd_username_id_dict[fd] = (username, row[0])
        username_fd_dict[username] = fd
        return 1

def chatting_list(c, fd, fd_username_id_dict):
    if(fd not in fd_username_id_dict):
        error_msg = "you are not online"
        buf = RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    print("online")
    username, userid = fd_username_id_dict[fd]
    #(ID INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, whose INT, msg TEXT)
    row_list = c.execute("SELECT * from {} ORDER BY user".format("msg_" + username)).fetchall()
    fd.send(RESULT.SUCCESS().encode(encode_method))
    if(len(row_list) > 0):
        user_name_list = [row_list[0][1]]
        tmp_user_name = row_list[0][1]
        chat_history_list = []
        msg_list = []
        i_th_msg = 0
        for row in row_list:
            if(row[1] == tmp_user_name):
                msg_list.append( (row[2], i_th_msg, row[3]) )
                i_th_msg = i_th_msg + 1
            else:
                chat_history_list.append(msg_list)
                msg_list = []
                i_th_msg = 1
                tmp_user_name = row[1]
                user_name_list.append(tmp_user_name)
                msg_list.append( (row[2], 0, row[3]))
        chat_history_list.append(msg_list)
        fd.send(struct.pack(">I", len(user_name_list)))
        print(len(user_name_list))
        for i in range(len(user_name_list)):
            chat_history = chat_history_list[i]
            buf = struct.pack(">I", len(user_name_list[i])) + user_name_list[i].encode(encode_method) + struct.pack(">I", len(chat_history))
            fd.send(buf)
            for msg in chat_history:
                buf = msg[0].encode(encode_method) + struct.pack(">I", msg[1]) + struct.pack(">I", len(msg[2])) + msg[2].encode(encode_method)
                fd.send(buf)
    else:
        fd.send(struct.pack(">I", 0))
    return 1

def chat(c, fd, fd_username_id_dict):
    print("chat")
    chatP_name_len = int.from_bytes(fd.recv(4), "big")
    print(chatP_name_len)
    if(chatP_name_len > 20 or chatP_name_len < 0):
        return -1 #close connection

    chatP_name = fd.recv(chatP_name_len).decode(encode_method)
    print(chatP_name)

    if(fd not in fd_username_id_dict):
        error_msg = "you are not online"
        buf = ACTION.CHAT().encode(encode_method) + RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    username, userid = fd_username_id_dict[fd]
    if(username == chatP_name):
        error_msg = "do not chat with yourself"
        buf = ACTION.CHAT().encode(encode_method) + RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    row_list = c.execute("SELECT * from usr_info WHERE username == (?)", [chatP_name]).fetchall()

    if(len(row_list) <= 0):
        error_msg = "user not found"
        buf = ACTION.CHAT().encode(encode_method) + RESULT.FAIL().encode(encode_method) + struct.pack(">I", len(error_msg)) + error_msg.encode(encode_method)
        fd.send(buf)
        return 1
    
    row = row_list[0]
    buf = ACTION.CHAT().encode(encode_method) + RESULT.SUCCESS().encode(encode_method) + struct.pack(">I", len(row[1])) + row[1].encode(encode_method)
    fd.send(buf)
    print(buf)
    return 1

def send_msg(c, fd, fd_username_id_dict, username_fd_dict):
    message_len = int.from_bytes(fd.recv(4), "big")
    message = fd.recv(message_len).decode(encode_method)
    receiver_name_len = int.from_bytes(fd.recv(4), "big")
    receiver_name = fd.recv(receiver_name_len).decode(encode_method)
    if(fd not in fd_username_id_dict):
        # you are not online
        return 1
    row_list = c.execute("SELECT * from usr_info WHERE username == (?)", [receiver_name]).fetchall()
    if(len(row_list) <= 0):
        #user not found
        return 1
    
    sender_name , sender_id = fd_username_id_dict[fd]
    print(sender_name)
    print(message)
    print(receiver_name)
    if(receiver_name == sender_name):
        #not send to yourself
        return 1
    c.execute("INSERT INTO {} (user , whose , msg ) VALUES (?, ?, ?)".format("msg_" + sender_name), (receiver_name, "1", message))
    c.execute("INSERT INTO {} (user , whose , msg ) VALUES (?, ?, ?)".format("msg_" + receiver_name), (sender_name, "0", message))

    if(receiver_name in username_fd_dict):
        receiver_fd = username_fd_dict[receiver_name]
        buf = ACTION.RECV_MSG().encode(encode_method) + struct.pack(">I", len(message)) + message.encode(encode_method)
        receiver_fd.send(buf)
        buf = struct.pack(">I", len(sender_name)) + sender_name.encode(encode_method)
        receiver_fd.send(buf)
    return 1

def send_file(c, fd, fd_username_id_dict, username_fd_dict):
    base_len = int.from_bytes(fd.recv(4), "big")
    base = fd.recv(base_len).decode(encode_method)
    receiver_name_len = int.from_bytes(fd.recv(4), "big")
    receiver_name = fd.recv(receiver_name_len).decode(encode_method)
    file_size = int.from_bytes(fd.recv(4), "big")
    if(file_size > 1024*1024*10):
        print("file too big")
        return -1

    if(fd not in fd_username_id_dict):
        # you are not online
        return -1
    
    
    sender_name , sender_id = fd_username_id_dict[fd]
    print(sender_name)
    print(base)
    print(receiver_name)
    if((receiver_name == sender_name) or (receiver_name not in username_fd_dict)):
        print("#not send to yourself or #receiver is not online")
        while(file_size > 0):
            if(file_size < 1024):
                l = fd.recv(file_size)
                file_size -= len(l)
            else:
                l = fd.recv(1024)
                file_size -= len(l)
        return 1
    print("pass")
    receiver_fd = username_fd_dict[receiver_name]
    buf = ACTION.FILE().encode(encode_method) + struct.pack(">I", len(base)) + base.encode(encode_method)
    buf = buf + struct.pack(">I", len(sender_name)) + sender_name.encode(encode_method) + struct.pack(">I", file_size)
    receiver_fd.send(buf)
    data_list = []
    while(file_size > 0):
        if(file_size < 1024):
            l = fd.recv(file_size)
            data_list.append(l)
            file_size -= len(l) 
        else:
            l = fd.recv(1024)
            data_list.append(l)
            file_size -= len(l)
    
    for data in data_list:
        receiver_fd.send(data)

    return 1



dbpath = "db.sqlite"
conn = sqlite3.connect(dbpath)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS usr_info (ID INTEGER PRIMARY KEY AUTOINCREMENT, username text, passwd text)")
port = int(input("input port number: "))
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

try:
    server.bind(('', port))
    print ('Socket bind complete')

except Exception as e:
    print(e)
    exit()

server.listen(5)
print('Socket now listening')

rfds = [server]
online_user_list = []
fd_username_id_dict = {}
username_fd_dict = {}
commit_cnt = 0
while(1):
    readable, writable, excetional = select.select(rfds, [], [], 1)
    print("go")
    commit_cnt = commit_cnt + 1
    if(commit_cnt == 5):
        conn.commit()
        commit_cnt = 0
    for fd in readable:
        if fd is server:
            client, addr = fd.accept()
            rfds.append(client)
            print(len(rfds))
            print('Connected with '  + addr[0] +':' +  str(addr[1]))
        else:
            try:
                action = fd.recv(1).decode(encode_method)
            except Exception as e:
                print(e)
                print(fd.fileno())
                if(fd in fd_username_id_dict):
                    usrpair = fd_username_id_dict[fd]
                    online_user_list.remove(usrpair[1])
                    print(usrpair[0] + ": has error")
                    del fd_username_id_dict[fd]
                    del username_fd_dict[usrpair[0]]

                rfds.remove(fd)
                continue
            if(len(action) > 0):
                if(action == ACTION.SIGN_UP()):
                    res = signup(c, fd)
                    if(res == -1):
                        if(fd in fd_username_id_dict):
                            usrpair = fd_username_id_dict[fd]
                            online_user_list.remove(usrpair[1])
                            del fd_username_id_dict[fd]
                            del username_fd_dict[usrpair[0]]
                        rfds.remove(fd)
                        fd.close()
                    

                elif(action == ACTION.SIGN_IN()):
                    res = signin(c, fd, online_user_list, fd_username_id_dict, username_fd_dict)
                    if(res == -1):
                        if(fd in fd_username_id_dict):
                            usrpair = fd_username_id_dict[fd]
                            online_user_list.remove(usrpair[1])
                            del fd_username_id_dict[fd]
                            del username_fd_dict[usrpair[0]]
                        rfds.remove(fd)
                        fd.close()

                elif(action == ACTION.CHATTING_LIST()):
                    res =chatting_list(c, fd, fd_username_id_dict)
                    if(res == -1):
                        if(fd in fd_username_id_dict):
                            usrpair = fd_username_id_dict[fd]
                            online_user_list.remove(usrpair[1])
                            del fd_username_id_dict[fd]
                            del username_fd_dict[usrpair[0]]
                        rfds.remove(fd)
                        fd.close()

                elif( action == ACTION.CHAT()):
                    res = chat(c, fd, fd_username_id_dict)
                    if(res == -1):
                        if(fd in fd_username_id_dict):
                            usrpair = fd_username_id_dict[fd]
                            online_user_list.remove(usrpair[1])
                            del fd_username_id_dict[fd]
                            del username_fd_dict[usrpair[0]]
                        rfds.remove(fd)
                        fd.close()
                elif( action == ACTION.SEND_MSG()):
                    res = send_msg(c, fd, fd_username_id_dict, username_fd_dict)
                    if(res == -1):
                        if(fd in fd_username_id_dict):
                            usrpair = fd_username_id_dict[fd]
                            online_user_list.remove(usrpair[1])
                            del fd_username_id_dict[fd]
                            del username_fd_dict[usrpair[0]]
                        rfds.remove(fd)
                        fd.close()
                elif( action == ACTION.FILE() ):
                    res = send_file(c, fd, fd_username_id_dict, username_fd_dict)
                    if(res == -1):
                        if(fd in fd_username_id_dict):
                            usrpair = fd_username_id_dict[fd]
                            online_user_list.remove(usrpair[1])
                            del fd_username_id_dict[fd]
                            del username_fd_dict[usrpair[0]]
                        rfds.remove(fd)
                        fd.close()
            
            else:
                if(fd in fd_username_id_dict):
                    usrpair = fd_username_id_dict[fd]
                    online_user_list.remove(usrpair[1])
                    print(usrpair[0] + ": log out")
                    del fd_username_id_dict[fd]
                    del username_fd_dict[usrpair[0]]
                rfds.remove(fd)
                fd.close()





