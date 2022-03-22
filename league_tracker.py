import random
from riotwatcher import LolWatcher, ApiError
from collections import Counter
import numpy as np
import time
import json
import requests
from requests.exceptions import HTTPError


# Riot API Key - Required to access API features
lol_watcher = LolWatcher('RGAPI-ac7d5826-ef0e-4b1d-9c13-01c843849d92')

s12_start_timestamp = 1641549600000 # Milliseconds Unix

# Info not obtainable directly through API
queue_names = {420: 'Ranked Solo', 440: 'Ranked Flex', 450: 'ARAM', 900: 'URF', 840:'Beginner Bots', 850: 'Intermediate Bots',
				400: 'Normal Draft', 430: 'Normal Blind', 700: 'Clash'}	

"""
queues_url = 'https://static.developer.riotgames.com/docs/lol/queues.json'
queue_dict = {}

try: 
	response = requests.get(queues_url)
	response.raise_for_status()

	queues = response.json()

	queue_dict = {x['queueId']: }

except HTTPError as http_err:
   print(f'HTTP error occurred: {http_err}')

except Exception as err:   
    print(f'Other error occurred: {err}')
"""

maps_url = 'https://static.developer.riotgames.com/docs/lol/maps.json'
maps_dict = {}

try: 
	response = requests.get(maps_url)
	response.raise_for_status()

	maps = response.json()

	maps_dict = {x['mapId']:x['mapName'] for x in maps}

except HTTPError as http_err:
   print(f'HTTP error occurred: {http_err}')

except Exception as err:   
    print(f'Other error occurred: {err}')


runes_url = 'https://ddragon.leagueoflegends.com/cdn/12.5.1/data/en_US/runesReforged.json'
runes_dict = {}
rune_keystones = {}
# Rune Details
try: 
	response = requests.get(runes_url)
	response.raise_for_status()

	runes = response.json()

	runes_dict = {x['id']: x for x in runes}	
	rune_keystones = {x['id']: {y['id']: y for y in x['slots'][0]['runes']} for x in runes}
except HTTPError as http_err:
   print(f'HTTP error occurred: {http_err}')

except Exception as err:   
    print(f'Other error occurred: {err}')


# Champ Details
champs_url = 'http://ddragon.leagueoflegends.com/cdn/12.5.1/data/en_US/champion.json'
champs_dict = {}
try: 
	response = requests.get(champs_url)
	response.raise_for_status()

	champs = response.json()
	champs_dict = {int(x['key']): x for x in champs['data'].values()}
except HTTPError as http_err:
   print(f'HTTP error occurred: {http_err}')

except Exception as err:
    print(f'Other error occurred: {err}')

# Item Details
items_url = "https://ddragon.leagueoflegends.com/cdn/12.5.1/data/en_US/item.json"
items_dict = {}

try: 
	response = requests.get(items_url)
	response.raise_for_status()

	items = response.json()
	items_dict = {k:v for k,v in items['data'].items()}

except HTTPError as http_err:
   print(f'HTTP error occurred: {http_err}')

except Exception as err:
    print(f'Other error occurred: {err}')



summs_url = "http://ddragon.leagueoflegends.com/cdn/12.5.1/data/en_US/summoner.json"
summs_dict = {}

try: 
	response = requests.get(summs_url)
	response.raise_for_status()

	summs = response.json()
	summs_dict = { int(x['key']): x for x in summs['data'].values()}

except HTTPError as http_err:
   print(f'HTTP error occurred: {http_err}')

except Exception as err:
    print(f'Other error occurred: {err}')


#print([x['name'] for x in summs_dict.values()])

