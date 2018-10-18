# -*- coding: utf-8 -*-
import select
import Queue
import socket
import sys
import argparse
import errno
import os

parser = argparse.ArgumentParser(description='Servidor CS')
#Definição do argumento [-p port] que define a porta onde o servidor vai aguardar conexões
parser.add_argument('-p',
	default=58026,
	type=int,
	help='É o porto bem conhecido no qual o servidor CS que se pretende contactar aceita pedidos por parte de utilizadores. (default: 58026)',
	metavar='CSport',
	dest='port')

args = parser.parse_args()

# Lista todos os servidores WS. Cada posição é uma lista de IP's
# Pos 0 - Servidores que processam WCT
# Pos 1 - Servidores que processam UPP
# Pos 2 - Servidores que processam LOW
# Pos 3 - Servidores que processam FLW
wsAddrList = [[],[],[],[]]
udpAddrList = []

SERVER_IP = ''   # Localhost
SERVER_PORT = args.port # Porta do servidor

# Cria um socket TCP
TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#print 'TCP Socket created'
TCPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Cria um socket UDP
UDPsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#print 'UDP socket created'

# Torna os sockets não bloqueantes para funcionar com a função select
TCPsocket.setblocking(0)
UDPsocket.setblocking(0)

# Cria o socket TCP cliente
#TCPclientSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
UDPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Inicialização da variavel a atribuir como numero de ficheiro
baseNumber = 100
# Inicialização da variavel de incremento nos fragmentos de ficheiro
fragIncr = 10

# Função auxiliar que percorre a lista de servidores e verifica quais as tasks disponiveis
# Retorna: uma string com o conjunto de tasks disponiveis
def getTasks():
	tasksList = ''
	if (wsAddrList[0]):
		tasksList = tasksList + 'WCT '
	if (wsAddrList[1]):
		tasksList = tasksList + 'UPP '
	if (wsAddrList[2]):
		tasksList = tasksList + 'LOW '
	if (wsAddrList[3]):
		tasksList = tasksList + 'FLW '
	return tasksList[:-1]

# Função auxiliar que devolve o número de tasks disponiveis na lista de servidores
def getNumTasks():
	numTasks = 0
	for n in range(0,4):
		if (wsAddrList[n]):
			numTasks += 1
	return numTasks

# Função auxiliar que devolve o index correspondente à task pedida na lista de servidores
def getTaskIndex(reqTask):
	#wsAddrListIndex = 0
	if (reqTask == 'WCT'):
		wsAddrListIndex = 0
	elif (reqTask == 'UPP'):
		wsAddrListIndex = 1
	elif (reqTask == 'LOW'):
		wsAddrListIndex = 2
	elif (reqTask == 'FLW'):
		wsAddrListIndex = 3
	return wsAddrListIndex

# Função auxiliar que devolve o numero de servidores disponiveis para a task passada em argumento
def getNumServers(reqTask):
	listPos = getTaskIndex(reqTask)
	return len(wsAddrList[listPos])

# Função auxiliar que devolve o numero total de tasks disponiveis em todos os WS
def getTasksNumber():
	total = 0
	for taskL in wsAddrList:
		if(taskL):
			total += len(taskL)
	return total

# Função auxiliar que verifica se a task que o user pretende aplicar ao ficheiro é válida
def isValidTask (task):
	if (task == 'WCT' or task == 'UPP' or task == 'LOW' or task == 'FLW'):
		return True
	else:
		return False

# Função auxiliar que valida se as task passadas como argumento na criação do WS são validas
def validateTasks(availableTasks):
	for t in availableTasks:
		if (t == 'WCT' or t == 'UPP' or t == 'LOW' or t == 'FLW'):
			pass
		else:
			return False
	return True

# Função auxiliar que actualiza o ficheiro file_processing_tasks.txt quando um novo WS se regista ou se desliga
def updateFPTfile():
	with open('file_processing_tasks.txt', 'wb') as fptFile:
		index = 0
		for taskList in wsAddrList:
			if(taskList):
				if (index == 0):
					for addrList in taskList:
						fptFile.write('WCT ' + str(addrList[0]) + ' ' + str(addrList[1])  + '\n')
				if (index == 1):
					for addrList in taskList:
						fptFile.write('UPP ' + str(addrList[0]) + ' ' + str(addrList[1]) + '\n')
				if (index == 2):
					for addrList in taskList:
						fptFile.write('LOW ' + str(addrList[0]) + ' ' + str(addrList[1]) + '\n')
				if (index == 3):
					for addrList in taskList:
						fptFile.write('FLW ' + str(addrList[0]) + ' ' + str(addrList[1]) + '\n')
			index += 1

# Função auxiliar que conta o número de linhas de um ficheiro passado no argumento
def countLines(inputFile):
	with open(inputFile) as inFile:
		count = sum(1 for line in inFile)
	return count

