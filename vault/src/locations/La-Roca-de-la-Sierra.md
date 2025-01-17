```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "La Roca de la Sierra"
sort company, dt_announce desc
```
