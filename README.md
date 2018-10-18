# IST-Redes
Projecto da cadeira "Redes de Computadores" usando a linguagem Python

This README describes the necessary steps to get your application up and running.

### What is this project? ###

* A server that offer different services to manipulate your text file.
* Version 0.9
* Fully functional Central Server with multiple Working Servers and User applications

### Minimum requirements ###

* Python 2.7 installed on your computer

### How do I get set up? ###

Open your command line and type:

* python user.py [-n hostname] [-p port]
* python cs.py [-p port]
* python ws.py PTC1 ... PTCn [-p wsport] [-n csServer] [-e csPort]

a PTC can be:

WCC - Word Count
UPP - Upper Case
LOW - Lower Case
FLW - Find longest word

Example: 

To run the Central Server on localhost type in your terminal: 

* python cs.py 

if you want to start your central server using another port type: 

* python cs.py -p 58027

The default values for CS are - hostname = localhost, port = 58026

###

To run a Working server on localhost type in your terminal: 

* python ws.py PTC1 ... PTCn (example: python ws.py WCT UPP) 

if you want to start your working server using another port and other CS adress

* python ws.py WCT UPP -p 59001 -n tejo.tecnico.ulisboa.pt -p 58011

The default values for WS are - cs hostname = localhost, cs port = 58026, wsport = 59000

###

To run user application just type in your terminal: 

* python user.py -n tejo.tecnico.ulisboa.pt -p 58011

The default values user are - cs hostname = localhost, cs port = 58026



### Notes ###

* The file you want to request needs to be in the same folder of the code
* You can run various user application at the same time
* The central server can handle multiple WS at the same time
* The maximum characters of a file to be processed is 8192
