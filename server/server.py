import random
import paho.mqtt.client as mqtt
import time
import file
import pandas as pd
import csv


class User:
    def __init__(self,n):
        self.name=n
        print("User created: "+n)
        self.game_name=""
        self.hand=[]
        self.score=0
        self.game=None
        self.ready=False

    def exit_game(self):
        self.game_name=""
        self.hand=[]
        self.score=0
        self.game=None
        self.ready=False

class Game:
    def __init__(self,u1,u2,M_c,country_name,country_index_value,country_longevity,country_education,country_GNI):
        self.user1=u1
        self.user2=u2
        self.country_name=country_name
        self.country_index_value=country_index_value
        self.country_longevity=country_longevity
        self.country_education=country_education
        self.country_GNI=country_GNI
        self.MQTT_client=M_c
        self.deck=list(map(str,list(range(1,192))))
        random.shuffle(self.deck)
        self.desks=[]
        self.turn=True
        self.round=0
        self.starter=bool(random.getrandbits(1))
        self.round_of_player=self.starter
        self.game_name=u1.game_name=u2.game_name=u1.name+":"+u2.name
        self.MQTT_client.publish("STC/"+u1.name+"/game_name",self.game_name,2,False)
        #print("STC/"+u1.name+"/game_name")
        self.MQTT_client.publish("STC/"+u2.name+"/game_name",self.game_name,2,False)
        #print("STC/"+u2.name+"/game_name")
        print("name of the game "+ self.game_name)
        #print("deck "+" ".join(self.deck))
        
    def initialize(self):
        self.draw(3)
        self.end_turn()
    def draw(self,i):
        for x in range(i):
            card=self.deck.pop()
            self.user1.hand.append(card)
            self.MQTT_client.publish("STC/"+self.game_name+"/"+"player1_hand",str(card),2,False)
            card=self.deck.pop()
            self.user2.hand.append(card)
            self.MQTT_client.publish("STC/"+self.game_name+"/"+"player2_hand",str(card),2,False)

    def new_desks(self):
        for i in range(random.randint(1,4)):
            self.desks.append([str(random.randint(0,3)),"0","0",str(i)])
            print(",".join(self.desks[i]))
            self.MQTT_client.publish("STC/"+self.game_name+"/"+"desk", ",".join(self.desks[i]), 2, False)

    def process_set_card_desk(self,user,payload):
        desk_number=int(payload.split(",")[0])
        card_number=payload.split(",")[1]
        if user.name==self.user1.name and not self.round_of_player:
            if self.desks[desk_number][1] != "0":
                card_back=self.desks[desk_number][1]
                user.hand.append(card_back)
                self.MQTT_client.publish("STC/"+self.game_name+"/"+"player1_hand",card_back,2,False)
            self.desks[desk_number][1]=card_number
            user.hand.remove(card_number)
            self.MQTT_client.publish("STC/"+self.game_name+"/"+"remove_card_hand1",str(card_number),2,False)
        elif user.name==self.user2.name and self.round_of_player:
            if self.desks[desk_number][2] != "0":
                card_back=self.desks[desk_number][2]
                user.hand.append(card_back)
                self.MQTT_client.publish("STC/"+self.game_name+"/"+"player2_hand",card_back,2,False)
            self.desks[desk_number][2]=card_number
            user.hand.remove(card_number)
            self.MQTT_client.publish("STC/"+self.game_name+"/"+"remove_card_hand2",str(card_number),2,False)
        self.MQTT_client.publish("STC/"+self.game_name+"/set_desk_card",",".join(self.desks[desk_number]), 2,False)
    def process_return_card_desk(self,user,payload):
        desk_number=int(payload.split(",")[0])
        
        if user.name==self.user1.name and not self.round_of_player:
            if self.desks[desk_number][1] != "0":
                card_back=self.desks[desk_number][1]
                user.hand.append(card_back)
                self.desks[desk_number][1]="0"
                self.MQTT_client.publish("STC/"+self.game_name+"/"+"player1_hand",str(card_back),2,False)
        elif user.name==self.user2.name and self.round_of_player:
            if self.desks[desk_number][2] != "0":
                card_back=self.desks[desk_number][2]
                user.hand.append(card_back)
                self.desks[desk_number][2]="0"
                self.MQTT_client.publish("STC/"+self.game_name+"/"+"player2_hand",str(card_back),2,False)
        
        self.MQTT_client.publish("STC/"+self.game_name+"/set_desk_card",",".join(self.desks[desk_number]), 2,False)

    def end_turn(self):
        self.turn=not self.turn
        self.round_of_player=not self.round_of_player
        if not self.turn:
            self.round=self.round+1
            self.round_of_player=not self.round_of_player
            self.MQTT_client.publish("STC/"+self.game_name+"/round",str(self.round))
            self.win_round()
            self.desks=[]
            self.new_desks()
            self.draw(2)
        self.MQTT_client.publish("STC/"+self.game_name+"/turn_of_player",str(self.round_of_player), 2,False)
        print("user1hand:"+",".join(self.user1.hand))
        print("user2hand:"+",".join(self.user2.hand))

    def compare(self,desk):
        data=[]
        if desk[0]=="0":
            data=self.country_index_value
        elif desk[0]=="1":
            data=self.country_longevity
        elif desk[0]=="2":
            data=self.country_education
        elif desk[0]=="3":
            data=self.country_GNI
        
        if data[int(desk[1])]<data[int(desk[2])]:
            print(self.user2.name+" wins. "+self.country_name[int(desk[1])]+": "+str(data[int(desk[1])])+", "+self.country_name[int(desk[2])]+": "+str(data[int(desk[2])]))
            return 1
        elif data[int(desk[1])]>data[int(desk[2])]:
            print(self.user1.name+" wins. "+self.country_name[int(desk[1])]+": "+str(data[int(desk[1])])+", "+self.country_name[int(desk[2])]+": "+str(data[int(desk[2])]))
            return -1
        elif desk[1]=="0" and desk[2]=="0" :
            print("None put any card, none wins.")
            return 0
        elif desk[1]=="0":
            print(self.user1.name+" did not put any card, "+self.user2.name+ " wins.")
            return 1
        elif desk[2]=="0":
            print(self.user2.name+" did not put any card, "+self.user1.name+ " wins.")
            return -1
        elif data[int(desk[1])]==data[int(desk[2])]:
            print("Tie game, none wins, "+self.country_name[int(desk[1])]+": "+str(data[int(desk[1])])+", "+self.country_name[int(desk[2])]+": "+str(data[int(desk[2])]))
            return 0
            

    def win_round(self):
        points=0
        for desk in self.desks:
            points=points+self.compare(desk)
        print("Points: "+str(points))
        if points<0 :
            self.user1.score=self.user1.score+1
            print("Winner: "+self.user1.name)
            self.MQTT_client.publish("STC/"+self.game_name+"/round_winner",self.user1.name,2,False)
        elif points>0 :
            self.user2.score=self.user2.score+1
            print("Winner: "+self.user2.name)
            self.MQTT_client.publish("STC/"+self.game_name+"/round_winner",self.user2.name,2,False)
        print("Scores: "+str(self.user1.score)+","+str(self.user2.score))
        if points ==0:
            self.MQTT_client.publish("STC/"+self.game_name+"/round_winner","Tie game",2,False)
        self.MQTT_client.publish("STC/"+self.game_name+"/scores",str(self.user1.score)+","+str(self.user2.score),2,False)
        self.win_game()
    def win_game(self):
        print("Scores: "+str(self.user1.score)+","+str(self.user2.score))
        if self.user1.score==5:
            self.MQTT_client.publish("STC/"+self.game_name+"/game_winner",self.user1.name,2,False)
            print(self.user1.name+" wins! "+self.user1.name+" has reached the 5 points first!")
            self.user1.exit_game()
            self.user2.exit_game()
        elif self.user2.score==5:
            self.MQTT_client.publish("STC/"+self.game_name+"/game_winner",self.user2.name,2,False)
            print(self.user1.name+" wins! "+self.user1.name+" has reached the 5 points first!")
            self.user1.exit_game()
            self.user2.exit_game()
        



        

