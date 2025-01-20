```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "San Pedro del Pinatar"
sort company, dt_announce desc
```
