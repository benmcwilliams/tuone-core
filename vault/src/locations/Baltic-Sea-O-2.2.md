```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Baltic Sea O 2.2"
sort company, dt_announce desc
```
