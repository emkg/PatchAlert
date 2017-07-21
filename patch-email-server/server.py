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

@app.route('/')
@app.route('/home')
@app.route('/PatchAlert')
def showAllAlerts():
    return "This is the main page!"

@app.route('/request/<int:alert_id>/login')
def loginToRequestException(alert_id):
    return "This is where users log in!"

@app.route('/request/<int:alert_id>/<int:user_id>')
def requestException(alert_id, user_id):
    return "This is where users ask for exceptions"

@app.route('/new/login')
def loginToCreateAlert():
    return "This is also where users log in!"

@app.route('/new/<int:user_id>/')
def createAlert(user_id):
    return "This is where admins create alerts."

@app.route('/new/<int:alert_id>/approval/login')
def loginToApproveNewAlert(alert_id):
    return "This is where admins log in to approve alerts"

@app.route('/new/<int:alert_id>/<int:user_id>/approval')
def approveAlert(alert_id, user_id):
    return "This is where admins approve of alerts"

@app.route('/PatchAlert/<int:alert_id>/stats')
def getStats(alert_id):
    return "this is where admins can see alert stats once they are logged in!"


if __name__ == '__main__':
    app.debug = True # restart server on changes
    app.run(host = '0.0.0.0', port = 5000)
