```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "23-Degrees-Renewables-Ltd" or company = "23 Degrees Renewables Ltd")
sort location, dt_announce desc
```
