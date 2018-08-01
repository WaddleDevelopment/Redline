import math
from BOFS.globals import db
from BOFS.util import fetch_condition_count


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


def std(numbers):
    mn = mean(numbers)
    variance = sum([(e-mn)**2 for e in numbers]) / len(numbers)
    return math.sqrt(variance)


class DescriptiveStats():
    def __init__(self):
        self.length = 0
        self.min = 0
        self.max = 0
        self.mean = 0
        self.std = 0
        self.sem = 0

    def calcDescriptives(self, data):
        self.length = len(data)

        if self.length > 0:
            self.min = min(data)
            self.max = max(data)
            self.mean = mean(data)
            self.std = std(data)
            self.sem = self.std/math.sqrt(self.length)


class NumericResults():
    def __init__(self, dbClass, fields, tag):
        self.dbClass = dbClass
        self.tag = tag
        self.fields = fields

        fieldsToRemove = []

        # Exclude fields that are not numeric before any of these other methods do their job
        for field in self.fields:
            dbColumn = getattr(self.dbClass, field.id)
            if not(dbColumn.expression.type.python_type == int or dbColumn.expression.type.python_type == float):
                fieldsToRemove.append(field)

        for field in fieldsToRemove:
            self.fields.remove(field)

        self.findIDGroups()
        self.fetchRawByCondition()
        self.calcGrouped()
        self.calcDescriptive()

    def getFieldOrPrefixList(self):
        result = []

        for field in self.fields:
            fieldParts = field.id.split('_')
            if len(fieldParts) > 1 and (fieldParts[0] in self.groupPrefixes):
                continue

            result.append(field.id)

        result.extend(self.groupPrefixes)
        result.sort()

        return result

    # Group names are what come before the first underscore
    def findIDGroups(self):
        potentialGroups = {} # key is potential group name, value is a count of fields that would fit into the group
        self.groupPrefixes = []
        self.groupSizes = {}

        for field in self.fields:
            #ids.append(field['id'])
            idParts = field.id.split('_')

            # No underscore, so skip it.
            if len(idParts) <= 1:
                continue

            # If there's already an entry for this potential prefix, add 1 to count, otherwise set to 1
            if idParts[0] in potentialGroups:
                potentialGroups[idParts[0]] += 1
            else:
                potentialGroups[idParts[0]] = 1

        for k, v in potentialGroups.items():
            if v > 1:
                self.groupSizes[k] = v
                self.groupPrefixes.append(k)

        return self.groupPrefixes

    def fetchRawByCondition(self):
        self.dataRaw = {}

        for condition in range(0, fetch_condition_count()+1):
            self.dataRaw[condition] = {}

            q = db.session.query(self.dbClass).\
                join(db.Participant,
                     db.and_(
                         getattr(self.dbClass, "participantID") == db.Participant.participantID,
                         db.Participant.condition == condition
                     )).\
                filter(
                    db.Participant.finished == True,
                    getattr(self.dbClass, "tag") == self.tag
                )

            self.dataRaw[condition] = q.all()

        # Eliminate empty conditions
        for condition in range(0, fetch_condition_count()+1):
            if len(self.dataRaw[condition]) == 0:
                del self.dataRaw[condition]
                break

    def calcGrouped(self):
        # key is condition (int), value is a dict
        # inner dicts: key is field name or group name, value is average over group or individual value
        self.dataGrouped = {}

        for condition, dr in self.dataRaw.items():
            if len(dr) == 0:  # No data here, so skip it.
                continue

            # Since we're starting with a fresh dict, we need to build it as we go
            if not condition in self.dataGrouped:
                self.dataGrouped[condition] = {}

            for i, row in enumerate(dr):
                for field in self.fields:
                    isGroup = False
                    idOrPrefix = field.id
                    idParts = field.id.split('_')

                    # is this field part of a group?
                    if len(idParts) > 1 and idParts[0] in self.groupPrefixes:
                        isGroup = True
                        idOrPrefix = idParts[0]

                    val = getattr(row, field.id)

                    if not (type(val) == int or type(val) == float):
                        break

                    # Continue to build the dict if necessary
                    if not idOrPrefix in self.dataGrouped[condition]:
                        self.dataGrouped[condition][idOrPrefix] = [0] * len(dr)

                    if isGroup:
                        if field.reversed:
                            self.dataGrouped[condition][idOrPrefix][i] += (len(field.labels) + 1 - val) # TODO: determine range
                        else:
                            self.dataGrouped[condition][idOrPrefix][i] += val
                    else:
                        self.dataGrouped[condition][idOrPrefix][i] = val

                # As the last step, need to calculate the average, for each grouped fields, for each row
                for prefix in self.groupPrefixes:
                    self.dataGrouped[condition][prefix][i] /= float(self.groupSizes[prefix])


    def calcDescriptive(self):
        self.dataDescriptive = {}

        for condition, dg in self.dataGrouped.items():

            self.dataDescriptive[condition] = {}

            for fieldOrPrefix, val in dg.items():
                ds = DescriptiveStats()
                ds.calcDescriptives(val)

                self.dataDescriptive[condition][fieldOrPrefix] = ds