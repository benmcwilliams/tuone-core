```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Powerhouse-Energy-PLC" or company = "Powerhouse Energy PLC")
sort location, dt_announce desc
```
