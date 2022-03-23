from flask import Flask, render_template, url_for, request, redirect, jsonify, session
import league_tracker
from riotwatcher import LolWatcher, ApiError
from time import sleep
from flask_sqlalchemy import SQLAlchemy
from collections import Counter
import numpy as np
import json
import html
import ast

lol_watcher = LolWatcher('RGAPI-f409d893-be65-4be5-b87d-ae4ab4cc7e71')

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


@app.route('/', methods=['POST', 'GET'])
def home():
	
	if request.method == 'POST':
		if request.form['ps']:
			acc_name = request.form['ps']
			acc_server = request.form['server-select']
			return redirect(url_for('profile', prof=acc_name, server=acc_server))
		else:
			return render_template('index.html')
	else: 
		return render_template('index.html')


@app.route('/news', methods=['POST','GET'])
def news(server='na1'):

	if request.method == 'POST':

		if request.form['ss']:
			new_acc_name = request.form['ss']
			new_acc_server = request.form['server-select']
			return redirect(url_for('profile', prof=new_acc_name, server=new_acc_server))	
		else: 
			return redirect(request.url)
	else: 
		return render_template('news.html', server=server)



@app.route('/profile/<server>/<prof>', methods=['POST', 'GET'])
def profile(prof, server='na1'):

	if request.method == 'POST':
		if request.form['ss']:
			new_acc_name = request.form['ss']
			new_acc_server = request.form['server-select']
			return redirect(url_for('profile', prof=new_acc_name, server=new_acc_server))	 
		else:
			return redirect(request.url)
	# Prevents an unknown issue from occuring
	elif prof == 'favicon.ico': 
		return ''

	else: 
		
		acc = league_tracker.Account(server, prof)
		
		if acc.acc is None:
			return render_template('not_found.html', name=prof, server=server)

		else: 	
				session['num_matches_displayed'] = 10
	
				acc_details = acc.get_profile_details()
				ranked_details = acc.get_ranked_details()
				recent_game_details = acc.get_recent_games()
				
				recent_games = recent_game_details[0]
	
				recent_game_stats = recent_game_details[1]

				# Getting relevant statistics
				champs_played = {k:v['games_played'] for k,v in recent_game_stats.items()}
				wl_records = {k: {'wins':v['wins'], 'losses':v['games_played']-v['wins']} for k,v in recent_game_stats.items()}
				wr_records = {k:float("{:.2f}".format((v['wins']/v['games_played'])*100)) for k,v in recent_game_stats.items()}
				cs_records = {k:v['cs'] for k,v in recent_game_stats.items()}
				in_game_time_records = {k:v['in_game_time'] for k,v in recent_game_stats.items()}
				kda_records = {k: v['kda'] for k,v in recent_game_stats.items()}
	
				played_with = recent_game_details[2]
				
				# The way this is done is really unnecessary; could just have used jinja.
				if ranked_details == {}:
	
					return render_template('profile.html', icon=acc_details['profileIconId'], name=acc_details['name']
										, lvl=acc_details['summonerLevel'], solo_rank='UNRANKED', flex_rank='UNRANKED',
											champs_played=list(champs_played.keys()),
											games_played=champs_played, 
											in_game_time=in_game_time_records, 
											avg_cs=cs_records,
											kda=kda_records,
											wl=wl_records, 
											wr=wr_records,
											matches=recent_games,
											recent_game_stats=recent_game_stats, 
											played_with=played_with, 
											server=server)
	
				elif ranked_details.get('RANKED_SOLO_5x5') is not None and ranked_details.get('RANKED_FLEX_SR') is not None:

					return render_template('profile.html', icon=acc_details['profileIconId'], name=acc_details['name']
										,lvl=acc_details['summonerLevel'], solo_rank=ranked_details['RANKED_SOLO_5x5']['rank'],
											solo_division=ranked_details['RANKED_SOLO_5x5']['division'],
											solo_lp=ranked_details['RANKED_SOLO_5x5']['lp'],
											solo_wins=ranked_details['RANKED_SOLO_5x5']['wins'],
											solo_losses=ranked_details['RANKED_SOLO_5x5']['losses'],
											solo_wr=ranked_details['RANKED_SOLO_5x5']['wr'],
											flex_rank=ranked_details['RANKED_FLEX_SR']['rank'],
											flex_division=ranked_details['RANKED_FLEX_SR']['division'],
											flex_lp=ranked_details['RANKED_FLEX_SR']['lp'],
											flex_wins=ranked_details['RANKED_FLEX_SR']['wins'],
											flex_losses=ranked_details['RANKED_FLEX_SR']['losses'],
											flex_wr=ranked_details['RANKED_FLEX_SR']['wr'],
											champs_played=list(champs_played.keys()),
											games_played=champs_played, 
											in_game_time=in_game_time_records, 
											avg_cs=cs_records,
											kda=kda_records,
											wl=wl_records, 
											wr=wr_records,
											matches=recent_games,
											recent_game_stats=recent_game_stats, 
											played_with=played_with,server=server)
	
				elif ranked_details.get('RANKED_SOLO_5x5') is not None:

					return render_template('profile.html', icon=acc_details['profileIconId'], name=acc_details['name']
										,lvl=acc_details['summonerLevel'], flex_rank='UNRANKED', solo_rank=ranked_details['RANKED_SOLO_5x5']['rank'],
											solo_division=ranked_details['RANKED_SOLO_5x5']['division'],
											solo_lp=ranked_details['RANKED_SOLO_5x5']['lp'],
											solo_wins=ranked_details['RANKED_SOLO_5x5']['wins'],
											solo_losses=ranked_details['RANKED_SOLO_5x5']['losses'],
											solo_wr=ranked_details['RANKED_SOLO_5x5']['wr'],
											champs_played=list(champs_played.keys()),
											games_played=champs_played, 
											in_game_time=in_game_time_records, 
											avg_cs=cs_records,
											kda=kda_records,
											wl=wl_records, 
											wr=wr_records,
											matches=recent_games,
											recent_game_stats=recent_game_stats, 
											played_with=played_with,server=server)
	
				else: 

					return render_template('profile.html', icon=acc_details['profileIconId'], name=acc_details['name']
										,lvl=acc_details['summonerLevel'], solo_rank='UNRANKED', flex_rank=ranked_details['RANKED_FLEX_SR']['rank'],
											flex_division=ranked_details['RANKED_FLEX_SR']['division'],
											flex_lp=ranked_details['RANKED_FLEX_SR']['lp'],
											flex_wins=ranked_details['RANKED_FLEX_SR']['wins'],
											flex_losses=ranked_details['RANKED_FLEX_SR']['losses'],
											flex_wr=ranked_details['RANKED_FLEX_SR']['wr'],
											champs_played=list(champs_played.keys()),
											games_played=champs_played, 
											in_game_time=in_game_time_records, 
											avg_cs=cs_records,
											kda=kda_records,
											wl=wl_records, 
											wr=wr_records,
											matches=recent_games,
											recent_game_stats=recent_game_stats, 
										played_with=played_with,server=server)


