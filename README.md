NTU 2019fall Computer Network Final  cnMessage.

MessageBox written by python3.

一、User & Operator Guide 

需要在linux上用python3執行。 
因為都是用python寫的，所以不用build，只要把沒有的library裝一下就好。 
程式上面都有print指示出來。 

二、Instructions on how to run server & clients 

server: 
1.用python3打開server.py 
2. 輸入port number 

client: 
1.用python3打開test_client.py 
2.輸入server的hostname和port number 


三、System & Program Design 

client端是使用curses這個library來輔助介面顯示。 
因為curses的鍵盤輸入不是stdin，所以不太知道要如何放進select裡面。 
所以用一個thread監控server的file descriptor，主程式監控鍵盤輸入。 
database是使用sqlite3這個library 


server端就只是根據client端傳來的資料，做出相對應的動作。 
sign up: 

1. Client端將username, password傳入server。 
2. Server檢查username有無重複，若無重複就將和password的sha256 hash
和username存進資料庫的user_info table。並且加開msg_{username}的
table用這個來存取之後此user的訊息。 

sign in: 

1. Client端將username, password傳入server。 
2. Server檢查此password的hash有沒有正確和username是否存在。再來檢
查此user不能上線中。 
。最後用dictionary綁定socket_fd和username的關係。所以可以使用此
dictionary來查找username是否上線中。如果socket_fd關閉，就將
dictionary關於socket_fd -> username刪除。 
3. 再來client端會和server端請求聊天紀錄，server收到請求後就會將聊天
紀錄傳送給client端。 

Send msg: 

1. Client端先向server查詢receiver_name是否存在。Server會回傳結果，若
是合法，client端就會進入聊天模式，這時候client端才能送訊息。 
2. 進入聊天模式後client就可以把receiver_name和message傳給server。
3. Server檢查此sender必須上線中，再來檢查receiver_name需存在且
receiver和sender不可為同一個人，接下來就將message存入receiver和
sender的message table。若是receiver為上線中，則將message 傳送給
receiver。 

File: 

1. Client端進入聊天模式後，可將file和receiver_name傳入server。 

2. Server檢查receiver是否上線中，若否則將file丟棄。若是直接將file傳送
給receiver。
