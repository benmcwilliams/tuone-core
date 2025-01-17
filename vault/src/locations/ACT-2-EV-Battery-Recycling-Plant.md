```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "ACT 2 EV Battery Recycling Plant"
sort company, dt_announce desc
```
