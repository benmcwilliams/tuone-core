```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Offshore Portugal"
sort company, dt_announce desc
```
