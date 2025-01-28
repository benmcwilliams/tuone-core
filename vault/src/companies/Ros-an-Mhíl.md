```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ros-an-Mhíl" or company = "Ros an Mhíl")
sort location, dt_announce desc
```
