```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energy-Optimisation-Solutions" or company = "Energy Optimisation Solutions")
sort location, dt_announce desc
```
