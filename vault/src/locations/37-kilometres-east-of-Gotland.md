```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "37 kilometres east of Gotland"
sort company, dt_announce desc
```
