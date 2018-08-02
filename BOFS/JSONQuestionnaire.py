import os
import json
from datetime import datetime
from globals import db
from flask import current_app, request, session, config
import pprint


class QuestionnaireField():
    def __init__(self, id, dataType, reversed=False, labels=[]):
        self.id = id
        self.dataType = dataType
        self.reversed = reversed
        self.labels = labels

    def __repr__(self):
        return "{{'id': {}, 'dataType': {}, 'reversed': {}, 'labels': {}}}".format(
                repr(self.id), repr(self.dataType), repr(self.reversed), repr(self.labels))


class JSONQuestionnaire():
    def __init__(self, fileName):
        self.fileName = fileName
        fullPath = os.path.join(current_app.root_path, "questionnaires/" + fileName + ".json")

        with open(fullPath) as f:
            self.jsonData = json.load(f)

        self.fields = []
        self.dbClass = None
        self.fieldCount = 0

    def fetchFields(self):
        self.fields = []

        #print "fetchFields() for " + self.fileName

        for q in self.jsonData['questions']:
            if not 'id' in q.keys():
                continue

            try:
                if q['questiontype'] == "radiogrid":  # Radiogrids will have multiple questions inside of them.
                    for qt in q['q_text']:
                        self.fields.append(QuestionnaireField(qt['id'], 'integer', qt.get('reversed', False), q.get('labels', [])))
                elif q['questiontype'] == "checklist":  # checklists also have multiple questions
                    for qt in q['questions']:
                        self.fields.append(QuestionnaireField(qt['id'], 'string'))
                elif q['questiontype'] == "radiolist":  # will always be integer types
                    self.fields.append(QuestionnaireField(q['id'], 'integer', False, q.get('labels', [])))
                elif 'datatype' in q.keys():
                    #print "self.fields.append(QuestionnaireField(" + q['id'] + ", " + q['datatype'] + "))"
                    self.fields.append(QuestionnaireField(q['id'], q['datatype']))
                else:
                    #print "self.fields.append(QuestionnaireField(" + q['id'] + ", 'string'))"
                    self.fields.append(QuestionnaireField(q['id'], 'string'))
            except:
                print "A very bad error occurred! Restart the server NOW or risk losing data!"

            #pprint.pprint(q)

        self.fieldCount = len(self.fields)
        return self.fields

    def createDBClass(self):
        #print "createDBClass() for " + self.fileName

        if not self.fields:  # If list is empty
            self.fetchFields()

        tableName = str.format("questionnaire_{}", self.fileName)

        tableAttr = {
            '__tablename__': tableName,
            str.format('{0}ID', self.fileName): db.Column(db.Integer, primary_key=True, autoincrement=True),
            'participantID': db.Column(db.Integer, db.ForeignKey("participant.participantID")),
            #'participantID': db.Column(db.Integer),
            'participant': db.relationship("Participant", backref=tableName),
            'tag': db.Column(db.String(30), nullable=False, default=""),
            'timeStarted': db.Column(db.DateTime, nullable=False, default=datetime.min),
            'timeEnded': db.Column(db.DateTime, nullable=False, default=datetime.now())
        }

        for field in self.fields:
            if field.dataType == "integer":
                tableAttr[field.id] = db.Column(db.Integer, nullable=False, default=0)
            else:
                tableAttr[field.id] = db.Column(db.Text, nullable=False, default="")

        #pprint.pprint(tableAttr)

        self.dbClass = type(self.fileName, (db.Model,), tableAttr)

    def createBlank(self):
        blank = self.dbClass()

        for column in blank.__table__.c:
            if column.default:
                setattr(blank, column.name, column.default.arg)
            if column.type == db.DateTime:
                setattr(blank, column.name, datetime.min)

        return blank

    def handleQuestionnaire(self, tag=""):
        newObject = self.dbClass()

        #print "handleQuestionnaire() for " + self.fileName + "."

        try:
            timeStarted = datetime.strptime(request.form['timeStarted'], "%Y-%m-%d %H:%M:%S.%f")
        except:
            timeStarted = datetime.strptime(request.form['timeStarted'], "%Y-%m-%d %H:%M:%S")

        # For some reason we've lost the fields! add them again
        if not self.fields or len(self.fields) == 0:
            print "Oh no! We've lost ALL the fields at {}. Running fetchFields() again.".format(str(timeStarted))
            self.fetchFields()

        if len(self.fields) != self.fieldCount:
            print "Oh no! We've lost SOME OF the fields at {}. Running fetchFields() again.".format(str(timeStarted))
            self.fetchFields()

        # Log the per-item timing data
        # gridItemClicks
        #request.form['gridItemClicks']

        try:
            for clickEvent in str(request.form['gridItemClicks']).split(";"):
                if len(clickEvent) == 0:
                    continue  # There is no data (is it the last line?), so skip it.

                clickEvent = clickEvent.replace('\\', "")
                clickEventDict = json.loads(clickEvent)

                parsedTime = datetime.fromtimestamp(float(clickEventDict['time']))

                newLog = db.RadioGridLog()
                newLog.participantID = session['participantID']
                newLog.questionnaire = self.fileName
                newLog.tag = tag
                newLog.questionID = clickEventDict['id']
                newLog.timeClicked = parsedTime
                newLog.value = clickEventDict['value']

                db.session.add(newLog)

        except:
            pass

        for field in self.fields:
            #print field

            try:
                value = request.form[field.id]
                setattr(newObject, field.id, value)
            except:
                print "Could not write field " + str(field.id)
            #print("value = {}; set value = {};".format(repr(value), repr(getattr(newObject, field.id))))

        setattr(newObject, 'participantID', session['participantID'])
        setattr(newObject, 'timeStarted', timeStarted)
        setattr(newObject, 'timeEnded', datetime.now())
        setattr(newObject, 'tag', tag)

        db.session.add(newObject)
        db.session.commit()

        if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] == True:
            if not os.path.exists("logs"):
                os.makedirs("logs")

            f = open("logs/" + self.fileName + ".txt", "a+")
            f.write("Time = " + str(timeStarted) + "; pID = " + str(session['participantID']) + ";\n" + pprint.pformat(request.form) + "\n\n")

    def getField(self, id):
        for f in self.fields:
            if f.id == id:
                return f
        return None

    def fetchFieldDict(self):
        pass

    def columnList(self):
        pass

    def fetchAllData(self):
        return db.session.query(self.dbClass).all()

    def fetchFinishedData(self):
        return db.session.query(self.dbClass).filter(db.Participant.finished == True).all()

    # Returns a list of the data for a single column, ordered by
    def fetchColumnData(self, column, condition=0, finishedOnly=True):
        #q = None
        #if finishedOnly:
        #    q = db.session.query(self.dbClass).filter(db.Participant.finished == True)
        #else:
        #    q = db.session.query(self.dbClass)

        q = db.session.query(getattr(self.dbClass, column)).\
            join(db.Participant,
                 db.and_(
                     getattr(self.dbClass, "participantID") == db.Participant.participantID,
                     db.Participant.condition == condition
                 ))

        return q.all()