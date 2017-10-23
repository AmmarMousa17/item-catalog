from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Team, Base, Player, User

engine = create_engine('sqlite:///teamplayerswithusers.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()



User1 = User(name="Ammar", email="ammar_mousa17@hotmail.com",
             picture='Ammar.jpg')
session.add(User1)
session.commit()

Team1 = Team(user_id=1, name="Ahly")

session.add(Team1)
session.commit()

player1 = Player(user_id=1, name="Ekramy", description="The worst",
                     price="$7.50m", position="Goalkeeper", team=Team1)

session.add(player1)
session.commit()


player2 = Player(user_id=1, name="Saad samir", description="",
                     price="$2.50m", position="Defender", team=Team1)

session.add(player2)
session.commit()

player2 = Player(user_id=1, name="Rabbia", description="",
                     price="$2.50m", position="Defender", team=Team1)


session.add(player2)
session.commit()

player2 = Player(user_id=1, name="Nagib", description="",
                     price="$2.50m", position="Defender", team=Team1)

session.add(player2)
session.commit()

player3 = Player(user_id=1, name="Ashour", description="",
                     price="$2.50m", position="Mid", team=Team1)

session.add(player3)
session.commit()

player4 = Player(user_id=1, name="Saleh", description="The Best",
                     price="$20.50m", position="Mid", team=Team1)


session.add(player4)
session.commit()

player5 = Player(user_id=1, name="Solya", description="The ",
                     price="$5.50m", position="Mid", team=Team1)


session.add(player5)
session.commit()

player6 = Player(user_id=1, name="Ajay", description="",
                     price="$5.50m", position="Attack", team=Team1)

session.add(player6)
session.commit()

player7 = Player(user_id=1, name="Walid", description=" ",
                     price="$10.50m", position="Attack", team=Team1)

session.add(player7)
session.commit()

Team2 = Team(user_id=1, name="Zamalek")

session.add(Team2)
session.commit()


player1 = Player(user_id=1, name="Shennawy", description=" ",
                     price="$10.50m", position="Goalkeeper", team=Team2)

session.add(player1)
session.commit()

player2 = Player(user_id=1, name="Gabr", description=" ",
                     price="$7.50m", position="Defender", team=Team2)

session.add(player2)
session.commit()


player3 = Player(user_id=1, name="Hazem", description=" ",
                     price="$10.50m", position="Defender", team=Team2)

session.add(player3)
session.commit()

player4 = Player(user_id=1, name="Tarek", description="",
                     price="$10.50m", position="Mid", team=Team2)

session.add(player4)
session.commit()


player5 = Player(user_id=1, name="Rooka", description=" ",
                     price="$.50m", position="Mid", team=Team2)

session.add(player5)
session.commit()


player6 = Player(user_id=1, name="kasongo", description=" ",
                     price="$0.50m", position="Attack", team=Team2)

session.add(player6)
session.commit()
print "added players!"

