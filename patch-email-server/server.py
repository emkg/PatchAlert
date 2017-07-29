from flask import Flask, flash, render_template, url_for, request, redirect, jsonify
from flask_mail import Mail, Message
import json

app = Flask(__name__)
app.secret_key = 'secret'
mail = Mail()

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = True,
))

mail.init_app(app)

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
    return render_template('home.html', alerts = alerts, json=json)

@app.route('/request/<int:alert_id>/', methods=['GET','POST'])
def requestException(alert_id):
    alert = session.query(Alert).filter_by(id = alert_id).one()
    if request.method == 'POST':
        newRequest = Request(
            server=request.form['server'],
            reason=request.form['reason'],
            altDate=request.form['altDate'],
            altTime=request.form['altTime'],
            user=request.form['user'],
            alert = alert)
        session.add(newRequest)
        session.commit()
        flash("Your request has been submitted. Thank you!")
        return redirect(url_for('showAllAlerts'))
    else:
        return render_template('request.html', alert_id=alert_id, alert=alert, json=json)

@app.route('/new/login', methods=['GET','POST'])
def loginToCreateAlert():
    if request.method == 'POST':
        return redirect(url_for('createAlert', user_id=1))
    else:
        return render_template('createAlert_login.html')

@app.route('/new/<int:user_id>/', methods=['GET','POST'])
def createAlert(user_id):
    if request.method == 'POST':
        newAlert = Alert(
            servers=getServersAsJSONString(request.form['Servers']),
            date=request.form['Date'],
            startTime=request.form['startTime'],
            endTime=request.form['endTime'],
            isApproved = 0,
            createdBy_id = user_id)
        session.add(newAlert)
        session.commit()
        flash("A new service alert has been created. It will appear here on approval by the appropriate admin.")

        '''
        sendMail("Hello,<br/>A new service alert has been created. "
        + "Please log in and approve it. <br/><br/>Thank you!",
        "Webmaster",
        "example@localhost",
        "example@localhost")
        '''

        return redirect(url_for('showAllAlerts'))
    else:
        return render_template('createAlert.html', user_id=user_id)

@app.route('/PatchAlert/new/<int:alert_id>/approval/login', methods=['GET','POST'])
@app.route('/new/<int:alert_id>/approval/login', methods=['GET','POST'])
def loginToApproveAlert(alert_id):
    if request.method == 'POST':
        return redirect(url_for('approveAlert', user_id=1, alert_id=alert_id))
    else:
        return render_template('approve_login.html', alert_id=alert_id)

@app.route('/PatchAlert/new/<int:alert_id>/<int:user_id>/approval', methods=['GET','POST'])
@app.route('/new/<int:alert_id>/<int:user_id>/approval', methods=['GET','POST'])
def approveAlert(alert_id, user_id):
    alert = session.query(Alert).filter_by(id = alert_id).one()
    if request.method == 'POST':
        alert.isApproved = 1
        session.add(alert)
        session.commit()
        flash("The alert has been approved!")
        '''
        # add more information to the message
        sendMail("Hello,<br/>A new service alert has been created. Please login to see details."
        + "<br/><br/>Thank you!",
        "Webmaster",
        "example@localhost",
        "exampleTeam@localhost")
        '''
        return redirect(url_for('showAllAlerts'))
    else:
        return render_template('approve.html', alert=alert, alert_id=alert_id, user_id=user_id)

@app.route('/PatchAlert/<int:alert_id>/stats')
def getStats(alert_id):
    return render_template('stats.html', alert_id=alert_id)

def sendMail(message, senderName, sender, recipient):
    '''
    msg = Message(message,
                  sender=(senderName, sender),
                  recipients=[recipient])
    mail.send(msg)
    '''
    return senderName + "@ " + sender + " says: \n" + message + "\n to: " + recipient


def getServersAsJSONString(stringlistOfServers):
    if stringlistOfServers:
        listlistOfServers = stringlistOfServers.split(' ')
        jso = json.dumps(listlistOfServers)

        return jso
    else:
        return "No servers listed :("


# need additional timer function that checks if alerts are expired
# may need to reconfigure db to inlcude an expiration date/time
# when an alert expires, send email to admin-creator(s) with stats,
# or link to stats

if __name__ == '__main__':
    app.debug = True # restart server on changes
    app.run(host = '0.0.0.0', port = 5000)
