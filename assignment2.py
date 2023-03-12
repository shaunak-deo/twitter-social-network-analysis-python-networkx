import twitter
import sys
import time
from urllib.error import URLError
from http.client import BadStatusLine

from functools import partial
from sys import maxsize as maxint
import operator # For using operators such as itemgetter(Getting item from iterable object)

import networkx as nx # For creating the graph
import matplotlib.pyplot as plt # For creating visualization

#Authentication keys required for accessing Twitter APIs and then using them to get access to Twitter APIs

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
OAUTH_TOKEN = ''
OAUTH_TOKEN_SECRET = ''

auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                           CONSUMER_KEY, CONSUMER_SECRET)

twitter_api = twitter.Twitter(auth=auth)
print(twitter_api)

#Got this function from twitter cookbook
def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw): 
    
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
    
        if wait_period > 3600: # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e
    
        # See https://developer.twitter.com/en/docs/basics/response-codes
        # for common codes
    
        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429: 
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'                  .format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function
    
    wait_period = 2 
    error_count = 0 

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0 
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise

#Got this function from twitter cookbook
def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    # Must have either screen_name or user_id
    assert (screen_name != None) != (user_id != None), "Must have screen_name or user_id, but not both"

    # See http://bit.ly/2GcjKJP and http://bit.ly/2rFz90N for details
    # on API parameters

    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids,
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids,
                                count=5000)

    friends_ids, followers_ids = [], []

    for twitter_api_func, limit, ids, label in [
        [get_friends_ids, friends_limit, friends_ids, "friends"],
        [get_followers_ids, followers_limit, followers_ids, "followers"]
    ]:

        if limit == 0: continue

        cursor = -1
        while cursor != 0:

            # Use make_twitter_request via the partially bound callable...
            if screen_name:
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else:  # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']

            print('Fetched {0} total {1} ids for {2}'.format(len(ids), label, (user_id or screen_name)),
                  file=sys.stderr)

            # XXX: You may want to store data during each iteration to provide an 
            # an additional layer of protection from exceptional circumstances

            if len(ids) >= limit or response is None:
                break

    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]

#Modified Function from twitter Cookbook
#A function to crawl the followers of a given Twitter user
def crawl_followers(twitter_api, screen_name):
    # Retrieve the friends and followers of the given Twitter user
    friends_ids, followers_ids = get_friends_followers_ids(twitter_api, screen_name, friends_limit=5000,
                                                           followers_limit=5000)

    # Find the reciprocal friends of the user
    reciprocal_friends = list(set(friends_ids).intersection(followers_ids))[0:15] 

    # Retrieving user info for the reciprocal friends
    reciprocalfriends_userinfo = make_twitter_request(twitter_api.users.lookup, user_id=reciprocal_friends)

    # Create a dictionary to store the screen name and followers count of the reciprocal friends
    reciprocalfriends_info = {}

    # Check if the user info is not None and add the screen name and followers count of the reciprocal friends to the dictionary
    if reciprocalfriends_userinfo is not None:
        for i in reciprocalfriends_userinfo:
            reciprocalfriends_info[i['screen_name']] = i['followers_count']

    # Sort the reciprocal friends in descending order of followers count and return the top 5 screen names
    sorted_reciprocalfriends = dict(sorted(reciprocalfriends_info.items(), key=operator.itemgetter(1), reverse=True))
    return list(sorted_reciprocalfriends.keys())[0:5]

#Creating an instance of a NetworkX graph
G = nx.Graph()
screen_name = "shaunakdeo" #Setting the initial screen name
friends = crawl_followers(twitter_api, screen_name) 

users = friends
G.add_node(screen_name)

#Adding the top 5 reciprocal friends of the initial screen name as nodes to the graph and creating an edge between each of them and the initial screen name
for user in friends:
    G.add_node(user)
    G.add_edge(screen_name, user)

# Crawling the followers of the top 5 reciprocal friends in order to get more nodes for the graph
for i in range(20):
    user = users[i]
    #Retrieving top 5 reciprocal friends for each of the new users
    new_users = crawl_followers(twitter_api, user)
    #Adding the new users to the list of all users
    users += new_users

    #Adding the new users as nodes to the graph and creating an edge between each new user and the original user who followed them
    for new in new_users:
        G.add_node(new)
        G.add_edge(user, new)

print("Name of users nodes:", users)
print("Number of nodes:", len(users) + 1)

# Network graph
nx.draw(G, with_labels=True, font_weight='bold')

# Output txt file to write the program output

#Creating a text file to write the program output
f = open("output.txt", "w")
f.write("Social Media Mining and Data Mining Assingment 2 \n")
f.write("Average distance of network = " + str(nx.average_shortest_path_length(G)) + "\n")
f.write("Average diameter of network = " + str(nx.diameter(G)) + "\n")
f.write("Number of nodes = " + str(len(users) + 1) + "\n")
f.write("Number of Edges = " + str(G.number_of_edges()))
f.close()

#Saving the graph as a PNG image file
nx.draw(G)
plt.savefig("graph.png")