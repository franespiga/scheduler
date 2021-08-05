import pyomo.environ as pyo
import numpy as np
import pyomo.kernel as pmo
import pandas as pd

class course_scheduler:
    def __init__(self, days, hours, hours_per_subject, max_hours_per_day):
        self.days = days
        self.hours = hours
        self.subjects = list(hours_per_subject.keys())
        self.hours_per_subject = hours_per_subject
        self.max_hours_per_day = max_hours_per_day
        self.model = None
        self.schedule = None
        
    def create_model(self):
        # MODEL DEFINITION ----------------------------------------------------------
        model = pyo.ConcreteModel()

        # Sets
        model.sDays = pyo.Set(initialize = self.days, ordered = True)
        model.sHours = pyo.Set(initialize = self.hours, ordered = True)
        model.sSubjects = pyo.Set(initialize = self.subjects)

        # Parameters
        model.pHoursPerSubject = pyo.Param(model.sSubjects, initialize = self.hours_per_subject)
        model.pMinDaysPerSubject = pyo.Param(model.sSubjects, initialize = dict(zip(self.hours_per_subject.keys(), [round(i/self.max_hours_per_day) for i in list(self.hours_per_subject.values())])))
        model.pMaxDaysPerSubject = pyo.Param(model.sSubjects, initialize = self.hours_per_subject)

        model.pPreferences = pyo.Param(model.sDays, model.sHours, model.sSubjects, initialize = 1.0, mutable = True)

        # Decision variable
        model.vbSubjectSchedule = pyo.Var(model.sDays, model.sHours, model.sSubjects, domain = pmo.Binary)

        # Helper variables
        model.vbSubjectDaysFlags = pyo.Var(model.sDays, model.sSubjects, domain = pmo.Binary)
        model.vIcumulatedHours = pyo.Var(model.sDays, model.sHours, model.sSubjects, domain = pyo.NonNegativeIntegers)
        model.vIsubjectTotalDays = pyo.Var(domain = pyo.NonNegativeIntegers)
        #model.vISubjectSwitches = pyo.Var(model.sDays, model.sHours, model.sSubjects, domain = pyo.Integers)
        model.vbSubjectSwitches = pyo.Var(model.sDays, model.sHours, model.sSubjects, domain = pmo.Binary)

        # Constraints 
        #-------- single assignment constraints
        # :: Only one subject can be held in the classroom at the same time
        model.ctOnlyOneSubject = pyo.ConstraintList()
        for i in model.sDays:
            for j in model.sHours:
                model.ctOnlyOneSubject.add(sum(model.vbSubjectSchedule[i,j,k] for k in model.sSubjects)<=1)

        #-------- hourly constraints
        # :: All the scheduled hours for a subject must be exactly the total weekly number of hours
        model.ctCoverAllHours = pyo.ConstraintList()
        for k in model.sSubjects:
            model.ctCoverAllHours.add(sum(model.vbSubjectSchedule[i,j,k] for i in model.sDays for j in model.sHours)<=model.pHoursPerSubject[k])
            model.ctCoverAllHours.add(sum(model.vbSubjectSchedule[i,j,k] for i in model.sDays for j in model.sHours)>=model.pHoursPerSubject[k])

        model.ctMaxDailyHours = pyo.ConstraintList()
        for k in model.sSubjects:
            for i in model.sDays:
                model.ctMaxDailyHours.add(sum(model.vbSubjectSchedule[i,j,k] for j in model.sHours)<=self.max_hours_per_day)


        #-------- daily constraints
        # :: for each subject and day, at most there can be the max daily hours alloted for that subject
        model.ctSubjectDaysFlags = pyo.ConstraintList()
        for k in model.sSubjects:
            for i in model.sDays:
                model.ctSubjectDaysFlags.add(self.max_hours_per_day*model.vbSubjectDaysFlags[i,k]>=sum(model.vbSubjectSchedule[i,j,k] for j in model.sHours))

        # :: Each subject can be assigned to at most hours/max hours DAYS and at least 1 hour on each of the days it has been scheduled.
        model.ctSubjectDays = pyo.ConstraintList()
        for k in model.sSubjects:
            model.ctSubjectDays.add(sum(model.vbSubjectDaysFlags[i,k] for i in model.sDays)<=model.pMaxDaysPerSubject[k])
            model.ctSubjectDays.add(sum(model.vbSubjectDaysFlags[i,k] for i in model.sDays)>=model.pMinDaysPerSubject[k])



        #--------- block constraints
        # :: Cumulative constraints
        model.ctCumulativeHours = pyo.ConstraintList()
        for k in model.sSubjects:
            for i in model.sDays:
                for j in model.sHours:
                    if j!=model.sHours.first():
                        model.ctCumulativeHours.add(expr = model.vIcumulatedHours[i,j,k]==model.vIcumulatedHours[i,model.sHours.prev(j),k]+model.vbSubjectSchedule[i,j,k])
                        model.ctCumulativeHours.add(expr = model.vIcumulatedHours[i,j,k]>=model.vbSubjectSchedule[i,j,k])
                    else:
                        model.ctCumulativeHours.add(expr = model.vIcumulatedHours[i,j,k] == 0)

        # :: Each subject must be given in consecutive blocks
        model.ctSubjectSwitches = pyo.ConstraintList()
        for k in model.sSubjects:
            for i in model.sDays:
                for j in model.sHours:
                    #model.ctSubjectSwitches.add(expr = model.vbSubjectSchedule[i,j,k] - model.vbSubjectSchedule[i,model.sHours.prevw(j), k] == model.vISubjectSwitches[i,j,k])
                    
                    model.ctSubjectSwitches.add(expr = model.vbSubjectSchedule[i,j,k] - model.vbSubjectSchedule[i,model.sHours.prevw(j), k] <= model.vbSubjectSwitches[i,j,k])
                    model.ctSubjectSwitches.add(expr = -model.vbSubjectSchedule[i,j,k] + model.vbSubjectSchedule[i,model.sHours.prevw(j), k] <= model.vbSubjectSwitches[i,j,k])
                    
                model.ctSubjectSwitches.add(expr = sum(model.vbSubjectSwitches[i,j,k] for j in model.sHours)==2*model.vbSubjectDaysFlags[i,k])
                
                # :: Unless a subject can be allocated to a whole day session, the first and last hour of the day cannot be assigned to the same subject
                if self.max_hours_per_day < len(model.sHours):
                    model.ctSubjectSwitches.add(expr = model.vbSubjectSchedule[i,model.sHours.first(), k] + model.vbSubjectSchedule[i,model.sHours.last(), k]  <= 1)
       
    
        #---------- assignment constraints
        # :: try to chunk subjects in as few days as possible, penalizing additional days
        model.ctCumulativeHours.add(model.vIsubjectTotalDays == sum(model.vbSubjectDaysFlags[i,k] for i in model.sDays for k in model.sSubjects)-sum(model.pMinDaysPerSubject[k] for k in model.sSubjects))
        
        penalty = -5
    
    
        
        
        # Objective function
        maximize = 1
        model.objSchedule= pyo.Objective(sense = -maximize, expr =  penalty*(model.vIsubjectTotalDays)+ sum(model.pPreferences[i,j,k]*model.vbSubjectSchedule[i,j,k] for i in model.sDays for j in model.sHours for k in model.sSubjects))

        
        self.model = model
        
    def update_preferences(self, preferences : list):
        #--------- preference constraints
        for k in preferences:
            self.model.pPreferences[k[0],k[1],k[2]]=k[3]

    def update_constraints(self, constraints : list):
        self.model.ctFixedSlots = pyo.ConstraintList()
        #--------- preference constraints
        for k in constraints:
            v = k[3]
            if v==1:
                self.model.ctFixedSlots.add(expr = self.model.vbSubjectSchedule[k[0],k[1],k[2]]==v)
            else:
                self.model.ctFixedSlots.add(expr = self.model.vbSubjectSchedule[k[0],k[1],k[2]]<=0)
        
    
    def solve_schedule(self):
        opt = pyo.SolverFactory('cbc')
        res = opt.solve(self.model)
        print(res)

    def print_schedule(self):

        hours = []
        subjects = []
        days = []
        bool_class = []
        for i in self.model.sDays:
            for j in self.model.sHours:
                for k in self.model.sSubjects:
                    hours.append(j)
                    days.append(i)
                    subjects.append(k)
                    bool_class.append(self.model.vbSubjectSchedule[i,j,k].value)

        df_schedule = pd.DataFrame({'day':days, 'hour':hours, 'subject':subjects, 'class':bool_class})
        df_schedule = df_schedule[df_schedule['class']>0].pivot(index = 'hour', columns = 'day', values = 'subject')
        
        return df_schedule.loc[[h for h in self.model.sHours] , [d for d in self.model.sDays]]
