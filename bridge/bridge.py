from firebase_admin.firestore import client
from services.db_service import DatabaseService
from serial.tools import list_ports
import serial
import random
from constants import  DISPENSER_ID, DEFAULT_RATION
from datetime import datetime
                                                                                                                                                                             
class Bridge:
    def __init__(self):
        self.ser = None
        self.port_name = None
        self.client = None
        self.inbuffer = []
        

    def set_client(self, client):
        self.client = client

    def setup_serial(self):
        print('List of available ports: ')

        ports = list_ports.comports()
        for port in ports:
            print('--> ' + port.device + port.description)
            if 'com' in port.description.lower():
                self.port_name = port.device

        if self.port_name is not None:
            print('Connecting to ' + self.port_name + '...')
            self.ser = serial.Serial(self.port_name, timeout=0)
            print('Connected with success!')
        else:
            print('No available ports!')


    def write(self, data):
        self.ser.write(data.encode())


    def loop(self):
        print('bridge thread!')

        # infinite loop
        while (True):
            #look for a byte from serial
            if self.ser.in_waiting>0:
                # data available from the serial port
                lastchar=self.ser.read(1)


                if lastchar==b'\xfe': #EOL
                    self.inbuffer.append(lastchar)
                    #print("\nAnimale avvicinato o stanno per finire croccantini!!!!!!!!!")
                    #print('verifico che l\' animale abbia ancora razione disponibile!')
                    print("su seriale: ")
                    print(self.inbuffer)
                    self.useData()
                    self.inbuffer =[]
                else:
                    # append
                    self.inbuffer.append (lastchar)

    def useData(self):
        animals = self.client.get_user_animals()

        # I have received a line from the serial port. I can use it
        print('controllo i DATI')
        if len(self.inbuffer)<3:   # at least header, size, footer
            print('minore di 3')
            return False
        # split parts
        if self.inbuffer[0] != b'\xff':
            print('il primo non è giusto')
            return False

        command = int.from_bytes(self.inbuffer[1], byteorder='little')
        print(command)
        if command == 1:
            print("\nAnimale avvicinato!!!!!")
            print('faccio verifica tramite il client')
            #faccio tutte le verfiche del caso tramite il client
            
            collar_id = random.choice(animals)
            print(collar_id)
            name = self.client.get_nameAnimal_fromCollar(collar_id)
            print(name)

            is_available = self.client.is_available(collar_id)
            if is_available:
                print('erogazione in corso')
                self.write('1')
                #a questo punto tolgo 30 dalla razione dell'animale
                avvicinato = True
                self.client.update_available_ration(collar_id, 30, avvicinato)

                # DA INSERIRE DOVE METTIAMO ACK RICEVUTO CORRETTAMENTE
                # SE VOGLIAMO POI FARE LA PREDIZIONE PER QUANDO SI AVVICINERA'
                #qnt = self.client.get_available_ration(collar_id)
                #self.client.add_prediction(collar_id, qnt, DISPENSER_ID )

                return True
            else:
                print('erogazione non avvenuta')
                return False
            
        else:
            if command == 2:
                print('ricevuto ack da arduino!')
                print("Ha erogato correttamente")
                
                
            else:
                if command == 6: 
                    print('si stanno esaurendo i croccantini!!!')
                    self.client.update_FoodStateDispenser()
                else:
                    if command==7:
                        print('il dispenser è rifornito')
                        self.client.update_FoodStateDispenser()
                    else:
                        print('qualcosa è andato storto')
                        return False

            
