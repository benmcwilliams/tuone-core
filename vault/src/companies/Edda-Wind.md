```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Edda-Wind" or company = "Edda Wind")
sort location, dt_announce desc
```
