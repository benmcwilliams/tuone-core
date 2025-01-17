```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Reichenow Möglin"
sort company, dt_announce desc
```
