```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "3S-Swiss-Solar-Systems" or company = "3S Swiss Solar Systems")
sort location, dt_announce desc
```