# Função auxiliar que devolve uma lista com as tasks disponiveis no ficheiro file_processing_tasks.txt
def fptToList():
		fptList = [[],[],[],[]]
		with open('file_processing_tasks.txt', 'r') as tmpFpt:
			for line in tmpFpt:
				lineSplit = line.split()
				if (lineSplit[0] == 'WCT'):
					fptList[0].append((lineSplit[1],int(lineSplit[2])))
				if (lineSplit[0] == 'UPP'):
					fptList[1].append((lineSplit[1],int(lineSplit[2])))
				if (lineSplit[0] == 'LOW'):
					fptList[2].append((lineSplit[1],int(lineSplit[2])))
				if (lineSplit[0] == 'FLW'):
					fptList[3].append((lineSplit[1],int(lineSplit[2])))
			return fptList

# Função que actualiza em memória as tasks disponiveis de acordo com o ficheiro file_processing_tasks.txt
def updateWsAddr():
	#print 'WSaddrList: ' + str(wsAddrList)
	fptLines = countLines('file_processing_tasks.txt')
	numbOfTasks = getTasksNumber()
	global wsAddrList
	if (fptLines != numbOfTasks):
		print 'Lista no ficheiro: ' + str(fptToList()) + '\n'
		print 'Lista na memoria: ' + str(wsAddrList) + '\n'
		wsAddrList = fptToList()
		print 'Lista final: ' + str(wsAddrList) + '\n'

# Função que fragmenta o ficheiro requerido pelo user consoante o número de servidores a enviar
def fragmentFile(inputPath, numServers):
	fragIncr = 1
	numberOfLines = countLines(inputPath)
	fragFileName = str(baseNumber) + str(fragIncr)

	if (numServers > numberOfLines):
		with open(inputPath) as inputFile:
			frag = [open('cs_frag_files/' + fragFileName + '%d.txt' % i , 'w') for i in range(numServers)]
			for i, line in enumerate(inputFile):
				frag[i % numServers].write(line)
			for t in frag:
				t.close()
	else:
		linesPerFile = int(numberOfLines / numServers) + (numberOfLines % numServers > 0)      # 20 lines per file
		outputBase = 'output' # output.1.txt, output.2.txt, etc.

		input = open(inputPath, 'r')
		count = 0
		fragN = 0
		dest = None
		for line in input:
			if count % linesPerFile == 0:
				if dest: dest.close()
				dest = open('cs_frag_files/' + fragFileName + str(fragN) + '.txt', 'w')
				fragN += 1
			dest.write(line)
			count += 1
		if (fragN < numServers):
			for frg in range(fragN, numServers):
				ip2 = open(fragFileName + str(fragN) + '.txt', 'w')
				fragN += 1

# Função que concatena as respostas REP do WS para os vários fragmentos enviados
def concREPcmd(reqTask, REPlist, numServers):
	if (reqTask == 'WCT'):
		concData = 0
		for i in range(numServers):
			REPsplit = REPlist[i].split()
			concData = int(concData) + int(REPsplit[3])
		return 'REP R ' + str(len(str(concData))) + ' ' + str(concData) + '\n'

	if (reqTask == 'FLW'):
		concLongest = 0
		longestW = ''
		for i in range(numServers):

			REPsplit = REPlist[i].split()
			if (int(REPsplit[4]) > concLongest):
				concLongest = REPsplit[4]
				longestW = REPsplit[3]
		return 'REP R ' + str(len(REPsplit[3]) + len(str(concLongest))) + ' ' + longestW  + ' ' + str(concLongest) +  '\n'

	if (reqTask == 'UPP'):
		concUpp = ''
		for i in range(numServers):
			REPsplit = REPlist[i].split(' ', 3)
			concUpp = concUpp + REPsplit[3]
		return 'REP F ' + str(len(str(concUpp))) + ' ' + str(concUpp)

	if (reqTask == 'LOW'):
		concLow = ''
		for i in range(numServers):
			REPsplit = REPlist[i].split(' ', 3)
			concLow = concLow + REPsplit[3]
		return 'REP F ' + str(len(str(concLow))) + ' ' + str(concLow)

