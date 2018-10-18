# -*- coding: utf-8 -*-
import socket
import sys
import argparse
import os

parser = argparse.ArgumentParser(description='Servidor CS')
#Definição do argumento [-n name] que define o nome da máquina onde o user se vai conectar
parser.add_argument('-n',
	default='localhost',
	type=str,
	help='É o nome da máquina que aloja o servidor CS que se pretende contactar. (default: 127.0.0.1)',
	metavar='CSname',
	dest='name')
#Definição do argumento [-p port] que define a porta onde o servidor vai aguardar conexões
parser.add_argument('-p',
	default=58026,
	type=int,
	help='É o porto bem conhecido no qual o servidor CS que se pretende contactar aceita pedidos por parte de utilizadores. (default: 58026)',
	metavar='CSport',
	dest='port')

args = parser.parse_args()
# IP do servidor CS que se pretende contactar
SERVER_IP = socket.gethostbyname(args.name)
# Porta do servidor CS que se pretende contactar
SERVER_PORT = args.port

# Cria um socket TCP (Cliente do CS)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

fileExcpFlag = 0

# Conecta o socket à porta onde o servidor está listening
server_address = (SERVER_IP, SERVER_PORT)
print 'connecting to %s port %s' % server_address

try:
	sock.connect(server_address)
	print 'Tcp connection established with CS server"\n'
except:
	print 'There is no available central server on %s:%s' %server_address
	sock.close()
	exit()

# Dicionario auxiliar para elaborar a descrição dos file processing tasks disponíveis
tasksDict = {'WCT': 'word count', 'UPP': 'convert to upper case', 'LOW': 'convert to lower case', 'FLW': 'find longest word'}

# Função auxiliar que lista as tasks disponíveis ao user após resposta do CS ao comando list
def printLST(lstReply):
	print "CS reply: " + lstReply + "\n"
	userList = ""
	index = 1
	# Remove o \n do final da string recebida
	tmpString = lstReply[:-1]
	splitList = tmpString.split(' ')
	nl = int(splitList[1])
	tmpList = splitList[2:]
	if (nl <= 0):
		print "There are no available tasks, try again later"
	else:
		for task in tmpList:
			if (task == 'WCT'):
				userList = userList + str(index) + '- ' + 'WCT - ' + tasksDict['WCT'] + '\n'
				index = index + 1;
			elif  (task == 'UPP'):
					userList = userList + str(index) + '- ' + 'UPP - ' + tasksDict['UPP'] + '\n'
					index += 1;
			elif (task == 'LOW'):
					userList = userList + str(index) + '- ' + 'LOW - ' + tasksDict['LOW'] + '\n'
					index += 1;
			elif (task == 'FLW'):
					userList = userList + str(index) + '- ' + 'FLW - ' + tasksDict['FLW'] + '\n'
					index += 1;
	return userList

# Função auxiliar que filtra e processa os inputs do utilizador
def processInput(userInput):
	inputFirstWord = userInput.split(' ')[0]
	# Processa o comando list enviando o comando LST para o CS
	if (inputFirstWord == 'list'):
		try:
			sock.sendall('LST\n')
			lstReply = sock.recv(32)
			print printLST(lstReply)
		except:
			raise socket.error
	# Processa o comando request enviando o comando REQ para o CS
	elif (inputFirstWord == "request"):
		# Faz o split do input em várias variáveis
		if (len(userInput.split(' ')) < 3):
			print 'You request is not correctly formulated. Please use: request PTC filename'
			sock.close()
			exit()
		else:
			originalFileName = userInput.split(' ')[2]
			reqTask = userInput.split(' ')[1]
			# Lê e envia o fichiero dado pelo user
			try:
				data = open(originalFileName, 'r').read()
			except:
				print "Could not read file: " + originalFileName + '. Make sure the name is correct'
				global fileExcpFlag
			# Determina o numero de bytes do ficheiro
			inFileSize = os.path.getsize(originalFileName)
			# Envia o comando REQ para o CS
			try:
				sock.sendall('REQ ' + reqTask + ' ' + str(inFileSize) + ' ' + data + '\n')
				csWsReply = sock.recv(8192)
				if(not csWsReply):
					raise Exception
				#print csWsReply
			except:
				raise socket.error

			if (csWsReply == 'REP EOF\n'):
				print 'The task you requested is not available at the moment. Use list command to see the available ones'
			elif (csWsReply == 'REP ERR\n'):
				print 'The task you requested has a syntax error or does not exist. Use list command to see the available ones '
			else:
				if (reqTask == 'WCT'):
					print '\nNumber of words: ' + str(csWsReply)

				elif (reqTask == 'FLW'):
					print '\nThe longest word is ' + csWsReply.split()[0] + ' and has ' + csWsReply.split()[1] + ' characters'

				elif (reqTask == 'UPP'):
					#UPPdata = csWsReply.split(' ')
					outputFileName = originalFileName[:-4] + '_UPP' + '.txt'
					with open(outputFileName, 'wb') as outputfile:
						outputfile.write(csWsReply)
					print 'received file ' + outputFileName + '\n' + str(os.path.getsize(outputFileName)) + ' Bytes'

				elif (reqTask == 'LOW'):
					#LOWdata = csWsReply.split(' ')
					outputFileName = originalFileName[:-4] + '_LOW' + '.txt'
					with open(outputFileName, 'wb') as outputfile:
						outputfile.write(csWsReply)
					print 'received file ' + outputFileName + '\n' + str(os.path.getsize(outputFileName)) + ' Bytes'

	# Processa o comando exit saindo da aplicação e encerrando as ligações
	elif (inputFirstWord == "exit"):
		sock.sendall('exit')
		sock.close()
		exit()
	else:
		print "Invalid command. Please try again"

	# Pede ao utilizador um comando a enviar ao servidor CS, processando-o de seguida
while 1:
	userInput = raw_input('\n> ')
	try:
		processInput(userInput)
	except socket.error:
		print 'Your message couldnt reach its destination. Your applications is now closed'
		sock.close()
		exit()
