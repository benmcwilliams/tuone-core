```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Brandenburg University of Technology (BTU)"
sort location, dt_announce desc
```
