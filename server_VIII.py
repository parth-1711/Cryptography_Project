import threading
import sympy as sp
import random
import socket
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import time
# from sympy import isprime
# import sys

# start_time = time.time()
# for _ in range(100000):
#     pass

# end_time = time.time()

elapsed_time = 0



def RealChua(t, state):
    """
    Computes the derivatives of the Chua's circuit variables.
    """
    V1, V2, z = state  
    R0 = 3.8 # 3.9 Ohms  

    # Circuit constants
    C1 = 10e-9 + elapsed_time*1e-8   # 10 nF
    C2 = 100e-9  # 100 nF
    R = 15 +R0*450.0   
    G = 1 / R    

    R1 = 220
    R2 = 220
    R3 = 2200
    R4 = 22000
    R5 = 22000
    R6 = 3300

    Esat = 9  # 9V batteries
    E1 = R3 / (R2 + R3) * Esat
    E2 = R6 / (R5 + R6) * Esat

    m12 = -1 / R6
    m02 = 1 / R4
    m01 = 1 / R1
    m11 = -1 / R3
    m1 = m12 + m11

    # Determine slope m0
    if E1 > E2:
        m0 = m11 + m02
    else:
        m0 = m12 + m01

    mm1 = m01 + m02
    Emax = max(E1, E2)
    Emin = min(E1, E2)

    # Nonlinear function g(V1)
    if abs(V1) < Emin:
        g = V1 * m1
    elif abs(V1) < Emax:
        g = V1 * m0
        if V1 > 0:
            g += Emin * (m1 - m0)
        else:
            g += Emin * (m0 - m1)
    else:
        g = V1 * mm1
        if V1 > 0:
            g += Emax * (m0 - mm1) + Emin * (m1 - m0)
        else:
            g += Emax * (mm1 - m0) + Emin * (m0 - m1)

    # Gyrator constants
    R7 = 100  # 100 Ohms
    R8 = 1000 # 1 kOhms
    R9 = 1000 # 1 kOhms
    R10 = 1800
    C = 100e-9  # 100 nF
    L = R7 * R9 * C * R10 / R8  # 18 mH

    # Chua's circuit equations
    xdot = (1 / C1) * (G * (V2 - V1) - g)
    ydot = (1 / C2) * (G * (V1 - V2) + z)
    zdot = -(1 / L) * (V2) 

    return [xdot, ydot, zdot]

# Initial conditions
initial_state = [0.1, 0.0, 0.0]  # [x0, y0, z0]

# Time span
t_span = (0, 0.049)  # Simulate for 10 milliseconds
t_eval = np.linspace(*t_span, 4000)  # High resolution

# Solve the system
solution = solve_ivp(RealChua, t_span, initial_state, t_eval=t_eval, method='RK45')

# Extract results
t = solution.t
V1, V2, IL = solution.y  # V1 = x, V2 = y, IL = z
# print(IL)

X1 = np.divide(V1, V2, out=np.zeros_like(V1, dtype=float), where=V2!=0)  # x/y
X2 = np.divide(V2, IL, out=np.zeros_like(V2, dtype=float), where=IL!=0)  # y/z
X3 = np.divide(V1, IL, out=np.zeros_like(IL, dtype=float), where=IL!=0)  # x/z

y1=(np.round(X1).astype(int) % 2047).tolist()
y2=(np.round(X2).astype(int) % 2047).tolist()
y3=(np.round(X3).astype(int) % 2047).tolist()

p_set=[num for num in y1 if sp.isprime(num)]
q_set=[num for num in y2 if sp.isprime(num)]
r_set=[num for num in y3 if sp.isprime(num)]

min_size = min(len(p_set), len(q_set), len(r_set))
pu = p_set[:min_size]
qu = q_set[:min_size]
ru = r_set[:min_size]

host = socket.gethostbyname(socket.gethostname())
port = 3000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

def encrypt_message(plaintext, e, n):
    return pow(plaintext, e, n)

def decrypt_message(ciphertext, d, n):
    return pow(ciphertext, d, n)

def generate_rsa_keys(prime1, prime2):
    n = prime1 * prime2
    phi = (prime1 - 1) * (prime2 - 1)
    e = 3
    while sp.gcd(e, phi) != 1:
        e += 2
    d = pow(e, -1, phi)
    return (e, n), (d, n)

# Generate a pool of keys
key_pool = []
def generate_key_pool(num_keys=10 if len(p_set)>10 else len(p_set)):
    for i in range(num_keys):
        # prime1 = sp.nextprime(random.randint(1000, 5000))
        # prime2 = sp.nextprime(random.randint(1000, 5000))
        public_key, private_key = generate_rsa_keys(p_set[i], q_set[i])
        key_pool.append((public_key, private_key))

generate_key_pool(10)

clients = []
nicknames = []
client_keys = {}


PASSWORD = "p"

