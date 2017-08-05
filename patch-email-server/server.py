from flask import Flask, flash, render_template, url_for, request, redirect, jsonify
from flask_mail import Mail, Message
from sqlalchemy import distinct, func
from datetime import datetime, timedelta
import json

user = False;

app = Flask(__name__)
app.secret_key = 'secret'
mail = Mail()

'''
app.config['MAIL_SERVER'] = default 'localhost'
app.config['MAIL_PORT'] = default 25
app.config['MAIL_USE_TLS'] = default False
app.config['MAIL_USE_SSL'] = default False
app.config['MAIL_DEBUG'] = default app.debug
app.config['MAIL_USERNAME'] = default None
app.config['MAIL_PASSWORD'] = default None
app.config['MAIL_DEFAULT_SENDER'] = default None
app.config['MAIL_MAX_EMAILS'] = default None
app.config['MAIL_SUPPRESS_SEND'] = default app.testing
app.config['MAIL_ASCII_ATTACHMENTS'] = default False
'''

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

'''
### API
'''
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
'''
### TEMPLATES
'''

### BASIC APP

# home
@app.route('/')
@app.route('/home')
@app.route('/PatchAlert')
def showAllAlerts():
    updateExpiredStatusOfAlerts()
    alerts = session.query(Alert).filter_by(isApproved = 1, isExpired = 0).all()
    return render_template('home.html', alerts = alerts, json=json)

@app.route('/request/<int:alert_id>/', methods=['GET','POST'])
def requestException(alert_id):
    alert = session.query(Alert).filter_by(id = alert_id).one()
    now = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        servers = request.form['server'].replace(', ', ',')
        newRequest = Request(
            server=servers,
            reason=request.form['reason'],
            altDate=request.form['altDate'],
            altTime=request.form['altTime'],
            dateCreated=now,
            user=request.form['user'],
            alert = alert)
        session.add(newRequest)
        session.commit()
        flash("Your request has been submitted. Thank you!")
        return redirect(url_for('showAllAlerts'))
    else:
        return render_template('request.html', alert_id=alert_id, alert=alert, json=json)

### ADMIN FUNCTIONS

# admin login
@app.route('/PatchAlert/admin/login', methods=['GET','POST'])
def adminLogin():
    if request.method == 'POST':
        global user
        user = True
        return redirect(url_for('showAllAlertsAdmin'))
    else:
        return render_template('login.html')

# admin home
@app.route('/PatchAlert/admin')
def showAllAlertsAdmin():
    if user == False:
        return redirect(url_for('adminLogin'))
    else:
        alerts = session.query(Alert).all()
        return render_template('adminHome.html', alerts = alerts, json=json)

# create alert
@app.route('/new', methods=['GET','POST'])
def createAlert():
    now = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        newAlert = Alert(
            servers=request.form['servers'],
            date=request.form['date'],
            startTime=request.form['startTime'],
            endTime=request.form['endTime'],
            dateCreated=now,
            isApproved = 0,
            isExpired = 0)
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

        return redirect(url_for('showAllAlertsAdmin'))
    else:
        return render_template('createAlert.html')

# approve alert
@app.route('/PatchAlert/new/<int:alert_id>/approval', methods=['GET','POST'])
@app.route('/new/<int:alert_id>/approval', methods=['GET','POST'])
def approveAlert(alert_id):
    alert = session.query(Alert).filter_by(id = alert_id).one()
    if request.method == 'POST':
        alert.isApproved = 1
        session.add(alert)
        session.commit()
        flash("The alert has been approved!")
        # add more information to the message
        '''
        sendMail("Hello,<br/>A new service alert has been created. Please login to see details."
        + "<br/><br/>Thank you!",
        "Webmaster",
        "localhost",
        "example@localhost")
        '''

        return redirect(url_for('showAllAlertsAdmin'))
    else:
        return render_template('approve.html', alert=alert,
                                               alert_id=alert_id,
                                               json=json)
