```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energy-Transition-Zone" or company = "Energy Transition Zone")
sort location, dt_announce desc
```