# Account class instance represents the account searched by user
class Account:

	def __init__(self, server, acc_name):

		self.server = server
		self.acc_name = acc_name

		if self.server in ['euw1', 'eun1', 'ru1', 'tr1']:
			self.region = 'EUROPE'

		elif self.server in ['kr', 'jp1']:
			self.region = 'ASIA'

		else: 
			self.region = 'AMERICAS'

		try:
			self.acc = lol_watcher.summoner.by_name(server, acc_name)

		except ApiError as err: 
			print(err)
			print("Name not found to be associated with an account.")
			self.acc = None

	# Returns profiles details e.g. Summoner Icon ID, name, level, etc.
	def get_profile_details(self):
		return self.acc

	# Takes past time in ms and returns how many seconds/mins/hours/days (depending on time value)
	# ago that was. 
	@staticmethod
	def how_long_ago(t):
		
		if t // 8.64e7 >= 1:
			return '%d Days Ago' % (int(t // 8.64e7))
		elif t // (60*60*1000) >= 1:
			return '%d Hours Ago' % (int(t // (60*60*1000)))
		elif t // (60*1000) >= 1:
			return '%d Minutes Ago' % (int(t // (60*1000)))

		return '%d Seconds Ago' % (int(t//1000))	

	# Return rank for solo and flex queues if available.
	def get_ranked_details(self):
		
		acc_ranked = lol_watcher.league.by_summoner(self.server, self.acc['id'])
		valid_queues = ['RANKED_SOLO_5x5', 'RANKED_FLEX_SR']

		# [Solo, Flex]
		ranks = {}

		for d in acc_ranked:
			if d['queueType'] in valid_queues:			
				# print(d['tier'], d['rank'])
				ranks[d['queueType']] = {}
				ranks[d['queueType']]['rank'] = d['tier']
				ranks[d['queueType']]['division'] = d['rank']
				ranks[d['queueType']]['lp'] = d['leaguePoints']
				ranks[d['queueType']]['wins'] = d['wins']
				ranks[d['queueType']]['losses'] = d['losses']
				ranks[d['queueType']]['wr'] = float("{:.2f}".format((d['wins']/(d['wins'] + d['losses'])*100)))

		return ranks

	# Returns ranked stats for solo and flex queues e.g. KDA, CSM, WR, etc.
	def get_ranked_stats(self, count=20):

		acc_matches = lol_watcher.match.matchlist_by_puuid(self.region, self.acc['puuid'],type='ranked', count=count) 		
		
		champs = {}
		champ_cs = {}
		champ_kda = {}
		champ_ingame_time = {}
		
		champ_winrates = []
		

		for i,m in enumerate(acc_matches): 


			curr_match_info = lol_watcher.match.by_id(self.region, m)['info']
			match_start_timestamp = curr_match_info['gameCreation'] # To ensure we're only grabbing games from current season
		
			# Matches from start of S12 and up
			if match_start_timestamp < s12_start_timestamp:
				break

			for p in curr_match_info['participants']:

				if p['puuid'] == self.acc['puuid']:
					
					# Remake Condition - Game ends in early surrender before normal early surrender condition is met (15 mins)
					if p['gameEndedInEarlySurrender'] and curr_match_info['gameDuration'] <= 240: break

					champ_winrates.append((p['championName'], p['win']))

					# Add new champ to stats
					if p['championName'] not in champs: 
						champs[p['championName']] = 1
						champ_cs[p['championName']] = p['totalMinionsKilled'] + p['neutralMinionsKilled']
						champ_ingame_time[p['championName']] = curr_match_info['gameDuration']
						champ_kda[p['championName']] = [p['kills'], p['deaths'], p['assists']]
					
					# Update champ stats if already played
					else:
						champs[p['championName']] += 1
						champ_cs[p['championName']] += p['totalMinionsKilled'] + p['neutralMinionsKilled'] 
						champ_ingame_time[p['championName']] += curr_match_info['gameDuration']
						champ_kda[p['championName']] = list(map(np.add, champ_kda[p['championName']], (p['kills'], p['deaths'], p['assists'])))


		# Sort champs by most played. 
		champs = dict(sorted(champs.items(), reverse=True, key=lambda x: x[1]))
		
		# Count wins and losses for each champ. 
		wl_record = dict(sorted(Counter(champ_winrates).items()))

		# Win-rates (%) for each champ
		wr_record = {}


		for c in champs.keys():
			
			wins = wl_record.get((c, True), 0)
			losses = wl_record.get((c, False), 0)

			wr_record[c] = float("{:.2f}".format((wins / (wins + losses))*100))


		return (champs, wl_record, wr_record, champ_cs, champ_ingame_time, champ_kda)


	# Returns n most recent games of specified queueType
	# Value queueTypes: ranked, normal, tutorial, tourney
	def get_recent_games(self, start=None, n=10, queueType=None, queueFilter=None):

		acc_matches = lol_watcher.match.matchlist_by_puuid(self.region, self.acc['puuid'], type=queueType, queue=queueFilter,start=start, count=n) 		
		
		recently_played_with = {}
		recent_game_stats = {}

		# List of dict of dicts containing match info
		match_details = []

		for i,m in enumerate(acc_matches):

			curr_match_info = lol_watcher.match.by_id(self.region, m)['info']

			match_start_timestamp = curr_match_info['gameCreation']

			game_length = curr_match_info['gameDuration']
			game_type = queue_names.get(curr_match_info['queueId'], 'Custom')
			#print(curr_match_info['queueId'])
			game_start_timestamp = curr_match_info['gameStartTimestamp']
			ms_since_game = int(time.time())*1000 - (game_start_timestamp + (game_length*1000)) # * 1000 since time.time() returns seconds

			# Matches from start of S12 and up
			if match_start_timestamp < s12_start_timestamp:
				break

			# Global Information e.g. Total Gold, Barons/Dragons killed, etc. 
			objective_details = curr_match_info['teams']

			if len(objective_details) == 2:
				red_team_objectives = {'barons': objective_details[0]['objectives']['baron']['kills'],
									'dragons': objective_details[0]['objectives']['dragon']['kills'],
									'towers': objective_details[0]['objectives']['tower']['kills'],
									'kills': objective_details[0]['objectives']['champion']['kills'],
									'win': 'Victory' if objective_details[0]['win'] else 'Defeat'}
				blue_team_objectives = {'barons': objective_details[1]['objectives']['baron']['kills'],
									'dragons': objective_details[1]['objectives']['dragon']['kills'],
									'towers': objective_details[1]['objectives']['tower']['kills'],
									'kills': objective_details[1]['objectives']['champion']['kills'],
									'win': 'Victory' if objective_details[1]['win'] else 'Defeat'}
			else: 
				blue_team_objectives = None
				red_team_objectives = None

			# Important details regarding each player that will be returned
			player_details = {'player_champs': {}, 'player_kdas': {}, 'player_levels': {}, 'player_cs': {},
								'player_runes': {}, 'player_items': {}, 'player_wards': {},
								'player_totaldamage':{}, 'player_gold': {}, 'player_team': {}, 'player_item_details':{},
								'player_summoner_details':{}}
			
			acc_details = None
			for p in curr_match_info['participants']:

				player_details['player_champs'][p['summonerName']] = p['championName']
				
				player_details['player_kdas'][p['summonerName']] = (p['kills'], p['deaths'], p['assists'], "{:.2f}".format(((p['kills'] + p['assists'])/p['deaths'])) if p['deaths'] > 0 else 'Perfect')

				player_details['player_team'][p['summonerName']] = p['teamId']

				player_details['player_levels'][p['summonerName']] = p['champLevel']
				
				if game_length <= 0:
					game_length = 1

				player_details['player_cs'][p['summonerName']] = (p['totalMinionsKilled'] + p['neutralMinionsKilled'],
																	"{:.2f}".format((p['totalMinionsKilled'] + p['neutralMinionsKilled'])/(game_length/60)))
					
				# Perk Details
				primary = p['perks']['styles'][0]['style']
				secondary = p['perks']['styles'][1]['style']
				
				# Technically possible to not have runes, this safeguards that possiblity. 
				if primary == 0: 
					keystone = 0
					player_details['player_runes'][p['summonerName']] = {'primary': 0, 
																		'secondary': 0}
				else: 
					keystone = p['perks']['styles'][0]['selections'][0]['perk']

					#print(runes_dict.get(primary)['slots'][keystone])

					#print(p['perks'])

					player_details['player_runes'][p['summonerName']] = {'primary': rune_keystones.get(primary,0).get(keystone,0), 
																		'secondary': runes_dict.get(secondary,0)}

				player_details['player_items'][p['summonerName']] = [p['item%d' % i] for i in range(7)] 
				player_details['player_item_details'][p['summonerName']] = [items_dict.get(str(p['item%d' % i]),"0") for i in range(7)]


				player_details['player_summoner_details'][p['summonerName']] = (summs_dict.get(p['summoner1Id'], summs_dict.get(7)),
																					summs_dict.get(p['summoner2Id'], summs_dict.get(6)))

				player_details['player_wards'][p['summonerName']] = (p['detectorWardsPlaced'], p['wardsPlaced'], p['wardsKilled']) 

				player_details['player_totaldamage'][p['summonerName']] = p['totalDamageDealtToChampions']

				player_details['player_gold'][p['summonerName']] = p['goldEarned']

				#player_details['player_ranks'][p['summonerName']] = Account.get_rank(p['summonerName'])

				if p['puuid'] == self.acc['puuid']:
					acc_details = {x:player_details[x][p['summonerName']] for x in player_details.keys()}
					acc_details['result'] = 'Victory' if p['win'] else 'Defeat'
					acc_details['summonerName'] = p['summonerName']


					if acc_details['player_champs'] not in recent_game_stats:
						recent_game_stats[acc_details['player_champs']] = {'in_game_time': game_length, 'cs': acc_details['player_cs'][0], 'kda': list(acc_details['player_kdas'][:3]), 'games_played': 1, 'wins': 1 if p['win'] else 0}
					else: 

						recent_game_stats[acc_details['player_champs']]['in_game_time'] += game_length

						recent_game_stats[acc_details['player_champs']]['cs'] += acc_details['player_cs'][0]

						#x_kda = list(map(lambda x,y: x+y, acc_details['player_kdas'][:3], recent_game_stats[acc_details['player_champs']]['kda'])) 

						recent_game_stats[acc_details['player_champs']]['kda'] = list(map(lambda x,y: x+y, acc_details['player_kdas'][:3],recent_game_stats[acc_details['player_champs']]['kda']))


						recent_game_stats[acc_details['player_champs']]['games_played'] += 1 
						recent_game_stats[acc_details['player_champs']]['wins'] += (1 if p['win'] else 0)
												

			for k,v in player_details['player_team'].items():
				if k != acc_details['summonerName']:
					if v == acc_details['player_team'] and k not in recently_played_with:
						recently_played_with[k] = {'count': 1, 'wins': 1 if acc_details['result'] == 'Victory' else 0}
					elif v == acc_details['player_team']: 
						recently_played_with[k]['count'] += 1
						recently_played_with[k]['wins'] += (1 if acc_details['result'] == 'Victory' else 0)


			# Team Specific stats that cannot be collected from objective_details

			blue_team_gold = red_team_gold = 0
			blue_champs, red_champs = {}, {}
			for k,v in player_details['player_team'].items():

				if v == 100:
					blue_team_gold += player_details['player_gold'][k]
					blue_champs[k] = player_details['player_champs'][k]
				else: 
					red_team_gold += player_details['player_gold'][k]
					red_champs[k] = player_details['player_champs'][k]

			if blue_team_objectives is not None and red_team_objectives is not None:
				blue_team_objectives['gold'] = blue_team_gold
				red_team_objectives['gold'] = red_team_gold
			
			# teamId 100 is Blue Team, 200 is Red Team
			if acc_details['player_team'] == 200: 
				acc_details['player_kp'] = '{:.2f}'.format((acc_details['player_kdas'][0]+acc_details['player_kdas'][2])/red_team_objectives['kills']*100) if (red_team_objectives is not None and red_team_objectives['kills'] > 0) else 'Perfect'  							

			else: 
				acc_details['player_kp'] = '{:.2f}'.format((acc_details['player_kdas'][0]+acc_details['player_kdas'][2])/blue_team_objectives['kills']*100) if (blue_team_objectives is not None and blue_team_objectives['kills'] > 0) else 'Perfect'  							


			player_details['teams'] = [blue_champs, red_champs]

			match_details.append([game_length, Account.how_long_ago(ms_since_game), game_type, acc_details, blue_team_objectives, red_team_objectives, player_details])

		#champs = dict(sorted(champs.items(), reverse=True, key=lambda x: x[1]))



		recently_played_with = dict(sorted(list(recently_played_with.items()), reverse=True, key=lambda x: x[1]['count'])[:10])
		recently_played_with = {k:v for k,v in recently_played_with.items() if v['count'] >= 2}

		recent_game_stats = dict(sorted(list(recent_game_stats.items()), reverse=True, key=lambda x: x[1]['games_played']))
		#print(recent_game_stats)
		return match_details, recent_game_stats, recently_played_with

	@staticmethod
	def ranks_numerical(ranks_1, ranks_2):
		# ranks_1 = [(,),(,),(,),(,),(,)]
		

		ranks_1 = [str(r['solo']).split() if r['solo'] != 'None' else r['flex'].split() for r in ranks_1]
		ranks_2 = [str(r['solo']).split() if r['solo'] != 'None' else r['flex'].split() for r in ranks_2]

		print(ranks_1)
		print(ranks_2)

		tier_map = {'IV': 4, 'III': 3, 'II': 2, 'I':1}
		ranks = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger']


		base = 0.25

		avgs_1 = np.round(np.mean([ranks.index(r[0]) + (1-(tier_map.get(r[1],4)/4)) for r in ranks_1 if r])/ base) * base 
		avgs_2 = np.round(np.mean([ranks.index(r[0]) + (1-(tier_map.get(r[1],4)/4)) for r in ranks_2])/base) * base

		print(avgs_1, avgs_2)

		return



	@staticmethod
	def seconds_to_ingame_time(t):
		mins = t//60
		secs = t%60

		if secs < 10:
			return '%d:0%d' % (mins,secs)
		
		return '%d:%d' % (mins,secs)

	@staticmethod
	def get_rank(acc_name, server):
		acc = lol_watcher.summoner.by_name(server, acc_name)
		acc_rank = lol_watcher.league.by_summoner(server, acc['id'])

		solo_rank, flex_rank = None, None
		acc_level = acc['summonerLevel']

		for r in acc_rank:

			if r['queueType'] == 'RANKED_SOLO_5x5':

				if r['tier'] in ('CHALLENGER', 'GRANDMASTER', 'MASTER'):
					solo_rank = '%s %s' % (r['tier'], str(r['leaguePoints']) + 'LP')

				else: 
					solo_rank = '%s %s' % (r['tier'], r['rank'])	

			elif r['queueType'] == 'RANKED_FLEX_SR':
				
				if r['tier'] in ('CHALLENGER', 'GRANDMASTER', 'MASTER'):
					flex_rank = '%s %s' % (r['tier'], str(r['leaguePoints'])  + 'LP')

				else: 
					flex_rank = '%s %s' % (r['tier'], r['rank'])

		return {'solo': solo_rank, 'flex':flex_rank, 'lvl':acc_level}

	def get_live_details(self):

		try: 
			live_game_info = lol_watcher.spectator.by_summoner(self.server, self.acc['id'])
			
			match_details = {'game_type': queue_names.get(live_game_info['gameQueueConfigId']), 'map': maps_dict.get(live_game_info['mapId']),
								'time_elapsed': '0:00' if live_game_info['gameLength'] <= 0 else Account.seconds_to_ingame_time(live_game_info['gameLength']), 'team_avgs':{}}
			player_details = {'player_champs': {}, 'player_runes': {}, 'player_bans': {}, 'player_ranks': {}, 'blue_team': [], 'red_team': [], 'player_summoner_details':{}}
			print(live_game_info)
			for i,p in enumerate(live_game_info['participants']):

				if p['teamId'] == 100:
					player_details['blue_team'].append(p['summonerName']) 
				else: 
					player_details['red_team'].append(p['summonerName']) 


				player_details['player_champs'][p['summonerName']] = champs_dict.get(p['championId'])['id']

				#player_details['player_runes'][p['summonerName']] = {'primary': runes_dict.get(p['perks']['perkStyle'],0),
				#													'secondary': runes_dict.get(p['perks']['perkSubStyle'],0)}
			
				primary = p['perks']['perkStyle']				
				secondary = p['perks']['perkSubStyle']
				keystone = p['perks']['perkIds'][0]

				player_details['player_runes'][p['summonerName']] = {'primary': rune_keystones.get(primary,0).get(keystone,0), 
																		'secondary': runes_dict.get(secondary,0)}
				
				player_details['player_summoner_details'][p['summonerName']] = (summs_dict.get(p['spell1Id'], summs_dict.get(7)),
																					summs_dict.get(p['spell2Id'], summs_dict.get(6)))

				player_details['player_ranks'][p['summonerName']] = Account.get_rank(p['summonerName'], self.server)

				ban = live_game_info['bannedChampions'][i]['championId']

				if ban > -1:
					player_details['player_bans'][p['summonerName']] = champs_dict.get(ban)['id']
				else: 
					player_details['player_bans'][p['summonerName']] = 'blank'


			return [match_details, player_details]

		except HTTPError as e: 
			print(e)
			

		return

acc = Account('na1','Darzival')
acc.get_recent_games()