# Função que processa toda a informação para enviar o comando WRQ para todos os servidores disponiveis para a task pedida
def sendWrq(reqTask):
	sockList = []
	if not os.path.exists('input_files/'):
		os.makedirs('input_files/')
	if not os.path.exists('cs_frag_files/'):
		os.makedirs('cs_frag_files/')
	inputPath = 'input_files/' + str(baseNumber) + '.txt'
	inputFile = open(inputPath, 'r').read()
	inputFileSize = os.path.getsize(inputPath)
	numberOfLines = countLines(inputPath)
	fragFileNumber = str(baseNumber) + str(1)
	REPlist = []
	concData = 0
	updateWsAddr()
	numServers = getNumServers(reqTask)
	# Processa se existirem vários serivodres disponiveis com a task pretendida
	if (numServers > 1):
		fragFileName = str(baseNumber) + str(1)
		for sock in range(numServers):
			newSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sockList.append(newSock)
			fragmentFile(inputPath, numServers)
		for s in range(numServers):
			fragFileName = fragFileNumber + '%d.txt' % s
			fragData = open('cs_frag_files/' + fragFileName, 'r').read()
			fragFileSize = os.path.getsize('cs_frag_files/' + fragFileName)
			wrqMsg = 'WRQ ' + reqTask + ' ' + fragFileName + ' ' + str(fragFileSize) + ' ' + fragData
			WSaddr = wsAddrList[getTaskIndex(reqTask)][s]
			#print 'WSaddr: ' + str(WSaddr)
			sockList[s].connect(WSaddr)
			sockList[s].sendall(wrqMsg)

			wsReply = sockList[s].recv(8192)
			REPlist.append(wsReply)
			sockList[s].close()

		REPcmd = concREPcmd(reqTask, REPlist, numServers)
		return REPcmd

	# Processa se só existir um servidor disponivel com a task pretendida
	if (numServers == 1):
		fragIncrm = 10
		fragFileName = str(baseNumber) + str(fragIncrm)
		fragFilePath = fragFileName + '.txt'
		fragIncrm += 1
		with open('cs_frag_files/' + fragFilePath, 'wb') as outputFragment:
			outputFragment.write(inputFile)
		wrqMsg = "WRQ " + reqTask + ' ' + fragFilePath + ' ' +  str(inputFileSize) + ' ' + inputFile
		WSaddr = wsAddrList[getTaskIndex(reqTask)][0]
		newSock = ''
		newSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print 'WS address: ' + str(WSaddr)
		newSock.connect(WSaddr)
		newSock.sendall(wrqMsg)
		wsReply = newSock.recv(8192)
		newSock.shutdown(socket.SHUT_RDWR)
		newSock.close()
		return wsReply

	else:
		print '\nThere are no available servers at the moment. Please reconnect\n'

# Função que processa os comandos recebidos vindos do user
def processInput(userInput):
	splittedInput = userInput.split(' ')
	command = splittedInput[0]
	# Processa o comando list enviado pelo user
	if (userInput == 'LST\n'):
		print 'List request: ' + client_address[0] + ' ' + str(client_address[1])

		# Verifica se a lista de servidores em memória esta actualizada, comparando-a com a do ficheiro
		updateWsAddr()
		lstReply = 'FPT ' + str(getNumTasks()) + ' ' + getTasks() + '\n'
		connection.sendall(lstReply)
	# Processa o comando request enviado pelo user
	if (command == "REQ"):
		reqTask = splittedInput[1]
		if isValidTask(reqTask):

			print 'A user sent: ' + userInput
			tIndex = getTaskIndex(reqTask)
			updateWsAddr()
			if (not wsAddrList[tIndex]):
				connection.sendall('REP EOF\n')
			else:
				global baseNumber
				# Cria o ficheiro com os dados recebidos do user para a pasta input_files
				if not os.path.exists('input_files/'):
					os.makedirs('input_files/')
				pathName = 'input_files/' + str(baseNumber) + '.txt'
				data = userInput.split(' ', 3)[3]
				with open(pathName, 'wb') as outputFile:
					outputFile.write(data[:-1])
				# Envia mensagem WRQ para o WS
				wsReply = sendWrq(reqTask)
				baseNumber += 1
				# Recebe a resposta REP do WS
				if (reqTask == 'WCT'):
					splitWsReply = wsReply.split()
					connection.sendall(splitWsReply[3])
				elif (reqTask == 'FLW'):
					splitWsReply = wsReply.split()
					connection.sendall(splitWsReply[3] + ' ' + splitWsReply[4])
				elif (reqTask == 'UPP'):
					fileData = wsReply.split(' ', 3)[3]
					connection.sendall(str(fileData))
				elif (reqTask == 'LOW'):
					fileData = wsReply.split(' ', 3)[3]
					connection.sendall(str(fileData))
		else:
			connection.sendall('REP ERR\n')
			print 'The task you required (' + (reqTask) + ") doesn't exist. Please try again"
	# Processa o comando exit enviado pelo user
	elif (userInput == 'exit'):
		connection.close()
		inputs.remove(connection)
		print "Connection closed. User closed the application"

#Faz o bind ao porto UDP (WS-CS)
try:
	UDPsocket.bind((SERVER_IP, SERVER_PORT))
