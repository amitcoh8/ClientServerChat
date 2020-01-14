Client Server Chat App
----------------------
GitHub Link: https://github.com/amitcoh8/ClientServerChat

Instructions:

A) Run the server
B) Run one or more clients

*If you are running the files from their .EXE versions and not the .PY version, the booting up proccess 
takes a couple of seconds*

Client registration:
--------------------
When running a client, there are two options to set the username:
1. If there is a configuration file named Config.config, the program will read the username from the file
  (if you use this method, please make sure you dont have two clients (or more) trying to load the same username)
2. Otherwise, you will be asked to insert your name: "Please register your username:"

After the client has connected to the server, you will get a message: "Registered successfully!"

Sending a message:
------------------
In order to send a message:
1. Insert the usernames of the users you want to send your message to. 
   For example ("Dani Yossi Shimon Rafi" etc...)
   As you can see in the example above, please enter a user name, then a space, and then optionally an additional user, and so on..
2. In the next line, enter the message you wish to send the listed users.
   For example ("This is my message, blah blah blah, $#!"

When one client receives a message from another client, he will see:
([time]) [name_of_sender] : [message]

Example:
--------
An example of a user named Yossi. First, Yossi is registering, after that he will send a message to Aviv and to Stav. 
At the end, he will be getting a message from Aviv.

Console display:
Please register your username:
Yossi 
Registered successfully!
Aviv Stav
Hi Aviv, Stav, How are you? Are we meeting today ?
(17:35) Aviv: Hi Yossi yes, see you at 8?





 