```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Port of Barcelona"
sort company, dt_announce desc
```
