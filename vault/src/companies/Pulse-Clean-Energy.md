```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Pulse-Clean-Energy" or company = "Pulse Clean Energy")
sort location, dt_announce desc
```
