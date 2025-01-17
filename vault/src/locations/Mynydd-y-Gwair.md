```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Mynydd y Gwair"
sort company, dt_announce desc
```
