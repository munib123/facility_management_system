import pandas as pd
import random
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

# Initialize Faker and seed for reproducibility
fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ==========================================
# 1. CONFIGURATION (How much data to generate)
# ==========================================
NUM_LOCATIONS = 50
NUM_STAFF = 20
NUM_TASKS = 1000
NUM_INSPECTIONS = 200
NUM_CONSUMABLES = 500
NUM_FINANCIALS = 100
NUM_TICKETS = 150

print("Generating dataset...")

# ==========================================
# 2. MASTER DATA (Locations & Staff)
# ==========================================

# --- Table: Facilities / Locations ---
location_ids = list(range(101, 101 + NUM_LOCATIONS))
locations_data = []

for loc_id in location_ids:
    locations_data.append({
        'Location_ID': loc_id,
        'Building_Wing': fake.random_element(elements=('North Wing', 'South Wing', 'Admin Block', 'Cafeteria')),
        'Floor': random.randint(1, 5),
        'Room_Area_Type': fake.random_element(elements=('Office', 'Conference Room', 'Washroom', 'Lobby', 'Pantry')),
        'Size_sqm': random.randint(20, 300),
        'Cleaning_Priority': fake.random_element(elements=('High', 'Medium', 'Low'))
    })

df_locations = pd.DataFrame(locations_data)

# --- Table: Staff / Workforce ---
staff_ids = list(range(1, 1 + NUM_STAFF))
staff_data = []

for s_id in staff_ids:
    staff_data.append({
        'Cleaner_ID': s_id,
        'Name': fake.name(),
        'Shift': fake.random_element(elements=('Morning', 'Afternoon', 'Night')),
        'Hours_worked': random.randint(4, 10),
        'Role_Grade': fake.random_element(elements=('Supervisor', 'Senior Cleaner', 'Junior Cleaner')),
        'Assigned_Location_ID': random.choice(location_ids) # Foreign Key
    })

df_staff = pd.DataFrame(staff_data)

# ==========================================
# 3. TRANSACTIONAL DATA (Tasks, Audits, Usage)
# ==========================================

# --- Table: Cleaning Schedule / Tasks ---
tasks_data = []
task_types = ['Vacuuming', 'Mop Floor', 'Trash Collection', 'Sanitization', 'Deep Clean']

for i in range(NUM_TASKS):
    tasks_data.append({
        'Task_ID': i + 1,
        'Location_ID': random.choice(location_ids),
        'Date': fake.date_between(start_date='-1y', end_date='today'),
        'Time': fake.time(),
        'Cleaner_ID': random.choice(staff_ids),
        'Task_Type': random.choice(task_types),
        'Status': np.random.choice(['Completed', 'Planned', 'Missed'], p=[0.8, 0.15, 0.05]),
        'Duration_Mins': random.randint(15, 120),
        'Notes': fake.sentence() if random.random() > 0.8 else None
    })

df_tasks = pd.DataFrame(tasks_data)

# --- Table: Cleaning Audit / Inspections ---
inspections_data = []

for i in range(NUM_INSPECTIONS):
    score = random.randint(1, 10)
    # Logic: Lower score = more issues found
    issues = fake.sentence() if score < 7 else "None"
    
    inspections_data.append({
        'Inspection_ID': i + 1,
        'Location_ID': random.choice(location_ids),
        'Date': fake.date_between(start_date='-1y', end_date='today'),
        'Hygiene_Score': score,
        'Auditor_ID': random.randint(500, 505),
        'Issues_found': issues,
        'Corrective_actions': "Retraining required" if score < 5 else "None",
        'Feedback': fake.text(max_nb_chars=50)
    })

df_inspections = pd.DataFrame(inspections_data)

# --- Table: Consumables & Resources ---
consumables_data = []
resources = {
    'Liquid Soap': 5.00, 
    'Paper Towels': 2.50, 
    'Sanitizer': 8.00, 
    'Trash Bags': 0.50, 
    'Floor Cleaner': 12.00
}

for i in range(NUM_CONSUMABLES):
    res_type = random.choice(list(resources.keys()))
    qty = random.randint(1, 20)
    unit_cost = resources[res_type]
    
    consumables_data.append({
        'Date': fake.date_between(start_date='-1y', end_date='today'),
        'Location_ID': random.choice(location_ids),
        'Resource_Type': res_type,
        'Quantity_used': qty,
        'Total_Cost': round(qty * unit_cost, 2)
    })

df_consumables = pd.DataFrame(consumables_data)

# ==========================================
# 4. FINANCIALS & TICKETS
# ==========================================

# --- Table: Cost / Financials ---
financials_data = []

for i in range(NUM_FINANCIALS):
    loc_id = random.choice(location_ids)
    # Get size of this location to calculate cost per sqm
    loc_size = df_locations.loc[df_locations['Location_ID'] == loc_id, 'Size_sqm'].values[0]
    
    labour = round(random.uniform(50, 500), 2)
    material = round(random.uniform(10, 200), 2)
    total = labour + material
    budget = total * random.uniform(0.9, 1.2) # Random budget variance
    
    financials_data.append({
        'Date': fake.date_between(start_date='-1y', end_date='today'),
        'Location_ID': loc_id,
        'Labour_cost': labour,
        'Material_cost': material,
        'Total_cost': total,
        'Cost_per_sqm': round(total / loc_size, 2),
        'Budget_vs_Actual': round(budget - total, 2)
    })

df_financials = pd.DataFrame(financials_data)

# --- Table: Requests / Work Orders ---
tickets_data = []

for i in range(NUM_TICKETS):
    report_date = fake.date_between(start_date='-1y', end_date='today')
    completion_time = random.randint(30, 480) # Minutes
    
    tickets_data.append({
        'Ticket_ID': f"TKT-{i+1000}",
        'Location_ID': random.choice(location_ids),
        'Date_reported': report_date,
        'Issue_type': random.choice(['Spill', 'Broken Fixture', 'Bin Overflow', 'Leakage']),
        'Response_time_mins': random.randint(5, 60),
        'Completion_time_mins': completion_time,
        'Staff_assigned': random.choice(staff_ids),
        'Status': np.random.choice(['Closed', 'In Progress', 'Open'], p=[0.7, 0.2, 0.1])
    })

df_tickets = pd.DataFrame(tickets_data)

# ==========================================
# 5. EXPORT
# ==========================================
# You can save these to CSV like this:
df_locations.to_csv('locations.csv', index=False)
df_staff.to_csv('staff.csv', index=False)
df_tasks.to_csv('tasks.csv', index=False)
df_inspections.to_csv('inspections.csv', index=False)
df_consumables.to_csv('consumables.csv', index=False)
df_financials.to_csv('financials.csv', index=False)
df_tickets.to_csv('tickets.csv', index=False)

print("Data generation complete! Here is a preview of the Tasks table:")
print(df_tasks.head())