```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Clayfords-Energy-Storage-Limited" or company = "Clayfords Energy Storage Limited")
sort location, dt_announce desc
```
