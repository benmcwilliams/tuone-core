```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Offshore Le Croisic"
sort company, dt_announce desc
```
