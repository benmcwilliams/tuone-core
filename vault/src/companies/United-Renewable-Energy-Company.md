```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "United-Renewable-Energy-Company" or company = "United Renewable Energy Company")
sort location, dt_announce desc
```
