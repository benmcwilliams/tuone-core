```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Las Manchas, El Paso"
sort company, dt_announce desc
```
