```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Floating-Power-Plant" or company = "Floating Power Plant")
sort location, dt_announce desc
```
