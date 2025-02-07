```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Kohler-Power-Systems" or company = "Kohler Power Systems")
sort location, dt_announce desc
```
