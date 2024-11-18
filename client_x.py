import socket
import threading
import time
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
root = tk.Tk()
root.withdraw()  # Hide the main window while asking for input

flag=0

# Connection setup
nickname = simpledialog.askstring("Nickname", "Choose a nickname:", parent=root)
password = simpledialog.askstring("Password", "Enter password to join the private network:", parent=root)

root.deiconify()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('10.2.5.39', 55555))  

BUFSIZE = 1024
public_key = []
private_key = []
reciver_pu = [0, 0]

def encrypt_message(plaintext, e, n):
    if n == 0:
        raise ValueError("Invalid modulus (n cannot be 0) in encryption.")
    return pow(plaintext, e, n)

def decrypt_message(ciphertext, d, n):
    if n == 0:
        raise ValueError("Invalid modulus (n cannot be 0) in decryption.")
    return pow(ciphertext, d, n)


def receive():
    while True:
        try:
            message = client.recv(4096).decode()
            
            if message == 'NICK':
                client.send(nickname.encode())
            elif message == 'PASSWORD':
                client.send(password.encode())
            elif message == "Wrong Password":
                print("Password is incorrect.")
                client.close()
                break
            elif message != '' and message[0] == '#':
                temp = message.split(',')
                if len(temp) >= 5 and temp[1].isdigit() and temp[2].isdigit() and temp[3].isdigit() and temp[4].isdigit():
                    public_key.append(int(temp[1]))
                    public_key.append(int(temp[2]))
                    private_key.append(int(temp[3]))
                    private_key.append(int(temp[4]))
                    print('Public key:', public_key)
                    print('Private key:', private_key)
                else:
                    print(temp)
                    print("Received invalid key format.")
            elif message != '' and message[0] == '*':
                temp = message.split(',')
                if len(temp) >= 3 and temp[1].isdigit() and temp[2].isdigit():
                    reciver_pu[0] = int(temp[1])
                    reciver_pu[1] = int(temp[2])
                    print("Receiver's public key:", reciver_pu)
                    # flag=1
                else:
                    print("Received invalid public key format.")
            elif ":" in message:
                temp = message.split(':')
                
                if temp[1].strip().isdigit():
                    ciph = int(temp[1].strip())
                    plaintext = decrypt_message(ciph, private_key[0], private_key[1])
                    print(f'{temp[0]}: {plaintext}')
                    chat_log.insert(tk.END, f'{temp[0]}: {plaintext} \n')   
                else:
                    print(temp)
                    print("Received invalid ciphertext format.")
            else:
                print(message)
                chat_log.insert(tk.END, message)
        except Exception as e:
            print("An error occurred:", e)
            client.close()
            break

def send_message(msg_type):
    try:
        msg_length = len(msg_type)
        send_length = str(msg_length).encode()
        send_length += b' ' * (64 - len(send_length))
        client.send(send_length)
        client.send(msg_type.encode())

        if msg_type == 'broadcast':
            message = f'{nickname}: {message_entry.get()} '
            msg_length = len(message)
            send_length = str(msg_length).encode()
            send_length += b' ' * (64 - len(send_length))
            client.send(send_length)
            client.send(message.encode())
            chat_log.insert(tk.END, 'Broadcast message sent!\n')

        elif msg_type == 'unicast':
            target_nick = simpledialog.askstring("Unicast", "Enter the nickname of the recipient:")
            combine = target_nick + ',' + nickname
            msg_length = len(combine)
            send_length = str(msg_length).encode()
            send_length += b' ' * (64 - len(send_length))
            client.send(send_length)
            client.send(combine.encode())
            while reciver_pu[1]==0: continue
            message = int(message_entry.get())
            # time.sleep(10)
            print(reciver_pu)
            encrypted_message = encrypt_message(message, reciver_pu[0], reciver_pu[1])
            final_message = f'{nickname}: {encrypted_message} '
            msg_length = len(final_message)
            send_length = str(msg_length).encode()
            send_length += b' ' * (64 - len(send_length))
            client.send(send_length)
            client.send(final_message.encode())
            chat_log.insert(tk.END, 'Unicast message sent!\n')
            # flag=0

        elif msg_type == 'multicast':
            group_size = int(simpledialog.askstring("Multicast", "Enter number of people in the group:"))
            group = [simpledialog.askstring("Multicast", "Enter nickname:") for _ in range(group_size)]
            group_str = ' '.join(group)
            grplen = len(group_str)
            send_length = str(grplen).encode()
            send_length += b' ' * (64 - len(send_length))
            client.send(send_length)
            client.send(group_str.encode())

            message = f'{nickname}: {message_entry.get()} '
            msg_length = len(message)
            send_length = str(msg_length).encode()
            send_length += b' ' * (64 - len(send_length))
            client.send(send_length)
            client.send(message.encode())
            chat_log.insert(tk.END, 'Multicast message sent!\n')
    except Exception as e:
        chat_log.insert(tk.END, f"An error occurred: {e}\n")

# GUI setup
root = tk.Tk()
root.title("Chat Client")

chat_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20, state='normal')
chat_log.pack(padx=10, pady=10)

message_entry = tk.Entry(root, width=40)
message_entry.pack(padx=10, pady=5)

send_broadcast_btn = tk.Button(root, text="Broadcast", command=lambda: send_message('broadcast'))
send_broadcast_btn.pack(side=tk.LEFT, padx=5)

send_unicast_btn = tk.Button(root, text="Unicast", command=lambda: send_message('unicast'))
send_unicast_btn.pack(side=tk.LEFT, padx=5)

send_multicast_btn = tk.Button(root, text="Multicast", command=lambda: send_message('multicast'))
send_multicast_btn.pack(side=tk.LEFT, padx=5)

receive_thread = threading.Thread(target=receive)
receive_thread.start()

root.mainloop()