@app.route('/profile/<server>/<prof>/live', methods=['POST', 'GET'])
def live_game(prof, server):
	
	if request.method == 'POST':

		if request.form['ss']:
			new_acc_name = request.form['ss']
			new_acc_server = request.form['server-select']
			return redirect(url_for('profile', prof=new_acc_name, server=new_acc_server))	

		else: 
			return redirect(request.url)
	else: 
		acc = league_tracker.Account(server, prof)

		live = acc.get_live_details()

		return render_template('live.html', name=prof, details=live, server=server)

queue_map = {'ARAM': 'normal', 'Ranked': 'ranked', 'Normal': 'normal', 'Clash': 'ranked', 'All': None}

def merge_game_stats(s1, s2):
	ret = {}
	for k in s1.keys():
		ret[k] = {}
		if k in s2:
			ret[k]['in_game_time'] = s1[k]['in_game_time'] + s2[k]['in_game_time']
			ret[k]['cs'] = s1[k]['cs'] + s2[k]['cs']
			ret[k]['kda'] = list(map(np.add, s1[k]['kda'], s2[k]['kda']))
			ret[k]['games_played'] = s1[k]['games_played'] + s2[k]['games_played']
			ret[k]['wins'] = s1[k]['wins'] + s2[k]['wins']
		
		else: 
			ret[k] = s1[k]

	for k in s2.keys():
		if k not in ret: 
			ret[k] = s2[k]

	return ret
 
