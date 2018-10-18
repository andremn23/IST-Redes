# -*- coding: utf-8 -*-
import socket
import sys
import argparse
import signal
import os
import select

parser = argparse.ArgumentParser(description='Servidor WS')

parser.add_argument('-p', # Port do WS
	default=59000,
	type=int,
	help='. (default: 59000)',
	metavar='WSport',
	dest='WSport')

parser.add_argument('-n', # Hostname do CS
	default='localhost',
	type=str,
	help='É o nome da máquina que aloja o servidor CS que se pretende contactar. (default: 127.0.0.1)',
	metavar='CSname',
	dest='CSname')

parser.add_argument('-e', # Port do CS
	default=58026,
	type=int,
	help='É o porto bem conhecido no qual o servidor CS que se pretende contactar aceita pedidos por parte de utilizadores. (default: 58026)',
	metavar='CSport',
	dest='CSport')

parser.add_argument('inputTasks', nargs='+')
args = parser.parse_args()

CS_IP =  args.CSname # Hostname do Central Server a conectar. Default: localhost
CS_PORT = args.CSport # Porta do Central Server
IPWS = socket.gethostbyname('localhost') #Ip do Working server
portWS = args.WSport # Porta do Working Server
inputTasks = args.inputTasks # Lista que contém as tasks recebidas como argumento na inicialização do servidor WS

# Cria o socket UDP (cliente)
socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#print 'UDP socket created'

# Cria o socket TCP (servidor)
socketTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#print 'TCP socket created'

socketTCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Faz o bind do socket TCP (servidor)
try:
	socketTCP.bind((IPWS, portWS))
except socket.error as msg:
	print 'TCP Bind failed. Error Code : ' + str(msg[0]) + ' ' + msg[1]
	print 'There is another WS running using this port'
	socketTCP.close()
	exit()

# Função que aplica a file processing task: WCT
def WCTtask(pathName):
	word_count = 0
	with open(pathName, 'r') as inf:
		for line in inf:
			words = line.split()
			word_count += len(words)
	return word_count

# Função que aplica a file processing task: UPP
def UPPtask(pathname, fileName):
	outputPath = 'output_files/' + fileName
	inputFile = open(pathname, 'r')
	content = inputFile.read()
	with open(outputPath, 'wb') as outputFile:
		outputFile.write(content.upper())

# Função que aplica a file processing task: LOW
def LOWtask(pathName, fileName):
	outputPath = 'output_files/' + fileName
	inputFile = open(pathName, 'r')
	content = inputFile.read()
	with open(outputPath, 'wb') as outputFile:
		outputFile.write(content.lower())

# Função que aplica a file processing task: FLW
def FLWtask(pathName):
	longest_size = 0
	longest_word = ''
	with open(pathName, 'r') as inf:
		for line in inf:
			words = line.split()
			for word in words:
				if (len(word) > longest_size):
					longest_size = len(word)
					longest_word = word
	return longest_word + ' ' + str(longest_size)

# Converte uma lista de tasks para string
def fptToString(availableTasks):
	fptString = ""
	for task in availableTasks:
		fptString = fptString + " " + task
	return fptString

# Procede ao envio do comando de registo (REG) para o CS
try:
	wsReg = 'REG' + fptToString(inputTasks) + " " +  str(IPWS) + " " + str(portWS) + '\n'
	socketUDP.sendto(wsReg, (CS_IP, CS_PORT))
	socketUDP.settimeout(5.0)
	csReply = socketUDP.recv(16)
	print csReply
	# ACEPT
	if (csReply == 'RAK ERR\n'):
		socketUDP.close()
		sys.exit()
except socket.timeout:
	print 'Impossible to register this server. This host cant reach destination. Try again later'
	socketUDP.close()
	sys.exit()
except:
	print 'Impossible to register this server. Sintax error. Please try again'
	socketUDP.close()
	sys.exit()

socketTCP.listen(10)
print 'Working Server waiting requests on: ' + str((IPWS, portWS)) + '\n'
totalWrqMsg = ''
receivedCount = 0

# Lista de inputs para o select, sendo adicionados os sockets que pretendemos ler
inputs = []
outputs = []
inputs.append(socketUDP)
inputs.append(socketTCP)

while True:

	try:

		readable, writable, exceptional = select.select(inputs, outputs, inputs)
		for s in readable:
			# Processa quando o socket UDP recebe algo do CS após estar registado
			if s is socketUDP:
				socketUDP.settimeout(None)
				shutdownMsg = socketUDP.recv(64)
				if (shutdownMsg):
					print shutdownMsg
					socketUDP.close()
					socketTCP.close()
					exit()
			# Processa quando o socket TCP recebe algo
			elif s is socketTCP:
				csConnection, cs_address = socketTCP.accept()
				wrqMsg = csConnection.recv(8192)
				splitWrq = wrqMsg.split(' ')
				printWrq = splitWrq[1] + ': ' + splitWrq[2] + ' (' + splitWrq[3] + ') Bytes'
				print "New Request -> " + printWrq
				# Processa o comando WRQ recebido
				reqTask = splitWrq[1]
				fileName = splitWrq[2]
				# Define o caminho onde será guardado o ficheiro recebido do CS
				if not os.path.exists('input_files/'):
					os.makedirs('input_files/')
				pathName = 'input_files/' + fileName #+ '.txt'
				if not os.path.exists('output_files/'):
					os.makedirs('output_files/')
				outPathName = 'output_files/' + fileName
				wsReply = ''
				# Passa-se apenas o conteudo do ficheiro para data
				data = wrqMsg.split(' ', 4)[4]
				with open(pathName, 'wb') as inputFragment:
					inputFragment.write(data)
				# Define as mensagens REP a enviar consoante a task
				if (reqTask == 'WCT'):
					wordCount = str(WCTtask(pathName))
					wsReply = 'REP R ' + str(len(wordCount)) + ' ' + wordCount + '\n' #o

				elif (reqTask == 'UPP'):
					UPPtask(pathName, fileName)
					outFile = open(outPathName, 'r')
					outContent = outFile.read()
					wsReply = 'REP R ' + str(len(outContent)) + ' ' + outContent

				elif (reqTask == 'LOW'):
					LOWtask(pathName, fileName)
					outFile = open(outPathName, 'r')
					outContent = outFile.read()
					wsReply = 'REP R ' + str(len(outContent)) + ' ' + outContent

				elif (reqTask == 'FLW'):
					longestWord = FLWtask(pathName)
					wsReply = 'REP R ' + str(len(longestWord)) + ' ' + longestWord + '\n'

				csConnection.sendall(str(wsReply))

	# Apanha o sinal CTRL+C e encerra as ligaçõe e o servidor
	except KeyboardInterrupt:
		socketTCP.close()
		unrMsg = 'UNR ' +  str(IPWS) + " " + str(portWS) + '\n'
		socketUDP.sendto(unrMsg, (CS_IP, CS_PORT))
		try:
			unrOk = socketUDP.recv(64)
		except:
			print '\nYou pressed CTRL+C. Unregistration not executed because central server is offline'
			socketUDP.close()
			sys.exit()
		print unrOk
		socketUDP.close()
		print "You closed this working server. CTRL+C Pressed\n"
		sys.exit()
