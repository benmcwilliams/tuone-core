```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "London-Electric-Vehicle-Company" or company = "London Electric Vehicle Company")
sort location, dt_announce desc
```
