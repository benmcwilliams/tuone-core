```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "North Sea N 12.1"
sort company, dt_announce desc
```
