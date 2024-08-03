


# def compare_time():
#     now = datetime.utcnow()
#     one_week_ago = now - timedelta(weeks=1)
#     two_weeks_ago = now - timedelta(weeks=2)

#     last_week_time = db.session.query(db.func.sum(UserSession.duration)).filter(
#         UserSession.start_time.between(one_week_ago, now)).scalar()

#     previous_week_time = db.session.query(db.func.sum(UserSession.duration)).filter(
#         UserSession.start_time.between(two_weeks_ago, one_week_ago)).scalar()

#     return jsonify({
#         'last_week_time': last_week_time,
#         'previous_week_time': previous_week_time
#     }), 200