```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Viana do Castelo"
sort company, dt_announce desc
```