def broadcast(message):
    # print(f"activve clients {clients}")
    for client in clients:
        client.send(message)
        # print(f"[MESSAGE SENT]  {message}")

def unicast(nickname,msg):
    print(nickname)
    index=nicknames.index(nickname)
    client=clients[index]
    client.send(msg)
    print(msg)
    print(f"msg sent to {nickname}")

def multicast(message, group):
    # print(f"active clients {clients}")
    for client in group:
        index=nicknames.index(client)
        clt=clients[index]
        # clt.send(msg)
        clt.send(message)
        
def encrypt_message(plaintext, e, n):
    return pow(plaintext, e, n)

# Decryption function
def decrypt_message(ciphertext, d, n):
    return pow(ciphertext, d, n)

# Generate RSA keys (simplified version for demonstration)
def generate_rsa_keys(prime1, prime2):
    n = prime1 * prime2
    phi = (prime1 - 1) * (prime2 - 1)
    e = 3
    while sp.gcd(e, phi) != 1:
        e += 2
    d = pow(e, -1, phi)
    return (e, n), (d, n)

# Generate a pool of keys
key_pool = []
def generate_key_pool(num_keys=10):
    for _ in range(num_keys):
        prime1 = sp.nextprime(random.randint(1000, 5000))
        prime2 = sp.nextprime(random.randint(1000, 5000))
        public_key, private_key = generate_rsa_keys(prime1, prime2)
        key_pool.append((public_key, private_key))

generate_key_pool(10)

def handle(client):
    while True:
        try:    
            msg_length=int(client.recv(64).decode())
            # print(msg_length)
            msg_type = client.recv(msg_length).decode()
            print(msg_type)
            
            
            if msg_type.strip().upper()=='BROADCAST':
                # print('hi')
                msg_length=int(client.recv(64).decode())
                # print(msg_length)
                
                message=client.recv(msg_length).decode()
                # print(message)
                broadcast(message.encode())

            elif msg_type.strip().upper()=='UNICAST':
                msg_length=int(client.recv(64).decode())
                nickname=client.recv(msg_length).decode()
                sender=nickname.split(',')[1]
                reci=nickname.split(',')[0]
                
                pu_key=client_keys[reci]
                # print('h')
                # print(pu_key[0])
                message=f'*,{pu_key[0][0]},{pu_key[0][1]}'.encode()

                print(message)
                client.send(message)
                
                # send_length=str(len(message)).encode()
                # send_length+=b' '*(64-len(send_length))
                
                
                # client.send(send_length)
                # client.send(combine.encode())
                
                msg_length=int(client.recv(64).decode())
                # print(msg_length)
                
                message=client.recv(msg_length).decode()
                # msg=client.recv(1024)
                unicast(reci,message.encode())

            elif msg_type.strip().upper()=='MULTICAST':    
                

                grouplen = client.recv(64).decode()
                grouplen = int(grouplen)
                group = client.recv(grouplen).decode()
                group = group.split(' ')

                msg_length=int(client.recv(64).decode())                
                message=client.recv(msg_length).decode()

                # msg=client.recv(1024)
                message+='(Multicast)'
                multicast(message.encode(), group)
            elif msg_type.strip().upper()=='GETKEY':
                msg_length=int(client.recv(64).decode())
                nickname=client.recv(msg_length).decode()
                sender=nickname.split(',')[1]
                reci=nickname.split(',')[0]
                
                # print(reci)
                pu_key=client_keys[reci]
                print('h')
                print(pu_key[0])
                message=f'*,{pu_key[0][0]},{pu_key[0][1]}'.encode()

                print(message)
                client.send(message)
                # unicast(message,)
                
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f'{nickname} left the Network!'.encode())
            nicknames.remove(nickname)
            break

def receive():
    while True:
        client, address = server.accept()

        client.send('NICK'.encode())
        nickname = client.recv(1024).decode()
        client.send('PASSWORD'.encode())
        password = client.recv(1024).decode()

        if password != PASSWORD:
            client.send("Wrong Password".encode())
            client.close()
        else:
            print(f"Connected with {str(address)}")

            nicknames.append(nickname)
            clients.append(client)


            print(f"Nickname of the client is {nickname}!")
            broadcast(f"{nickname} has joined the Network!".encode())
            # client.send('Connected to the server!'.encode())
            
            if key_pool:
                public_key, private_key = key_pool.pop(0)
                client_keys[nickname] = (public_key, private_key)
                client.send(f"#,{public_key[0]},{public_key[1]},{private_key[0]},{private_key[1]},#".encode())
                print(f"Assigned RSA key pair to {nickname}: Public Key: {public_key}, Private Key: {private_key}")
            else:
                client.send("NO_KEYS_AVAILABLE".encode())
                client.close()
                continue

            broadcast(f"{nickname} has joined the Network!\n".encode())
            thread = threading.Thread(target=handle, args=(client,))
            thread.start()



print('Server is listening...')
receive()