@app.route('/update_match_history', methods=['GET','POST'])
def update_match_history(): 
	
	acc_name = html.unescape(request.values.get('name'))
	acc_server = request.values.get('server')
	queue = request.values.get('queue')

	queue_filter = None
	if queue == 'ARAM':
		queue_filter = 450

	elif queue == 'Clash':
		queue_filter = 700

	elif queue == 'Normal':
		queue_filter = 400

	acc = league_tracker.Account(acc_server, acc_name)
	
	new_get_recent_games = acc.get_recent_games(start=session['num_matches_displayed'], queueType=queue_map.get(queue), queueFilter=queue_filter)

	old_matches = ast.literal_eval(html.unescape(request.values.get('matches')))
	new_matches = new_get_recent_games[0]
	

	matches = old_matches + new_matches

	old_recent_game_stats = ast.literal_eval(html.unescape(request.values.get('recent_game_stats')))
	new_recent_game_stats = new_get_recent_games[1]

	recent_game_stats = merge_game_stats(old_recent_game_stats, new_recent_game_stats)
	recent_game_stats = dict(sorted(list(recent_game_stats.items()), reverse=True, key=lambda x: x[1]['games_played']))
	
	session['num_matches_displayed'] += 10
	
	return jsonify('', render_template('updated_match_history_model.html', matches=matches, name=acc_name, server=acc_server, recent_game_stats=recent_game_stats))

@app.route('/update_stats', methods=['GET','POST'])
def update_stats(): 
	recent_game_stats = ast.literal_eval(html.unescape(request.values.get('recent_game_stats')))

	champs_played = {k:v['games_played'] for k,v in recent_game_stats.items()}
	wl_records = {k: {'wins':v['wins'], 'losses':v['games_played']-v['wins']} for k,v in recent_game_stats.items()}
	wr_records = {k:float("{:.2f}".format((v['wins']/v['games_played'])*100)) for k,v in recent_game_stats.items()}
	cs_records = {k:v['cs'] for k,v in recent_game_stats.items()}
	in_game_time_records = {k:v['in_game_time'] for k,v in recent_game_stats.items()}
	kda_records = {k: v['kda'] for k,v in recent_game_stats.items()}

	total_games = sum(champs_played.values())
	return jsonify('', render_template('updated_ranked_stats_model.html', total_games=total_games,champs_played=list(champs_played.keys()), games_played=champs_played, in_game_time=in_game_time_records,
			avg_cs=cs_records, kda=kda_records, wl=wl_records, wr=wr_records))

@app.route('/update_queue', methods=['GET', 'POST'])
def update_queue():
	acc_name = html.unescape(request.values.get('name'))
	acc_server = request.values.get('server')

	acc = league_tracker.Account(acc_server, acc_name)

	queue = request.values.get('queue')
	
	# queue values: ARAM, Ranked, Normal, Clash, All

	old_matches = ast.literal_eval(html.unescape(request.values.get('matches')))

	retained = []

	if queue is not None:
		
		for m in old_matches:

			if queue_map.get(m[2].split()[0]) == queue:

				retained.append(m)


	games_to_collect = 10 - len(retained)

	queue_filter = None
	if queue == 'ARAM':
		queue_filter = 450

	elif queue == 'Clash':
		queue_filter = 700

	elif queue == 'Normal':
		queue_filter = 400


	new_get_recent_games = acc.get_recent_games(start=len(retained), n=games_to_collect, queueType=queue_map.get(queue), queueFilter=queue_filter)
	
	new_matches = new_get_recent_games[0]
	recent_game_stats = new_get_recent_games[1]

	matches = retained + new_matches
	session['num_matches_displayed'] = 10

	return jsonify('', render_template('updated_match_history_model.html', matches=matches, name=acc_name, server=acc_server, recent_game_stats=recent_game_stats))
