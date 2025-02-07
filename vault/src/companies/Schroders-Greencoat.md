```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Schroders-Greencoat" or company = "Schroders Greencoat")
sort location, dt_announce desc
```
