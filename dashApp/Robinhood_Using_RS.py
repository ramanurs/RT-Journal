#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import uuid, requests, urllib
import pandas as pd
import pathlib as path
from datetime import datetime, timezone
from getpass import getpass

class RobinhoodUsingRS:

    endpoints = {
        "accounts": "https://api.robinhood.com/accounts/",
        "dividends": "https://api.robinhood.com/dividends/",
        "documents": "https://api.robinhood.com/documents/",
        "investment_profile":  "https://api.robinhood.com/user/investment_profile/",
        "instruments": "https://api.robinhood.com/instruments/",
        "login": "https://api.robinhood.com/oauth2/token/",
        "logout": "https://api.robinhood.com/oauth2/revoke_token/",
        "markets": "https://api.robinhood.com/markets/",
        "orders": "https://api.robinhood.com/orders/",
        "portfolios": "https://api.robinhood.com/portfolios/",
        "positions": "https://api.robinhood.com/positions/",
        "quotes": "https://api.robinhood.com/quotes/",
        "user": "https://api.robinhood.com/user/",
        "watchlists": "https://api.robinhood.com/watchlists/",
        "optionsInstruments": "https://api.robinhood.com/options/instruments/",
        "optionsOrders":"https://api.robinhood.com/options/orders/",
        "optionsPositions":"https://api.robinhood.com/options/positions/"
    }

    session = None
    headers = None
    auth_token = None
    refresh_token = None
    device_token = ""
    client_id = "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS"
    instrumentsList = {}
    instrumentBasic = {}

    def __init__(self):
        self.session = requests.session()
        try:
            self.session.proxies = urllib.getproxies() #py2
        except:
            self.session.proxies = urllib.request.getproxies() #py3
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en;q=1, fr;q=0.9, de;q=0.8, ja;q=0.7, nl;q=0.6, it;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-Robinhood-API-Version": "1.0.0",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:87.0) Gecko/20100101 Firefox/87.0"
        }
        self.session.headers = self.headers

    def mfa_login(self, data_load,attempt = 3):
        data_load["mfa_code"] = str(input("Input mfa code: "))
        response= self.session.post(self.endpoints['login'],data=data_load) 
        attempt -= 1
        if (response.status_code != requests.codes.ok) and (attempt > 0):
            print("Invalid mfa code: No of Attempts left %s" %attempt)
            return self.mfa_login(data_load, attempt)
        elif response.status_code == requests.codes.ok:
             return response.json()
        else:
            print("Too many attempts for login")
            print("Please restart the kernal and try back login")
            self.session.close()

    def challenge_login(self, data_load,res,attempt = 3):
        challenge_url = ("https://api.robinhood.com/"f"challenge/{res['challenge']['id']}/respond/")
        challenge_load = {
            'response':str(input("Enter RH challenge code sent to you. Challenge Type: SMS : "))}
        challenge_header = {"X-ROBINHOOD-CHALLENGE-RESPONSE-ID": str(res['challenge']['id'])}
        response= self.session.post(
            challenge_url,
            data=challenge_load,
            headers = challenge_header) 
        if (response.status_code != requests.codes.ok) and (attempt > 0):
            print("Invalid code: No of Attempts left %s" %attempt)
            return self.challenge_login(data_load,res, attempt)
        elif response.status_code == requests.codes.ok:
            try:
                return self.session.post(self.endpoints['login'],data=data_load,
                                         headers = challenge_header).json()
            except Exception as e:
                print("Some error occured "+str(e) )
        else:
            print("Too many attempts for login")
            print("Please restart the kernal and try back login")
            self.session.close()

    def login(self, username=None, password=None, attempts = 3):
        self.device_token: str = (str(uuid.uuid4())) 
        while True:
            data_load = {
                    'username' : username if (username and attempts == 3) else str(input("Please Enter User Email Id : ")),
                    'password' : password if (password and attempts == 3) else getpass("Plese Enter Password : "), #str(input("Plese Enter Password : \n")),
                    'grant_type': 'password',
                    'scope' : 'internal',
                    "expires_in": 86400,
                    'client_id': self.client_id,
                    'device_token': self.device_token,
                    #'challenge_type': 'sms',
                    "mfa_code": "889214"
                }
            print("Logging in with %s" %data_load['username'])
            print("logging in with data" %data_load)
            
            res = self.session.post(self.endpoints['login'], data=data_load)
            print("response code: %s" %res.status_code)
            print("response text: %s" %res.text)
            print("response json: %s" %res.json())

            if (res.status_code != requests.codes.ok) and (attempts > 0):
                print("Invalid Username or Password: No of Attempts left %s" %attempts)
                return self.login(username,password, attempts)
            elif res.status_code == requests.codes.ok:
                 break
            res = res.json()
            if 'mfa_required' in res:
                print("Get Autharization code from "+str(res['mfa_type']))
                res = self.mfa_login(data_load)
                break
            elif "challenge" in res:
                res = self.challenge_login(data_load,res)
                break
            elif "detail" or "error" in res:
                attempts -= 1
                print(res)
                if attempts > 0:
                    print("Username or Password Incorrect")
                    print("Reintiating login procedure, Login Attempt Left : %s" %attempts)
                else: 
                    print("THREE Failes Attempts, Closing this session: Restart Terminal or Kernal")
                    self.session.close()
                    return False
        try:
            self.auth_token = res['access_token']
            self.refresh_token = res['refresh_token']
        except Exception as e:
            print(str(e) + "@ login method")
            return res
        self.headers['Authorization'] = 'Bearer ' + self.auth_token
        return True

    def logout(self):
        logout_load = {"client_id": self.client_id, "token": self.auth_token}
        try:
            response = self.session.post(self.endpoints['logout'], data=logout_load)
            print("Login off.....")
            print(response)
            self.headers.pop("Authorization", None)
            print("Successfully Signed Out")
            self.session.close()
            return response
        except Exception as e:
            print(e)
            return False

    def get_url(self,url):
        return self.session.get(url).json()

    def get_account(self):
        return pd.Series(self.session.get(self.endpoints['accounts']).json()['results'][0])

    def get_user(self):
        return self.session.get(self.endpoints['user']).json()

    def get_markets(self):
        return self.session.get(self.endpoints['markets']).json()

    def get_documentsInfo(self):
        response = self.session.get(self.endpoints['documents']).json()
        if response: return pd.DataFrame(pd.DataFrame(response).results.tolist())
        else: return False

    def get_portfolios(self):
        return self.session.get(self.endpoints['portfolios']).json()

    def get_positions(self):
        response =  self.session.get(self.endpoints['positions']).json()
        result = response["results"]
        while response["next"]:
            response = self.session.get(response["next"]).json()
            result += response["results"]
        return result

    def get_optionsPositions(self):
        response =  self.session.get(self.endpoints['optionsPositions']).json()
        result = response["results"]
        while response["next"]:
            response = self.session.get(response["next"]).json()
            result += response["results"]
        return result

    def basicInstrumentSchema(self,obj):
        returnObj = {
            'instrument_id'  : obj['id'],
            'url' : obj['url'],
            'state' : obj['state'],
            'market' : self.session.get(obj["market"]).json()["name"],
            "name" : obj['name'],
            'symbol' : obj['symbol'],
            'country': obj['country'],
            'instrumentType' : obj['type'],
            'splits': obj['splits'],
            'quote' : None if obj['state'] == 'inactive' else self.get_url(obj['quote'])['last_trade_price'],
            'quote_time' : datetime.now()
            }
        return returnObj

    def get_instruments(self , stock = False):
        if stock:
            return self.session.get(self.endpoints['instruments'], params={'query':stock.upper()}).json()
        else:
            return self.session.get(self.endpoints['instruments']).json()

    def instrumentObject(self,url):
        def instrument(url):
            if url in self.instrumentsList.keys():
                    return self.instrumentsList[url]
            else:
                try:
                    res = self.session.get(url).json()
                    if res: self.instrumentsList[url] = res
                    return self.session.get(url).json()
                except Exception as e:
                    print("Error %s at %s" % (e,url))
                    return False
        if isinstance(url, list):
            returnObj = []
            for i in url:
                instrumentObj = instrument(i)
                if instrumentObj: returnObj.append(instrumentObj)
            return returnObj
        else: return instrument(url)

    def get_instrumentBasic(self,url):
        def instrument(url):
            if url in self.instrumentBasic.keys():
                return self.instrumentBasic[url]
            else:
                try:
                    res = self.session.get(url).json()
                    if res:
                        res = self.basicInstrumentSchema(res)
                        self.instrumentBasic[res["url"]] = res
                    return res
                except Exception as e:
                    print("Error %s at %s" % (e,url))
                    return False
        if isinstance(url, list):
            returnObj = []
            for i in url:
                instrumentObj = instrument(i)
                if instrumentObj: returnObj.append(instrumentObj)
            return pd.DataFrame(returnObj).drop_duplicates()
        else: return instrument(url)

    def get_optionsObject(self,url):
        response = self.get_url(url)
        date= datetime.strptime(response["expiration_date"],'%Y-%m-%d').date()
        returnstring = ( "%s %.2f %s %s" %(response["chain_symbol"],
                            float(response["strike_price"]),response["type"].upper(),date) )
        return {"optionName" : returnstring, "state" :response["state"],'strikePrice': response['strike_price'],
                "optionType" :response["type"].upper(), "expDate" : date}

    def get_quotes(self,stock):
        try:
            if isinstance(stock, list):
                url = str(self.endpoints['quotes'] + "?symbols=" + ",".join([i.upper() for i in stock]))
                returnObj ={}
                for i in  self.session.get(url).json()['results']:
                    returnObj[i['symbol']] =  i['last_trade_price']
                print("Showing Recent Prices for Instruments")
                print(pd.Series(returnObj))
                return returnObj
            elif isinstance(stock, str):
                url = str(self.endpoints['quotes'] +stock.upper() + "/")
                return self.session.get(url).json()["last_trade_price"]
        except Exception as e:
            print("Error occured during getting quotes. Most likely Invalid ticker symbol")
            print("Error: "+str(e))
            return False

    def options_owned(self):
        options = self.session.get(self.endpoints['optionsPositions']+'?nonzero=true').json()
        try:
            returnlist = options["results"]
            while options["next"]:
                options = self.session.get(options["next"]).json()
                returnlist = options["results"]
            return [ i for i in returnlist if (float(i['average_price'])*float(i['quantity'])) != 0 ]
        except Exception as e:
            print("Error occured at options_owned method, %s" %e)
            return False

    def positions_owned(self):
        positions = self.session.get(self.endpoints['positions']+'?nonzero=true').json()
        try:
            returnlist = positions["results"]
            while positions["next"]:
                positions = self.session.get(positions["next"]).json()
                returnlist = positions["results"]
            return returnlist
        except Exception as e:
            print("Error occured at postions_owned method, %s" %e)
            return False

    def get_dividends(self):
        response = self.session.get(self.endpoints['dividends'])
        if response:
            response = response.json()  
            tmp_result = response["results"]
            while response["next"]:
                response  = self.session.get(response["next"])
                if response:
                    response = response.json()  
                    tmp_result = tmp_result + response["results"]
            return tmp_result
        else: return response

    def get_optionsOrders(self):
        response = self.session.get(self.endpoints['optionsOrders']).json()
        result = response["results"]
        while response["next"]:
            response = self.session.get(response["next"]).json()
            result += response["results"]
        return result

    def get_orders(self):
        response = self.session.get(self.endpoints['orders']).json()
        result = response["results"]
        while response["next"]:
            response = self.session.get(response["next"]).json()
            result += response["results"]
        return result

    def savePdf(self,url: str):
        try:
            file = path('RH_pdf/%s.pdf' %(url.split("/")[-3]))
            file.write_bytes(self.session.get(url).content)
            print("File Downloaded : %s" %file.name)
            return True
        except Exception as e:
            print("Downloadn error : %s" %e)
            return False

    def downloadPdf(self,pdfType:str='account_statement', start_date = "2000-01-01",
                        end_date = str(datetime.now().date())):
        if pdfType not in ['1099', 'account_statement', 'trade_confirm']:
            pdfType = 'account_statement'
        df = self.get_documentsInfo()
        if not isinstance(df, pd.DataFrame): return False
        df["dateObj"] = [datetime.strptime(d,'%Y-%m-%d').date() for d in df.date.tolist()]
        start_date = datetime.strptime(start_date,'%Y-%m-%d').date()
        end_date = datetime.strptime(end_date,'%Y-%m-%d').date()
        df = df[df["dateObj"].between(start_date,end_date)]
        df = df[df["type"]==pdfType]
        download = df.download_url.tolist()
        if download:
            download_log = {}
            for i in download:
                print(i)
                download_log[i.split("/")[-3]] = self.savePdf(i)
            return download_log
        return False