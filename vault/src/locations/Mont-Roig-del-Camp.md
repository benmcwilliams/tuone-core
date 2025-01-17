```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Mont Roig del Camp"
sort company, dt_announce desc
```
