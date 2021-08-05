from fastapi import FastAPI
from pydantic import BaseModel
import sys
sys.path.append('../')
from scheduler_model import course_scheduler
import numpy as np
from typing import List, Dict, Optional
import uvicorn

app = FastAPI(title="Schedule creator v1.0", description="Create your optimal schedule automatically")

class Preferences(BaseModel):
    day : str
    hour : str
    subject : str
    preference : int
    

class Schedule(BaseModel):
    days: List[str]
    hours : List[str]
    hours_per_subject : Dict[str, int]
    max_hours_per_day : int
    preferences: Optional[List[Preferences]] = None
    constraints: Optional[List[Preferences]] = None
        
@app.get("/test_example")
async def root():
    
    # Args 
    days = ['l','m','x','j', 'v']
    hours = [f"h_{i}" for i in np.arange(10,14,1)]
    subjects = [f"SB_{i}" for i in range(8)]
    hours_per_subject = dict(zip(subjects, [2 for i in range(8)]))
    for i in np.random.choice(subjects, 4):
        hours_per_subject[i]+=1

    max_hours_per_day = 2

    preferences = [
        ('l', f"h_{11}", 'SB_3', 4)
    ]

    constraints = [
        ('l', f"h_{12}", 'SB_1',  1)
    ]
    
    SCHEDULE = course_scheduler(days, hours, hours_per_subject, max_hours_per_day)
    SCHEDULE.create_model()
    SCHEDULE.update_preferences(preferences)
    SCHEDULE.update_constraints(constraints)
    SCHEDULE.solve_schedule()

    df_schedule = SCHEDULE.print_schedule()
    
    return {"schedule": df_schedule.to_json(), "status":"OK"}


@app.post("/create_schedule")
async def create_schedule(schedule : Schedule):    
    SCHEDULE = course_scheduler(schedule.days, 
                                schedule.hours, 
                                schedule.hours_per_subject, 
                                schedule.max_hours_per_day)
    SCHEDULE.create_model()
    
    if schedule.preferences is not None:
        preferences = []
        for p in schedule.preferences:
            x = (p.day, p.hour, p.subject, p.preference)
            preferences.append(x)
        
                
        SCHEDULE.update_preferences(preferences)
    
    if schedule.constraints is not None:
        
        constraints = []
        for p in schedule.constraints:
            x = ()
            x = (p.day, p.hour, p.subject, p.preference)
            constraints.append(x)
        SCHEDULE.update_constraints(constraints)
    
    SCHEDULE.solve_schedule()
    
    df_schedule = SCHEDULE.print_schedule()
    
    return {"schedule": df_schedule.to_json(), "status":"OK"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)