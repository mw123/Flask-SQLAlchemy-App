from flask import Flask, json, jsonify, request
from flask_sqlalchemy import SQLAlchemy

class Config(object):
    SQLALCHEMY_DATABASE_URI = 'DATABASE URI HERE'

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

@app.route('/')
def root():
    return 'Player API'


################################## model definitions ################################
MAX_STR_LEN = 250

class Player(db.Model):
    __tablename__ = 'player'
    # player identified by ID, accompanied by a nickname and email address,
    # has number of points, and possess 0 or more items
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(MAX_STR_LEN), nullable=False) # require nickname not empty; max length set
    email = db.Column(db.String, nullable=False) # email required
    points = db.Column(db.Integer, nullable=False)
    
    # guild is parent of player; back_populates in oder to make tracking changes between parent/child easier.
    # guild id could be null since a player doesnt have to belong to a guild
    guild_id = db.Column(db.Integer, db.ForeignKey("guild.id"))
    guild = db.relationship('Guild', lazy="dynamic", back_populates="player_list")
 
    # every player can have more than 1 item.
    # assumption: deletion of a player also deletes associated items
    items = db.relationship('Item', lazy="dynamic", cascade="delete")

    def __init__(self, nickname, email, points):
        self.nickname = nickname
        self.email = email
        self.points = points

    # for logging purpose
    def __repr__(self):
        return "<Player(id=%r,nickname=%r,email=%r,points=%r)>" % (self.id, self.nickname, 
                self.email, self.points)

class Item(db.Model):
    __tablename__ = 'item'
    # an item increases player's skill points if the player is not in a guild. otherwise, if any
    # other player in the same guild has this item, every player gets a decrease in points first.
    # items are identified by unique combination of name and owner_id, whose value is contrained by player id.
    # (no back ref here because item does not need more information of player)
    # assumption: item is created only at the time a player picks it up
    name = db.Column(db.String(MAX_STR_LEN), primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("player.id"), primary_key=True)
    bonus = db.Column(db.Integer, nullable=False)

    def __init__(self, name, owner_id, bonus):
        self.name = name
        self.owner_id = owner_id
        self.bonus = bonus

    def __repr__(self):
        return "<Item(name=%r,owner_id=%r,bonus=%r)>" % (self.name, self.owner_id, self.bonus)

class Guild(db.Model):
    __tablename__ = 'guild'
    # a guild is identified by unique ID and a name, and optionally a country code
    # guild requires 2 or more players
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    country_code = db.Column(db.Integer)

    player_list = db.relationship('Player', lazy="dynamic", back_populates="guild")

    def __init__(self, name, country_code, players_id):
        self.name = name
        self.country_code = country_code

        # add the players that initially form the guild
        for player_id in players_id:
            self.player_list.append(Player.query.get(player_id))

    # compute total number of points in a guild
    def get_total_points():
        sum = 0
        for player in self.player_list:
            sum += player.points

        return sum

    def __repr__(self):
        return "<Guild(id=%r,name=%r,country_code=%r)>" % (self.id, self.name, self.country_code)


######################## Endpoints #############################

# Player
@app.route('/players/', methods = ['GET'])
def player_index():
    return jsonify({'players': Player.query.all()})

@app.route('/players/<int:id>/')
def get_player(id):
    return jsonify({'player': Player.query.get(id)})

@app.route('/players/', methods = ['POST'])
def create_player():
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({'success': 'false'}), 400
    player = Player(data['name'], data['email'], data['points'])
    db.session.add(player)
    db.session.commit()
    return jsonify({'success': 'true'}), 201

@app.route('/players/<int:id>', methods = ['DELETE'])
def delete_player(id):
    if not Player.query.get(id):
        return jsonify({'success': 'false'}), "Player does not exist"
    db.session.delete(Player.query.get(id))
    db.session.commit()
    return jsonify({'success': 'true'})

@app.route('/players/<int:id>', methods = ['PUT'])
def update_player(id):
    data = request.get_json()
    if not data or not Player.query.get(id):
        return jsonify({'success': 'false'}), 400
    player = Player.query.get(id)
    # allow changing player nickname
    if 'name' in data:
        player.name = data['name']
    if 'email' in data and data['email']!=player.email:
        # email change not allowed
        return jsonify({'success': 'false'}), "Cannot change email"
    if 'points' in data:
        player.points = data['points']
    if 'guild_id' in data:
        # this implementation allows player to switch guild
        guild = Guild.query.get(data['guild_id'])
        if guild:
            player.guild = guild
        else:
            return jsonify({'success': 'false'}), "Guild_id does not exist"

    db.session.commit()
    return jsonify({'success': 'true'})
    

# Item
@app.route('/items/', methods = ['GET'])
def item_index():
    return jsonify({'items': Item.query.all()})

# get method not implemented because item is unique to each player

@app.route('/items/', methods = ['POST'])
def create_item():
    data = request.get_json()
    if not data or 'name' not in data or 'owner_id' not in data or
        return jsonify({'success': 'false'}), 400
    # check to make sure player id exists
    player = Player.query.get(data['owner_id'])
    if not player:
        return jsonify({'success': 'false'}), "Player does not exist"        
    
    # check if player belongs to a guild
    if player.guild:
        # if so, every player except current player in the guild get a points decrease
        for guild_player in player.guild.player_list:
            # from problem description, my understanding is that the player who just picked 
            # up the item does not get a decrease in skill points even if he belongs in a guild
            if data['name'] in guild_player.items and guild_player.id != player.id:
                guild_player.points -= data['bonus']
    
    player.points += data['bonus']

    item = Item(data['name'], data['owner_id'], data['bonus'])
    player.items.append(item)

    db.session.add(item)
    db.session.commit()
    return jsonify({'success': 'true'}), 201

# assumption: items exist as long as the player possessing it, so they
# will be deleted only if the player dies; items also have fixed attributes
# therefore, delete and update methods not implemented


# Guild
@app.route('/guilds/', methods = ['GET'])
def guild_index():
    return jsonify({'guilds': Guild.query.all()})

@app.route('/guilds/<int:id>/')
def get_guild(id):
    return jsonify({'guild': Guild.query.get(id), 
                    'total_sp': Guild.query.get(id).get_total_points()})

@app.route('/guilds/', methods = ['POST'])
def create_guild():
    data = request.get_json()
    if not data or 'name' not in data or len(data['players_id'])<2:
        return jsonify({'success': 'false'}), 400
    # make sure two or more players are added
    if len(data['players_id']) < 2:
        return jsonify({'success': 'false'}), "Guild requires 2 or more players" 
    # check players actually exist
    for player_id in data['players_id']:
        if not Player.query.get(player_id):
            return jsonify({'success': 'false'}), "Player does not exist"
    
    if 'country_code' in data:
        country_code = data['country_code']
    else:
        country_code = None
    guild = Guild(data['name'], country_code, data['players_id'])

    db.session.add(guild)
    db.session.commit()
    return jsonify({'success': 'true'}), 201

@app.route('/guilds/<int:id>', methods = ['DELETE'])
def delete_guild():
    if not Guild.query.get(id):
        return jsonify({'success': 'false'}), "Guild does not exist"
    db.session.delete(Guild.query.get(id))
    db.session.commit()
    return jsonify({'success': 'true'})
    
@app.route('/guilds/<int:id>', methods = ['PUT'])
def update_guild(id):
    data = request.get_json()
    # allow changing guild name
    if 'name' in data:
        guild.name = data['name']
    if 'country_code' in data:
        guild.country_code = data['country_code']

    db.session.commit()
    return jsonify({'success': 'true'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
