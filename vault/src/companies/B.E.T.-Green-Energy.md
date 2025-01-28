```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "B.E.T.-Green-Energy" or company = "B.E.T. Green Energy")
sort location, dt_announce desc
```