except socket.error as msg:
	print 'UDP socket bind failed. Error Code : ' + str(msg[0]) + ' Message' + msg[1]
	sys.exit()
print 'UDP connection created'

#Faz o bind ao port TCP (User-CS)
try:
	TCPsocket.bind((SERVER_IP, SERVER_PORT))
except socket.error as msg:
	print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
	sys.exit()
print 'TCP connection created'

#Inicia o listening a novas conexões TCP
TCPsocket.listen(10)
# Lista de sockets que esperamos ler quando receberem uma ligação
inputs = [TCPsocket, UDPsocket]
# Lista de sockets que esperamos escrever
outputs = []

while inputs:
	try:
		# Aguarda até que pelo menos um socket receba algo
		print '\nAwaiting for a TCP or UDP connection...\n'
		readable, writable, exceptional = select.select(inputs, outputs, inputs)
		# A lista readable contém os sockets que receberam algo
		for s in readable:
			# Processa quando o socket TCP recebe algo
			if s is TCPsocket:
				connection, client_address = TCPsocket.accept()
				print 'Connected with ' + client_address[0] + ':' + str(client_address[1])
				connection.setblocking(0)
				inputs.append(connection)
				# Efectua um fork sempre que uma ligação com o user é establecida
				pid = os.fork()
				if pid == 0:
					TCPsocket.close()
					UDPsocket.close()
					inputs.remove(TCPsocket)
					inputs.remove(UDPsocket)
				else:
					connection.close()
					inputs.remove(connection)

			# Esta condição é executada quando o socket UDP recebe uma ligação
			elif s is UDPsocket:
					# As linhas seguintes dividem as palavras do comando recebido do WS em várias variáveis
					wsMsg = UDPsocket.recvfrom(128)
					print 'UDP message received: ' + wsMsg[0] + ' from: ' + str(wsMsg[1])
					wsMsgCmd = wsMsg[0].split(' ')[0]
					SplitwsMsg = wsMsg[0].split(' ')
					wsClientAdress = wsMsg[1]
					wsServerAdress = (SplitwsMsg[-2], int(SplitwsMsg[-1][:-1]))  # wsServerAdress = wsAdress =
					# Procede ao Unregister do servidor WS, removendo as respectivas task da lista geral (wsAddrList)
					if (wsMsgCmd == 'UNR'):
						#Remove ip da lista
						pos = 0
						for i in wsAddrList:
							for tuplo in i:
								if (tuplo == wsServerAdress):
									wsAddrList[pos].remove(tuplo)
							pos += 1
						print '\n-' + str(SplitwsMsg[1]) + str(SplitwsMsg[1]) + '\n'
						print wsAddrList
						UDPsocket.sendto('UNR OK\n', wsClientAdress)
						updateFPTfile()
					# Procede ao registo do servidor WS no CS
					if (wsMsgCmd == 'REG'):
						# Verifica se o nome das tasks são válidas, devolvendo RAK ERR caso contrário
						wsInputTasks = SplitwsMsg[1:-2]
						if (validateTasks(wsInputTasks)):
							for validTask in wsInputTasks:
								if (validTask == 'WCT'):
									wsAddrList[0].append(wsServerAdress)
								elif (validTask == 'UPP'):
									wsAddrList[1].append(wsServerAdress)
								elif (validTask == 'LOW'):
									wsAddrList[2].append(wsServerAdress)
								elif (validTask == 'FLW'):
									wsAddrList[3].append(wsServerAdress)
							UDPsocket.sendto('RAK OK\n', wsClientAdress)
							udpAddrList.append(wsClientAdress)
							# Esta mensagem é impressa quando o WS se regista com sucesso
							print '+' + wsMsg[0][4:]
							# Actualiza o ficheiro file_processing_tasks.txt
							updateFPTfile()

						else:
							UDPsocket.sendto('RAK ERR\n', wsClientAdress)
							print 'WS registration Error: Invalid Sintax'

			# Se o socket TCP receber algo numa ligação TCP já activa, é executado o código abaixo
			elif s is connection:

				userInput = connection.recv(8192)
				if userInput:
					#Aguarda pelo envio de um comando por parte do cliente processando-o de seguida
					processInput(userInput)
					# Ao não receber mais dados na ligação TCP, é encerrada a conexão
				else:
					print 'closing' + client_address
					# Interrompe a escuta de ligações em sockets a espera de escrita
					if connection in outputs:
						outputs.remove(s)
					inputs.remove(s)
					connection.close()

	except KeyboardInterrupt:
					if (udpAddrList):
						unrSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						for addr in udpAddrList:
							unrSocket.sendto('Central server is now offline, this WS is now disconnected\n', addr)
					print 'You pressed CTRL+C. This Central server and all connected WS are now offline\n'
					if (len(inputs) > 2):
						connection.close()
					sys.exit()
