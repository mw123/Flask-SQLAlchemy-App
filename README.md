# REST API Using Flask-SQLAlchemy 

Player API
==========

Background
----------

In this exercise, I built a simple REST API. The purpose of the API is to manage the players, guilds and items of some game. The objects are described below.

### Players

Players are identified by a unique ID, and provide a nickname and an email address when they sign up. They have a specific number of skill points, and they may possess zero or more items.

### Guilds

A guild consists of a team of two or more players. All guilds have a unique ID and a name, and optionally a country code.

### Items

Items are special bonuses which the player encounters as they progress through the game, which can increase the player's skill points by a certain amount. If the player is not in a guild when they pick up an item, it simply increases their skill points. 

However, a special rule applies if a player is in a guild when they pick up an item: if anyone else in the guild has the same item, the skill points of the players with that item are decreased by the same amount first.


Software Requirements:
----------------------
- Python release: 3.6
- Application framework: Flask
- Object-relational mapper: SQLAlchemy


## Endpoints

The API has endpoints with the following functionality:

1. create, update and delete a player
2. create, update and delete a guild
3. create, update and delete an item
4. add a player to a guild
5. remove a player from a guild
6. add an item to a player
7. calculate the total number of skill points in a guild

The API accepts JSON objects as the request body. For example, a `POST` to the endpoint to add a player to a guild might look like

```
{
    "player_id": <UUID>,
    "guild_id": <UUID>
}
```

The endpoints handle errors and return HTTP status codes appropriately. If a request is successfully processed (i.e. results in a 2XX status), the server responds with the following message:

```
{
    "success": "true"
}
```

If the request is not successful, the endpoint returns an appropriate HTTP status code and error message.

