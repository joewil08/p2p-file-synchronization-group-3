
# THIS FILE IS SIMILAR TO MESSAGE FORWARDING >> ONCE THIS FILE IS COMPLETED, DELETE message_forwarding.py

list_of_messages = {}
from peer import peers_in_network


#TODO
#create a socket to handle messaging

def reply_to_message():
    '''this method will be used to reply to a message sent by a peer'''

    #TODO get message from user
    message = "" 
    #TODO get sender_id from user and use sender_id to get IP,PORT# in peers_in_network
    sender_id = "" 
    
    #TODO --> finish the method implementation
    pass



def listen_for_messages():
    '''
    this method will be used to listen to incoming messages sent by peers
    SHOULD BE DONE IN THE BACKGROUND SILENTLY (no print statements unless for testing)
    '''
    #TODO
    pass


def broadcast_message():
    '''this method will be used to send a message to all peers in network'''

    message = input("Enter message to send to all users in network:") 

    #TODO --> send message to all peers in network
    pass

def handle_upcoming_message():
    ''''
    save the message to the list of messages so that users can viwe them later
    save it in the format ->  
        {
        "Valery-10.1.10.60:50002": "I would like to download a file from your trusted list", 
        "Mark-10.1.10.97:50002": "Hi"
        }
    '''
    #TODO
    pass

def display_messages():
    #TODO
    pass