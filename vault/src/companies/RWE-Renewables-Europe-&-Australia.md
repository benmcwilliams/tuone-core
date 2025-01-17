```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "RWE Renewables Europe & Australia"
sort location, dt_announce desc
```
