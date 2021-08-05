from scheduler_model import course_scheduler
import numpy as np 

if __name__ == "__main__":
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

    print(SCHEDULE.print_schedule())