# twitter-social-network-analysis-python-networkx
This repository contains code for Twitter Social Network Analysis using Python and NetworkX. The program retrieves friends and followers, identifies reciprocal friends, creates a social network graph, and calculates the diameter and average distance of the resulting network.

Getting Started
Prerequisites
You need to have Python 3.x installed on your system along with the following packages:

  python-twitter
  networkx
  matplotlib

You can install these packages using pip:

  pip install python-twitter networkx matplotlib

Usage

Replace the authentication keys for the Twitter API in the code (CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, and OAUTH_TOKEN_SECRET) with your own keys. You can obtain these keys by creating a Twitter developer account and creating a new app.
Set the screen_name variable to the Twitter username for which you want to analyze the social network.

Run the code using the following command:

python twitter_social_network.py

The program will output the network size (in terms of numbers of nodes & edges), average distance, and diameter of the social network. It will also save an image file of the social network graph (graph.png) and the program output to a file (output.txt).
