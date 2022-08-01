from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

#These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(DBSession) #g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()

"""
-------- Helper methods (feel free to add your own!) -------
"""

def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    with open('server_log.txt', 'a') as log_file:
     log_file.write(json.dumps(d))

"""
---------------- Endpoints ----------------
"""
    
@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True
        if error:
            print( json.dumps(content) )
            log_message(content)
            return jsonify( False )
            
        #Your code here
        #Note that you can access the database session using g.session
        
        # Extract data from content
        
        payload = content.get("payload")
        payload_text = json.dumps(content['payload'])
        sig = content['sig']
        pk = payload.get("sender_pk")
        
        # Create order
        
        order_data = {'sender_pk': payload.get("sender_pk"),
                      'receiver_pk': payload.get("receiver_pk"),
                      'buy_currency': payload.get("buy_currency"),
                      'sell_currency': payload.get("sell_currency"),
                      'buy_amount': payload.get("buy_amount"),
                      'sell_amount': payload.get("sell_amount"),
                      'signature': sig}
        
        new_order_fields = ['sender_pk','receiver_pk','buy_currency','sell_currency','buy_amount','sell_amount','signature']
        new_order = Order(**{f:order_data[f] for f in new_order_fields})

        # Check if order is signed
        
        # Check platform
        if content['payload']['platform'] == 'Ethereum':

            print("Check for Ethereum")
            # Check Ethereum
            eth_encoded_msg = eth_account.messages.encode_defunct(text=payload_text)
            
            if eth_account.Account.recover_message(eth_encoded_msg, signature=sig) == pk:
                g.session.add(new_order)
                print("Gonzalo1")
                g.session.commit()
                return jsonify( True )
            else:
                print("Gonzalo2")
                print(payload_text)
                log_message(payload_text)
                return jsonify( False )
        else:
            # Check Algorand
            print("Check for Algorand")
            if algosdk.util.verify_bytes(payload_text.encode('utf-8'),sig,pk):
                print("Gonzalo3")
                g.session.add(new_order)
                g.session.commit()
                return jsonify( True )                      
            else:
                print("Gonzalo4")
                print(payload_text)
                log_message(payload_text)
                return jsonify( False )                      

@app.route('/order_book')
def order_book():
    
    #Your code here
    #Note that you can access the database session using g.session
    
    print("Checkpoint 1")
    
    a_list = []
    
    for row in g.session.query(Order).all():
        a_list.append({'sender_pk':row.sender_pk,
                       'receiver_pk':row.receiver_pk,
                       'buy_currency':row.buy_currency,
                       'sell_currency':row.sell_currency,
                       'buy_amount':row.buy_amount,
                       'sell_amount':row.sell_amount,
                       'signature': row.signature}
        print("Hello, world")
                     
                      
    
    result = json.dumps({'data' : a_list})
    
    print("Checkpoint 2")
                   
    return jsonify(result)

if __name__ == '__main__':
    app.run(port='5002')
