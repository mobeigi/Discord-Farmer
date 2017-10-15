#!/usr/bin/env python

import sys, os, requests, threading, time, pickle, re
from datetime import datetime, date

accounts = []

DISCORD_API = 'https://discordapp.com/api/'
DELAY = 87000 # 24 hours, 10 minutes
CACHE_MISS_DELAY = 960 # 16 minutes (cache reproduced every 15 minutes)

# Set CWD to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_me(session, token):
    return session.get(DISCORD_API + "/users/@me", headers={'Authorization': token})

# Try to get guilds to see if account is verified
def get_verified(session, token):
    return session.get(DISCORD_API + "/users/@me/guilds", headers={'Authorization': token})
    
def change_username(session, token, new_username, password):
    return session.patch(DISCORD_API + "/users/@me", json={'username': new_username, 'password': password}, headers={'Authorization': token})

def get_username_matching_discrims(session, token):
    # Load pickle
    with open('discrims.pkl', 'rb') as f:
        return pickle.load(f)

def is_token_valid(token):
    if len(token) != 59:
        return False
        
    return True

def is_target_discrim(discrim):
    return discrim <= 10 or discrim in [1111,2222,3333,4444,5555,6666,7777,8888,9999,666,420,1337]

def log_event(email, message):
    _log_to_file(email, message, "log.txt", True)

def log_target(email, message):
    _log_to_file(email, message, "targets.txt", False)

def _log_to_file(email, message, filename, print_to_stdout):
    str_time = datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')
    
    # Log to file
    with open(filename, "a") as myfile:
        myfile.write(f"{str_time} [{email}] {message}\n")

    # Also print log entry to stdout?
    if print_to_stdout:
        print(f"{str_time} [{email}] {message}")

# Main work thread
def work_thread(account):
    while True:
        session = requests.Session()
    
        # Test if account requires verification to proceed (i.e. email or phone)
        resp = get_verified(session, account[2])
        
        if resp.status_code != 200:
            resp = resp.json()
            if resp['code'] == 40002: #You need to verify your account in order to perform this action.
                log_event(account[0], f"Account needs verification with error code {resp['code']}. Ending thread.")
            else:
                log_event(account[0], f"Account needs attention with error code {resp['code']}. Ending thread.")
            
            break
        
        # Get @me
        resp = get_me(session, account[2])
        
        if resp.status_code != 200:
            log_event(account[0], f"Failed to authenticate with error code {resp.status_code}. Ending thread.")
            break
        
        resp = resp.json()
        
        # Fetch parameters
        username = resp['username']
        discrim = resp['discriminator']
        
        log_event(account[0], f"Current Discord: {username}#{discrim}")
        
        # Check if we already target discrim
        if is_target_discrim(int(discrim)):
            log_event(account[0], f"Already has target discrim with discord {username}#{discrim}. Ending thread.")
            break # leave thread
        
        # Get Cached Discrims
        cached_discrims = get_username_matching_discrims(session, account[2])
        same_discrim_usernames = cached_discrims[discrim]
        
        # Remove current username from set
        if username in same_discrim_usernames:
            same_discrim_usernames.remove(username)
        
        # If no matching discrims found, sleep and try again
        if len(same_discrim_usernames) == 0:
            log_event(account[0], f"Found no discriminator in cached discrims. Sleeping for {CACHE_MISS_DELAY} seconds.")
            time.sleep(CACHE_MISS_DELAY)
            continue
        
        # Sort list from longer names to shortner names
        # This makes it less likely the name is 'too common'
        same_discrim_usernames.sort(key = len)
        same_discrim_usernames.reverse()
        
        error_count = 0
        for new_username in same_discrim_usernames:
            
            resp = change_username(session, account[2], new_username, account[1])
            if resp.status_code != 200:
                error_count = error_count + 1
                log_event(account[0], f"Encountered error trying to change username. Error count {error_count}.")
                
                if error_count >= 3:
                    log_event(account[0], "Encountered too many errors. Sleeping now.")
                    break
                
                time.sleep(10)
            else:
                # Successful change
                resp = resp.json()
                username = resp['username']
                discrim = resp['discriminator']
                log_event(account[0], f"Successfully changed Discord to: {username}#{discrim}")
                break
        
        # Check to see if we now have a target discrim
        if is_target_discrim(int(discrim)):            
            log_event(account[0], f"Found target discrim {username}#{discrim}. Ending thread.")
            log_target(account[0], f"Found target discrim {username}#{discrim}. Ending thread.")
            break # leave thread
        
        # Timeout
        log_event(account[0], f"Sleeping for {DELAY} seconds.")
        time.sleep(DELAY)

if __name__ == '__main__':
    log_event("CONSOLE", f"Script Started. Reading input from accounts.txt")
    
    with open('accounts.txt') as f:
        for line in f:
            line = line.rstrip()
            #Ignore blank lines or comments
            if not line or line.startswith('#'):
                continue
            else:
                email, password, token = line.split('\t')
                
                # Soft check token before adding account
                if is_token_valid(token):
                    accounts.append((email, password, token))
                else:
                    log_event(email, f"Invalid token provided.")
    
    log_event("CONSOLE", f"Starting farm with {len(accounts)} account(s) loaded.")
    
    for account in accounts:
        threading.Thread(target=work_thread, args=(account,)).start()
        # Spread out username changes over course of 1 day to avoid IP rate limiting
        time.sleep(86400 / len(accounts))