class Server:

    def __init__(self,url,port):
        self.MQTT_client = mqtt.Client("Server")
        self.MQTT_client.on_connect = self.on_connect
        self.MQTT_client.on_message = self.on_message
        self.MQTT_client.on_publish = self.on_publish
        self.MQTT_client.on_disconnect = self.on_disconnect
        self.MQTT_client.on_unsubscribe = self.on_unsubscribe
        self.MQTT_client.on_subscribe = self.on_subscribe
        self.topic = None
        self.payload = None
        self.matching_users=[]
        self.logged_users=[]
        self.games=[]
        self.MQTT_client.connect(url,port)
        self.MQTT_client.publish("STATUS","OK",2,True)
        self.MQTT_client.subscribe("CTS/#",2)
        #self.MQTT_client.loop_start()
        self.country_name=[""]
        self.country_index_value=[0]
        self.country_longevity=[0]
        self.country_education=[0]
        self.country_GNI=[0]
        self.get_HDI_fIle()
    def get_HDI_fIle(self):
        file.runcmd("find  . -name 'HDR*' -exec rm {} \;")
        file.runcmd("wget https://hdr.undp.org/sites/default/files/2021-22_HDR/HDR21-22_Statistical_Annex_HDI_Table.xlsx", verbose = True)
        df = pd.read_excel(io="HDR21-22_Statistical_Annex_HDI_Table.xlsx" )
        df.to_csv('hdi.csv', index=False)
        with open('hdi.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile)
            for row in spamreader:
                if row[0].isdigit():
                    self.country_name.append(row[1])
                    self.country_index_value.append(float(row[2]))
                    self.country_longevity.append(float(row[4]))
                    self.country_education.append(float(row[6]))
                    self.country_GNI.append(int(row[10].replace(".","")))

        print("index value card 1:"+str(self.country_index_value[1]))
        
    def server_loop(self):
        while True:
            self.MQTT_client.loop(10)
            if(self.topic==None):
                continue
            topics=self.topic.split("/")
            username=topics[1]
            user=None
            for u in self.logged_users:
                if u.name==username:
                    user=u

            if topics[2] =="login" and self.payload=="login":
                self.MQTT_client.publish("STC/"+username+"/logged","logged",2,False)
                print(username+"logged")
                if user not in self.logged_users:
                    self.logged_users.append(User(username))
                elif user in self.logged_users and user.game:
                    self.MQTT_client.publish("STC/"+username+"/game_name",user.game_name,2,False)
            elif topics[2] =="matching" and self.payload=="matching" and user in self.logged_users:
                #if self.matching_users:
                #    print("processing second user: "+user.name+" matching_user:"+","+self.matching_users[0].name)
                if len(self.matching_users)==0:
                    self.matching_users.append(user)
                    print(username+"matching")
                elif user!=self.matching_users[0]:
                    print(username+" and "+self.matching_users[0].name+" matched")
                    game=Game(self.matching_users[0],user,self.MQTT_client,self.country_name,self.country_index_value,self.country_longevity,self.country_education,self.country_GNI)
                    self.games.append(game)
                    self.matching_users[0].game=user.game=game
                    self.matching_users=[]
            elif topics[2] =="waiting" and self.payload=="waiting":
                if user in matching_users:
                    matching_users.remove(user)
            elif topics[2] =="ready" and self.payload=="ready":
                user.ready=True
                if user.game.user1.ready and user.game.user2.ready:
                    user.game.initialize()
            elif topics[2]=="set_card_desk":
                user.game.process_set_card_desk(user,self.payload)
            elif topics[2]=="return_card_desk":
                user.game.process_return_card_desk(user,self.payload)
            elif topics[2]=="end_turn" and self.payload=="end_turn":
                user.game.end_turn()
            self.topic=self.payload=None
                

    def connect_server_to_borker(self, url, port):
        self.MQTT_client.connect(url, port)

    def on_connect(self, client, userdata, flags, rc):
        print("client  connected with result code: " + str(rc))

    def on_message(self, client, userdata, msg):
        self.topic = msg.topic
        self.payload = str(msg.payload.decode("utf-8"))
        print(msg.topic + ", " + str(msg.payload.decode("utf-8")))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("On Subscribed: qos = %d" % granted_qos)
        pass

    def on_unsubscribe(self, client, userdata, mid, granted_qos):
        print("On unSubscribed: qos = %d" % granted_qos)
        pass

    def on_publish(self, client, userdata, mid):
        #time.sleep(100)
        print("On publishing: mid = " + str(mid))
        pass

    def on_disconnect(self, client, userdata, rc):
        print("Unexpected disconnection rc = " + str(rc))
        pass

server=Server("52.148.250.153",1883)
server.server_loop()
