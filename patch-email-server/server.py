from flask import Flask, render_template, url_for, request, redirect, jsonify
app = Flask(__name__)

# import CRUD operations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Alert, User, Request

# make sure we can access the database
engine = create_engine('sqlite:///patchalerts.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# API
@app.route('/PatchAlert/requests/JSON')
def getAllRequestsJSON():
    requests = session.query(Request).all()
    return jsonify(requests=[request.serialize for request in requests])

@app.route('/PatchAlert/requests/<int:alert_id>/JSON')
def getAllRequestsPerAlertJSON(alert_id):
    requests = session.query(Request).filter_by(alert_id=alert_id).all()
    return jsonify(requests=[request.serialize for request in requests])

@app.route('/PatchAlert/alerts/JSON')
def getAllAlertsJSON():
    alerts = session.query(Alert).all()
    return jsonify(alerts=[alert.serialize for alert in alerts])


# render templates
@app.route('/')
@app.route('/home')
@app.route('/PatchAlert')
def showAllAlerts():
    alerts = session.query(Alert).filter_by(isApproved = 1).all()
    return render_template('home.html', alerts = alerts)

@app.route('/request/<int:alert_id>/', methods=['GET','POST'])
def requestException(alert_id):
    if request.method == 'POST':
        alert = session.query(Alert).filter_by(id = alert_id).one()
        newRequest = Request(
            server=request.form['server'],
            reason=request.form['reason'],
            altDate=request.form['altDate'],
            altTime=request.form['altTime'],
            user=request.form['user'],
            alert = alert)
        session.add(newRequest)
        session.commit()
        return redirect(url_for('showAllAlerts'))
    else:
        return render_template('request.html', alert_id=alert_id)

@app.route('/new/login', methods=['GET','POST'])
def loginToCreateAlert():
    if request.method == 'POST':
        return redirect(url_for('createAlert', user_id=1))
    else:
        return render_template('new-alert_login.html')

@app.route('/new/<int:user_id>/', methods=['GET','POST'])
def createAlert(user_id):
    if request.method == 'POST':
        newAlert = Alert(
            servers=request.form['Servers'],
            date=request.form['Date'],
            startTime=request.form['startTime'],
            endTime=request.form['endTime'],
            isApproved = 0,
            createdBy_id = user_id)
        session.add(newAlert)
        session.commit()
        return redirect(url_for('showAllAlerts'))
    else:
        return render_template('createAlert.html', user_id=user_id)

@app.route('/PatchAlert/new/<int:alert_id>/approval/login', methods=['GET','POST'])
@app.route('/new/<int:alert_id>/approval/login', methods=['GET','POST'])
def loginToApproveAlert(alert_id):
    if request.method == 'POST':
        return redirect(url_for('approveAlert', user_id=1, alert_id=alert_id))
    else:
        return render_template('approve-alert_login.html', alert_id=alert_id)

@app.route('/PatchAlert/new/<int:alert_id>/<int:user_id>/approval', methods=['GET','POST'])
@app.route('/new/<int:alert_id>/<int:user_id>/approval', methods=['GET','POST'])
def approveAlert(alert_id, user_id):
    alert = session.query(Alert).filter_by(id = alert_id).one()
    if request.method == 'POST':
        if request.form['approve'] == "1":
            # figure out how to set isApproved to form['approve']
            alert.isApproved = 1
            session.add(alert)
            session.commit()
        else:
            print "Not approved"
        return redirect(url_for('showAllAlerts'))
    else:
        return render_template('approve.html', alert=alert, alert_id=alert_id, user_id=user_id)

@app.route('/PatchAlert/<int:alert_id>/stats')
def getStats(alert_id):
    return render_template('stats.html', alert_id=alert_id)


if __name__ == '__main__':
    app.debug = True # restart server on changes
    app.run(host = '0.0.0.0', port = 5000)
