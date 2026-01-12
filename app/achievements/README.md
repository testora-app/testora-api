# 🏆 Flask Achievement System

This is a modular, data-driven achievement system built for a Flask API using SQLAlchemy. It tracks user progress and automatically awards achievements when thresholds are met.

---

## 🚀 Features

- Track progress by: number of tests taken, streak days, test points, and level
- Define achievements in a database (or JSON for seeding)
- Automatically unlock and store achievements per user
- Designed to scale easily by using a generic checking system

---

## 📦 Database Models (SQLAlchemy)

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tests_taken = db.Column(db.Integer, default=0)
    streak_days = db.Column(db.Integer, default=0)
    test_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

class Achievement(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)  # e.g., "tests_taken"
    value = db.Column(db.Integer)

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    achievement_id = db.Column(db.String, db.ForeignKey('achievement.id'))

    user = db.relationship('User', backref='achievements')
    achievement = db.relationship('Achievement')


def check_and_unlock_achievements(user):
    unlocked_ids = {ua.achievement_id for ua in user.achievements}
    new_achievements = []

    all_achievements = Achievement.query.all()

    for ach in all_achievements:
        stat_value = getattr(user, ach.type, 0)
        if stat_value >= ach.value and ach.id not in unlocked_ids:
            ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
            db.session.add(ua)
            new_achievements.append(ach.name)

    if new_achievements:
        db.session.commit()
    
    return new_achievements


@app.route('/user/<int:user_id>/take_test', methods=['POST'])
def take_test(user_id):
    user = User.query.get_or_404(user_id)

    # Simulate test action
    user.tests_taken += 1
    user.test_points += request.json.get('points', 10)
    user.streak_days += 1
    user.level += 1

    db.session.commit()

    newly_unlocked = check_and_unlock_achievements(user)

    return jsonify({
        "message": "Test taken.",
        "new_achievements": newly_unlocked
    })


def seed_achievements():
    achievements = [
        {"id": "tests_10", "name": "Test Taker - 10 Tests", "type": "tests_taken", "value": 10},
        {"id": "streak_7", "name": "One Week Streak", "type": "streak_days", "value": 7},
        {"id": "points_100", "name": "Century Points", "type": "test_points", "value": 100},
        {"id": "level_up", "name": "Level Up", "type": "level", "value": 2}
    ]
    for a in achievements:
        if not Achievement.query.get(a["id"]):
            db.session.add(Achievement(**a))
    db.session.commit()
```

Add frontend achievement badges

Create admin panel for adding/editing achievements

Hook into a notification or email system

Create XP-based leveling system
