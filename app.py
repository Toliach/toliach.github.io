from flask import Flask, render_template, request, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = "secret_key"

class Character:
    def __init__(self, name, hp, damage, tokens=3):
        self.name = name
        self.hp = hp
        self.damage = damage
        self.tokens = tokens

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        return Character(data['name'], data['hp'], data['damage'], data['tokens'])

characters = {
    "knight": Character("Треугол", 100, 10),
    "archer": Character("Крог", 80, 15),
    "tank": Character("КвОдрат", 150, 5)
}

enemies = [
    Character("Треугол", 100, 10),
    Character("КвОдрат", 150, 5),
    Character("Крог", 80, 15)
]

def generate_enemy():
    enemy = random.choice(enemies)
    return Character(enemy.name, enemy.hp, enemy.damage)

def get_battle_image(player, enemy):
    return f"{player.name.lower()}_{enemy.name.lower()}.png"

def enemy_turn(enemy):
    t = enemy.tokens

    if t <= 0:
        return 0, 0, 0

    if t <= 5:
        attack = 1 if t >= 1 else 0
        defense = 0
        save = t - attack

    elif t <= 8:
        attack = max(1, t // 2)
        defense = 1 if t - attack >= 1 else 0
        save = t - attack - defense

    elif enemy.hp <= 30:
        attack = t
        defense = 0
        save = 0

    else:
        attack = t - 2
        defense = 1
        save = 1

    attack = max(0, attack)
    defense = max(0, defense)
    save = max(0, save)

    return attack, defense, save


def resolve_turn(player, enemy, p_act, e_act):
    p_attack, p_def, p_save = p_act
    e_attack, e_def, e_save = e_act

    damage_to_enemy = max(0, (p_attack * player.damage) - (e_def * enemy.damage))
    damage_to_player = max(0, (e_attack * enemy.damage) - (p_def * player.damage))

    enemy.hp -= damage_to_enemy
    player.hp -= damage_to_player

    player.tokens = player.tokens + p_save
    enemy.tokens = enemy.tokens + e_save

    player.tokens += 1
    enemy.tokens += 3

    return damage_to_enemy, damage_to_player

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    choice = request.form.get("character")
    player = characters[choice]
    enemy = generate_enemy()

    session['player'] = player.to_dict()
    session['enemy'] = enemy.to_dict()
    session['log'] = []

    return redirect(url_for('battle'))


@app.route("/battle", methods=["GET", "POST"])
def battle():
    if 'player' not in session:
        return redirect(url_for('index'))

    player = Character.from_dict(session['player'])
    enemy = Character.from_dict(session['enemy'])
    image = get_battle_image(player, enemy)

    log = session.get('log', [])

    if request.method == "POST":
        attack = int(request.form.get("attack", 0))
        defense = int(request.form.get("defense", 0))
        save = int(request.form.get("save", 0))

        if attack + defense + save > player.tokens:
            log.append("Недостаточно жетонов")
        else:
            player.tokens -= (attack + defense)

            p_act = (attack, defense, save)
            e_act = enemy_turn(enemy)

            e_attack, e_def, e_save = e_act
            enemy.tokens -= (e_attack + e_def)
            p_act = (attack, defense, save)
            e_act = enemy_turn(enemy)

            dmg_e, dmg_p = resolve_turn(player, enemy, p_act, e_act)

            log.append(f"Игрок нанес {dmg_e} урона")
            log.append(f"Враг нанес {dmg_p} урона")

    session['player'] = player.to_dict()
    session['enemy'] = enemy.to_dict()
    session['log'] = log

    if player.hp <= 0:
        return "Вы проиграли"
    if enemy.hp <= 0:
        return "Вы победили"

    return render_template("battle.html", player=player, enemy=enemy, log=log, image=image)


if __name__ == "__main__":
    app.run(debug=False)


"""
<!DOCTYPE html>
<html>
<head>
    <title>Выбор персонажа</title>
</head>
<body>
    <h1>Выбери персонажа</h1>
    <form method="post" action="/start">
        <button name="character" value="knight">Knight</button>
        <button name="character" value="archer">Archer</button>
        <button name="character" value="tank">Tank</button>
    </form>
</body>
</html>
"""

"""
<!DOCTYPE html>
<html>
<head>
    <title>Бой</title>
</head>
<body>
    <h2>Бой</h2>

    <img src="{{ url_for('static', filename=image) }}" width="400">

    <p>Игрок: {{player.name}} | HP {{player.hp}} | Жетоны {{player.tokens}}</p>
    <p>Враг: {{enemy.name}} | HP {{enemy.hp}} | Жетоны {{enemy.tokens}}</p>

    <form method="post">
        <input type="number" name="attack" placeholder="Атака">
        <input type="number" name="defense" placeholder="Защита">
        <input type="number" name="save" placeholder="Экономия">
        <button type="submit">Следующий ход</button>
    </form>

    <h3>Лог:</h3>
    {% for line in log %}
        <p>{{line}}</p>
    {% endfor %}

</body>
</html>
"""