# delete alert
@app.route('/PatchAlert/admin/<int:alert_id>/delete')
def deleteAlert(alert_id):
    alert = session.query(Alert).filter_by(id = alert_id).one()
    session.delete(alert)
    session.commit()
    return redirect(url_for('showAllAlertsAdmin'))

# get alert stats
@app.route('/PatchAlert/<int:alert_id>/stats')
def getStats(alert_id):
    alertDate = session.query(Alert).filter_by(id = alert_id).one().date
    requests = session.query(Request).filter_by(alert_id = alert_id).all()
    requestServers = []
    for r in requests:
        servers = r.server.split(',')
        for s in servers:
            requestServers.append(s)
    requestServers = getCounts(requestServers)
    return render_template('stats.html', alert_id=alert_id,
                                         alertDate=alertDate,
                                         servers=requestServers,
                                         requests=requests)

# get historic stats
@app.route('/PatchAlert/stats')
def getAllStats():
    alerts = session.query(Alert).all()
    requests = session.query(Request).all()
    allServers = []
    timeDictionary = {}
    for a in alerts:
        # deal with timing
        deltaTimeSum = 0
        requestsPerAlert = session.query(Request).filter_by(alert_id = a.id).all()
        for req in requestsPerAlert:
            # a.dateCreated - req.dateCreated,
            # converted to datetime, get .toSeconds() (or to day for now)
            # to store as float
            timeDiff = datetime.strptime(a.dateCreated, '%Y-%m-%d') - datetime.strptime(req.dateCreated, '%Y-%m-%d')
            timeDiff = timeDiff.days
            deltaTimeSum = deltaTimeSum + timeDiff
            # save the dictionary so that each alert id is stored
            # as a key to a dictionary of number of requests for that
            # alert, and the total seconds sum of time between alert creation
            # and request
        timeDictionary.update({a.id : { len(requestsPerAlert) : deltaTimeSum }})

        # get the servers
        serversAffected = a.servers.split(',')
        for sa in serversAffected:
            allServers.append(sa)

    allServers = getCounts(allServers)
    users = []
    requestServers = []
    for r in requests:
        users.append(r.user)
        servers = r.server.split(',')
        for s in servers:
            requestServers.append(s)
    requestServers = getCounts(requestServers)
    users = getCounts(users)
    return render_template('allStats.html', servers=allServers,
                                            timeDictionary=timeDictionary,
                                            requests=requestServers,
                                            users=users)

### AUXILIARY FUNCTIONS

''' counts the number of things in the
    list of things supplied (must be a list)
'''
def getCounts(listOfThings):
    countsDictionary = {};
    for i in listOfThings:
        count = 0
        for j in listOfThings:
            if j == i:
                count = count + 1
        countsDictionary.update({i : count})
    return countsDictionary

''' send an email with the suppled message from the
    supplied senderName at the "sender" address
    to the supplied recipient address
'''
def sendMail(message, senderName, sender, recipient):
    msg = Message(message,
                  sender=(senderName, sender),
                  recipients=[recipient])
    mail.send(msg)
    return senderName + "@ " + sender + " says: \n" + message + "\n to: " + recipient

def updateExpiredStatusOfAlerts():
    alerts = session.query(Alert).all()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    now = datetime.strptime(now, '%Y-%m-%d %H:%M')
    for a in alerts:
        date = "%s %s" % (a.date, a.startTime)
        date = datetime.strptime(date, '%Y-%m-%d %H:%M')
        if (now - date) >= timedelta(hours=-12):
            a.isExpired = 1
            session.add(a)
            session.commit()
            #sendMail()
                # TODO:
                # when an alert expires, send email to admin-creator(s) with stats,
                # or link to stats
        else:
            a.isExpired = 0
            session.add(a)
            session.commit()
    return

# launches the app:
if __name__ == '__main__':
    app.debug = True # restart server on changes
    app.run(host = '0.0.0.0', port = 5000)
